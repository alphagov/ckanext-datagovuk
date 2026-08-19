#!/usr/bin/env python
#
# Set the FILENAME_BASE to the txt file containing the list of package_ids
#
# Execute script like this -
# python solr_reindex_package_ids.py
#

import argparse
import logging
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

logger = logging.getLogger(__name__)

FILENAME_BASE = (
    "<filename for list of package_ids to reindex without the txt extension>"
)


def setup_logging(log_to_file=False):
    _format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    logger.setLevel(logging.INFO)
    c_handler = logging.StreamHandler()
    c_handler.setFormatter(_format)
    logger.addHandler(c_handler)

    if log_to_file:
        f_handler = logging.FileHandler("%s.log" % FILENAME_BASE)
        f_handler.setFormatter(_format)
        logger.addHandler(f_handler)

    logger.info("====================================================================")


def run_reindex_package(package_id: str, ckan_ini: str) -> tuple[str, bool, str]:
    command = ["ckan", "-c", ckan_ini, "search-index", "rebuild", package_id]
    try:
        subprocess.check_call(command)
        return package_id, True, ""
    except Exception as exc:
        return package_id, False, str(exc)


def reindex_solr(filename=None, workers: int | None = None):
    if not filename:
        filename = f"{FILENAME_BASE}.txt"

    ckan_ini = os.environ.get("CKAN_INI")
    if ckan_ini is None:
        logger.error("CKAN_INI env variable not set")
        sys.exit(1)

    with open(filename, "r") as f:
        lines = f.readlines()

    datasets = [line.strip() for line in lines if line.strip()]
    if not datasets:
        logger.warning("No package IDs found in %s", filename)
        return

    workers = workers or os.cpu_count() or 1
    logger.info("Reindexing %d datasets using %d worker(s)", len(datasets), workers)

    failures = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        future_to_package = {
            executor.submit(run_reindex_package, package_id, ckan_ini): package_id
            for package_id in datasets
        }

        for index, future in enumerate(as_completed(future_to_package), start=1):
            package_id = future_to_package[future]
            try:
                _, success, error = future.result()
                if success:
                    logger.info("CKAN reindex %d/%d - %s succeeded", index, len(datasets), package_id)
                else:
                    logger.error("CKAN reindex %d/%d - %s failed: %s", index, len(datasets), package_id, error)
                    failures.append(package_id)
            except Exception:
                logger.exception("Unexpected exception while processing %s", package_id)
                failures.append(package_id)

    if failures:
        logger.error("Reindexing failed for %d package(s): %s", len(failures), ", ".join(failures))
        sys.exit(1)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reindex CKAN datasets in Solr based on a list of package IDs.",
    )
    parser.add_argument(
        "--input-file",
        "-i",
        default=f"{FILENAME_BASE}.txt",
        help="Path to a text file containing package IDs, one per line.",
    )
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=None,
        help="Number of worker processes to use for reindexing. Defaults to CPU count.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    setup_logging()

    logger.info("Executing REINDEX")
    logger.info("====================================================================")
    logger.info("Reindex datasets")
    reindex_solr(filename=args.input_file, workers=args.workers)
    logger.info("Processing complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
