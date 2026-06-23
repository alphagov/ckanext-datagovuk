"""Run the harvest jobs for the organisations in the report file."""

import argparse
import csv
import logging
import os
import sys
import psycopg2
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

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


def get_harvest_source_for_org(connection: psycopg2.extensions.connection, org: str):
    cursor = connection.cursor()
    sql = """
    SELECT harvest_source.id FROM harvest_source, "group"
    WHERE "group".id = harvest_source.publisher_id 
    AND harvest_source.active = true AND "group".name = %s
    GROUP BY harvest_source.id;
    """
    cursor.execute(sql, (org,))
    return cursor


def run_harvester_subprocess(harvest_source_id: str) -> tuple[str, bool, str]:
    """Helper executed in worker process to run a single harvest source."""
    cmd = ["ckan", "harvester", "run-test", harvest_source_id]
    try:
        subprocess.check_call(cmd)
        return harvest_source_id, True, ""
    except Exception as exc:
        return harvest_source_id, False, str(exc)


def run_harvest_jobs(logger: logging.Logger, report_path: str) -> None:
    """Identifies unique organisations in the report to run harvest jobs for."""
    POSTGRES_URL = os.environ.get('POSTGRES_URL')
    if not POSTGRES_URL:
        logger.error("POSTGRES_URL env var is not set")
        return 1

    with open(report_path, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=REPORT_HEADERS)        
        rows = list(reader)

    rows.pop(0)

    orgs = set()
    orgs = {row["org-name"] for row in rows if row["org-name"]}

    connection = psycopg2.connect(POSTGRES_URL)

    for org in orgs:
        logger.info(f"Running harvest job(s) for organisation: {org}")
        cursor = get_harvest_source_for_org(connection, org)
        harvest_sources = [row[0] for row in cursor]

        if not harvest_sources:
            logger.info(f"No active harvest sources found for organisation: {org}")
            continue

        workers = os.cpu_count() or 1
        failures = []
        with ProcessPoolExecutor(max_workers=workers) as executor:
            future_to_source = {executor.submit(run_harvester_subprocess, hs): hs for hs in harvest_sources}

            for future in as_completed(future_to_source):
                hs = future_to_source[future]
                try:
                    source_id, success, error = future.result()
                    if success:
                        logger.info(f"Harvest job completed for harvest source: {source_id}")
                    else:
                        logger.error(f"Harvest job failed for harvest source: {source_id}. Error: {error}")
                        failures.append(source_id)
                except Exception:
                    logger.exception("Unexpected exception while running harvest source: %s", hs)
                    failures.append(hs)

        if failures:
            logger.error("%d harvest source(s) failed for organisation %s: %s", len(failures), org, ", ".join(failures))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Set the report path",
    )
    parser.add_argument(
        "--report-path",
        required=True,
        help="path to CSV report file",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logger = setup_logging()

    report_path = args.report_path
    if not os.path.exists(report_path):
        logger.error("Report file not found: %s", report_path)
        return 1

    error = run_harvest_jobs(logger, report_path)
    if not error:
        logger.info("Harvest jobs completed successfully for report file: %s", report_path)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
