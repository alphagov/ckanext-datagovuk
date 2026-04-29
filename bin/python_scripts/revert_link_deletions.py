"""Reverses a prior `check_links.py --mode live` run using its CSV report.

For every row with `to-delete == "true"`:
  * `live`: flips the resource `state` back to 'active' (if currently
    'deleted') and bumps the package `metadata_modified` to NOW().
  * `dry-run`: logs the intended change, no DB writes.

Writes a `packages_to_reindex_revert_{ts}.txt` for feeding into
`solr_reindex_package_ids.py`.

Note: `metadata_modified` is bumped to NOW(). We don't have the pre-run
value to restore. Keeps the timestamp honest for any downstream consumer
that looks at it (scheduled reindexing? other?).
"""

import argparse
import csv
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python_scripts.check_links import Repository, setup_logging

LOG_FILE = "check_links_revert.log"
REINDEX_FILE = "packages_to_reindex_revert_{timestamp}.txt"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reverses a prior check_links --mode live run from its CSV report. "
        "Filenames are timestamped templates (module-level constants).",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="check_links CSV report to reverse (required)",
    )
    parser.add_argument(
        "--mode",
        choices=["dry-run", "live"],
        default="dry-run",
        help="'dry-run' (default) reports only; 'live' restores deleted resources",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="directory for the reindex list (default: current directory). "
        "Log file is always written to the current directory.",
    )
    return parser.parse_args(argv)


def revert(
    *,
    logger: logging.Logger,
    repository: Repository,
    input_path: str,
    reindex_path: str,
    mode: str,
) -> None:
    to_reindex: set[str] = set()
    updated = 0

    with open(input_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["to-delete"] != "true":
                continue
            resource_id = row["resource-id"]
            package_id = row["package-id"]

            if mode == "live":
                rowcount = repository.mark_resource_active(resource_id, package_id)
                if rowcount > 0:
                    to_reindex.add(package_id)
                    updated += 1
                else:
                    logger.info(f"skipped {resource_id} (not in deleted state)")
            else:
                to_reindex.add(package_id)
                updated += 1
                logger.info(f"would revert {resource_id}")

    with open(reindex_path, "w", encoding="utf-8") as f:
        for package_id in sorted(to_reindex):
            f.write(f"{package_id}\n")

    logger.info(f"reverted {updated} resources, {len(to_reindex)} packages to reindex")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    log_path = LOG_FILE
    reindex_path = os.path.join(
        args.output_dir, REINDEX_FILE.format(timestamp=timestamp)
    )
    logger = setup_logging(log_path)
    logger.info(f"mode: {args.mode}")
    logger.info(f"input: {args.input}")
    logger.info(f"reindex path: {reindex_path}")

    dsn = os.environ.get("POSTGRES_URL")
    if not dsn:
        logger.error("POSTGRES_URL env var is not set")
        return 1

    with Repository(dsn) as repository:
        revert(
            logger=logger,
            repository=repository,
            input_path=args.input,
            reindex_path=reindex_path,
            mode=args.mode,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
