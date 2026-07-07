"""Process a check_links.py CSV report.

This script marks resources as deleted ('inactive') or
active in the database depending on the `--set-state` flag which
accepts the values `deleted` or `actove`.

The default `--mode`, dry-run, will not make any database
updates. It only update resources if run in live mode.

This does NOT fetch resources from the database or
check link liveness, it uses the report and actions it directly.

Use it to apply a previously generated report without rerunning the
resource liveness check

Writes a `packages_to_reindex_apply_{ts}.txt` for feeding into
`solr_reindex_package_ids.py`.
"""

import argparse
import contextlib
import csv
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from lib.s3 import CkanOutputBucket

sys.path.insert(0, str(Path(__file__).parent.parent))

from python_scripts.check_links import Repository, setup_logging

LOG_FILE = "check_links_updated_to_{state}.log"
REINDEX_FILE = "{state}_packages_to_reindex_{timestamp}.txt"


def _create_output_filename(filepath, state, timestamp):
    path = Path(filepath)
    return str(path.with_name(f"{path.stem}_{state}_{timestamp}{path.suffix}"))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deletes resources from a check_links CSV report "
        "without fetching from the database or checking link liveness. "
        "Filenames are timestamped templates (module-level constants).",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="check_links CSV report of resources to delete (required)",
    )
    parser.add_argument(
        "--set-state",
        choices=["active", "deleted"],
        required=True,
        help="'action' - updates resources to state == active or deleted",
    )
    parser.add_argument(
        "--mode",
        choices=["dry-run", "live"],
        default="dry-run",
        help="'dry-run' (default) reports only; 'live' marks to-delete resources deleted",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="directory for the reindex list (default: current directory). "
        "Log file is always written to the current directory.",
    )
    parser.add_argument(
        "--reindex-timestamp",
        default=datetime.now(UTC).strftime("%Y%m%dT%H%M%S"),
        help="timestamp for reindex file (default: current UTC time)",
    )    
    return parser.parse_args(argv)


def apply(
    *,
    logger: logging.Logger,
    repository: Repository,
    input_path: str,
    reindex_path: str,
    output_report_path: str,
    mode: str,
    set_state: str,
) -> None:
    to_reindex: set[str] = set()
    updated = 0
    outfile = None
    writer: csv.DictWriter | None = None

    with contextlib.ExitStack() as stack:
        infile = stack.enter_context(open(input_path, newline="", encoding="utf-8"))
        for row in csv.DictReader(infile):
            if row.get("to-delete", "").lower().strip() != "true":
                continue
            resource_id = row["resource-id"]
            package_id = row["package-id"]
            to_reindex.add(package_id)

            if mode == "live":
                rowcount = repository.update_resource(
                    resource_id, package_id, set_state
                )
                if rowcount > 0:
                    row_copy = row.copy()
                    row_copy["update-applied"] = set_state
                    row_copy["update-applied-on"] = datetime.now(UTC).isoformat(
                        timespec="minutes"
                    )
                    updated += 1
                    # open the report lazily so a run that deletes nothing
                    # doesn't create empty applied file
                    if writer is None:
                        outfile = stack.enter_context(
                            open(output_report_path, "w", newline="", encoding="utf-8")
                        )
                        writer = csv.DictWriter(outfile, fieldnames=list(row_copy))
                        writer.writeheader()
                    writer.writerow(row_copy)
                    outfile.flush()
                else:
                    logger.info(
                        f"skipped {resource_id} (not in correct state to set state to {set_state})"
                    )
            else:
                updated += 1
                logger.info(f"would set state == {set_state} on resource {resource_id}")

    if writer is not None:
        logger.info(f"report of resources set to {set_state}: {output_report_path}")

    with open(reindex_path, "w", encoding="utf-8") as f:
        for package_id in sorted(to_reindex):
            f.write(f"{package_id}\n")

    logger.info(
        f"{set_state} {updated} resources, {len(to_reindex)} packages to reindex"
    )


def upload_to_s3(logger, output_report_path):
    bucket = CkanOutputBucket()
    bucket.upload_to_s3(output_report_path, "check_links")
    logger.info(f"uploaded {output_report_path} to S3 bucket {bucket.bucket.name}")
    logger.info("=== check_links/ ls")
    for filename in bucket.get_s3_ls(path="check_links/"):
        logger.info(filename)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    reindex_timestamp = args.timestamp
    log_path = LOG_FILE.format(state=args.set_state)
    reindex_path = os.path.join(
        args.output_dir, REINDEX_FILE.format(state=args.set_state, timestamp=reindex_timestamp)
    )

    logger = setup_logging(log_path)
    logger.info(f"mode: {args.mode}")
    logger.info(f"input: {args.input}")
    logger.info(f"set state: {args.set_state}")
    logger.info(f"reindex path: {reindex_path}")

    output_report_path = _create_output_filename(args.input, args.set_state, timestamp)
    logger.info(f"{args.set_state} report path: {output_report_path}")

    dsn = os.environ.get("POSTGRES_URL")
    if not dsn:
        logger.error("POSTGRES_URL env var is not set")
        return 1

    with Repository(dsn) as repository:
        apply(
            logger=logger,
            repository=repository,
            input_path=args.input,
            reindex_path=reindex_path,
            output_report_path=output_report_path,
            mode=args.mode,
            set_state=args.set_state,
        )

    upload_to_s3(logger, output_report_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
