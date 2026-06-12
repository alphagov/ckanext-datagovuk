"""Applies resource deletions from a check_links.py CSV report.

For every row with `to-delete == "true"`:
  * `live`: marks the resource `state` to 'deleted' (if currently 'active')
    and bumps the package `metadata_modified` to NOW().
  * `dry-run`: logs the intended change, no DB writes.

This does NOT fetch resources from the database or
check link liveness, it uses the report and actions it directly. 
Use it to apply a previously generated report without rerunning the
resource liveness check

Writes a report of check links rows deleted with a "deleted-on" 
timestamp.

Writes a `deleted_packages_to_reindex_{ts}.txt` for feeding into
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

sys.path.insert(0, str(Path(__file__).parent.parent))

from python_scripts.check_links import Repository, setup_logging

LOG_FILE = "check_links_delete.log"
REINDEX_FILE = "deleted_packages_to_reindex_{timestamp}.txt"


def _create_deleted_filename(filepath, timestamp):
    path = Path(filepath)
    return str(path.with_name(f"{path.stem}_deleted_{timestamp}{path.suffix}"))


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
    return parser.parse_args(argv)


def apply(
    *,
    logger: logging.Logger,
    repository: Repository,
    input_path: str,
    reindex_path: str,
    deleted_path: str,
    mode: str,
) -> None:
    to_reindex: set[str] = set()
    updated = 0
    outfile = None
    writer: csv.DictWriter | None = None

    with contextlib.ExitStack() as stack:
        infile = stack.enter_context(open(input_path, newline="", encoding="utf-8"))
        for row in csv.DictReader(infile):
            if row["to-delete"] != "true":
                continue
            resource_id = row["resource-id"]
            package_id = row["package-id"]

            if mode == "live":
                rowcount = repository.mark_resource_deleted(resource_id, package_id)
                if rowcount > 0:
                    to_reindex.add(package_id)
                    updated += 1
                    row["deleted-on"] = datetime.now(UTC).isoformat(timespec="minutes")
                    # open the report lazily so a run that deletes nothing
                    # doesn't create empty applied file
                    if writer is None:
                        outfile = stack.enter_context(
                            open(deleted_path, "w", newline="", encoding="utf-8")
                        )
                        writer = csv.DictWriter(outfile, fieldnames=list(row))
                        writer.writeheader()
                    writer.writerow(row)
                    outfile.flush()
                else:
                    logger.info(f"skipped {resource_id} (not in active state)")
            else:
                updated += 1
                logger.info(f"would delete {resource_id}")

    if writer is not None:
        logger.info(f"deletion report: {deleted_path}")

    with open(reindex_path, "w", encoding="utf-8") as f:
        for package_id in sorted(to_reindex):
            f.write(f"{package_id}\n")

    logger.info(f"deleted {updated} resources, {len(to_reindex)} packages to reindex")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    log_path = LOG_FILE
    reindex_path = os.path.join(
        args.output_dir, REINDEX_FILE.format(timestamp=timestamp)
    )
    deleted_path = _create_deleted_filename(args.input, timestamp)
    logger = setup_logging(log_path)
    logger.info(f"mode: {args.mode}")
    logger.info(f"input: {args.input}")
    logger.info(f"reindex path: {reindex_path}")
    logger.info(f"deleted report path: {deleted_path}")

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
            deleted_path=deleted_path,
            mode=args.mode,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
