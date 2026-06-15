"""Sorts the check_links report CSV file by organization name and HTTP status."""

import argparse
import csv
import logging
import os
import sys

from lib.s3 import CkanOutputBucket
from check_links import REPORT_HEADERS


def setup_logging() -> logging.Logger:
    logger = logging.getLogger(__name__)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)
    return logger


def upload_to_s3(logger, report_path):
    bucket = CkanOutputBucket()
    bucket.upload_to_s3(report_path, "check_links")
    logger.info(f"uploaded {report_path} to S3 bucket {bucket.bucket.name}")
    logger.info("=== check_links/ ls")
    for filename in bucket.get_s3_ls(path="check_links/"):
        logger.info(filename)


def sort_report(report_path: str) -> None:
    """Sorts the report CSV file by org-name and http-status."""
    with open(report_path, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=REPORT_HEADERS)
        rows = list(reader)

    rows.pop(0)  # Remove header row so that it doesn't get sorted with the data rows
    rows.sort(key=lambda row: (row["org-name"], row["http-status"]))

    with open(report_path.replace(".csv", "_sorted.csv"), "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=REPORT_HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Set the input dir",
    )
    parser.add_argument(
        "--input-dir",
        default=".",
        help="directory for CSV report and reindex list (default: current directory). ",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logger = setup_logging()

    # there will only be one report file in the input dir as this will be run on a cronjob on a pod after check_links.py has run
    report_files = [f for f in os.listdir(args.input_dir) if f.startswith("check_links_report_") and f.endswith(".csv")]
    report_path = os.path.join(args.input_dir, report_files[0]) if report_files else None

    if report_path is None:
        logger.error("No report file found in input directory.")
        return 1

    sort_report(report_path)
    logger.info(f"Sorted report file saved to {report_path.replace('.csv', '_sorted.csv')}")

    if os.environ.get('CKAN_OUTPUT_BUCKET_NAME'):
        upload_to_s3(logger, report_path.replace(".csv", "_sorted.csv"))
        logger.info(f"Uploaded sorted report to S3 bucket {os.environ.get('CKAN_OUTPUT_BUCKET_NAME')}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
