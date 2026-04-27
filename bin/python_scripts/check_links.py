"""Checks active resource URLs of active dataset packages.

For each URL:
  * Classifies the response (OK / 404 / 410 / other 4xx / 5xx / timeout / etc.).
  * in `dry-run` mode no db writes - just report/log output
  * in `live' mode: if 404 or 410, updates resource `state` to 'deleted'
  * and updates package `metadata_modified` to NOW().

Writes `check_links_report_{ts}.csv` (one row per URL) and
`packages_to_reindex_{ts}.txt` (unique packages with at least one
to-delete resource) for feeding into `solr_reindex_package_ids.py`.
"""

import argparse
import csv
import logging
import os
import sys
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from urllib.parse import urlsplit

import psycopg2
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LOG_FILE = "check_links.log"
REPORT_FILE = "check_links_report_{timestamp}.csv"
REINDEX_FILE = "packages_to_reindex_{timestamp}.txt"
USER_AGENT = "data.gov.uk-link-checker/1.0 (+https://www.data.gov.uk)"
HTTP_TIMEOUT = (5, 5)  # (connect, read) seconds
WORKERS = 50
HEAD_FALLBACK_STATUSES = {400, 403, 405, 501}

REPORT_HEADERS = [
    "package-id",
    "package-name",
    "resource-id",
    "resource-url",
    "org-name",
    "org-id",
    "http-status",
    "category",
    "error-detail",
    "to-delete",
    "checked-at",
]


def setup_logging(log_path: str) -> logging.Logger:
    logger = logging.getLogger(__name__)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    return logger


class Category(StrEnum):
    OK = "OK"
    NOT_FOUND = "404"
    GONE = "410"
    TOO_MANY_REQUESTS = "429"
    OTHER_CLIENT_ERROR = "OTHER_CLIENT_ERROR"
    SERVER_ERROR = "SERVER_ERROR"
    TIMEOUT = "TIMEOUT"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    OTHER_ERROR = "OTHER_ERROR"


@dataclass(frozen=True)
class ResourceRow:
    """Represents a package (dataset) resource and its URL from db"""

    package_id: str
    package_name: str
    resource_id: str
    url: str
    org_name: str | None = None
    org_id: str | None = None


@dataclass
class CheckResult:
    """A report row for one checked package resource URL"""

    row: ResourceRow
    http_status: int | None = None
    category: Category | None = None
    error_detail: str | None = None
    checked_at: datetime | None = None

    @property
    def to_delete(self) -> bool:
        return self.category in {Category.NOT_FOUND, Category.GONE}


def classify_response(
    status_code: int | None, exc: BaseException | None
) -> tuple[Category, str | None]:
    match (status_code, exc):
        case (_, requests.Timeout()):
            return Category.TIMEOUT, str(exc)
        case (_, requests.ConnectionError()):
            return Category.CONNECTION_ERROR, str(exc)
        case (_, BaseException()):
            return Category.OTHER_ERROR, str(exc)
        case (None, None):
            return Category.OTHER_ERROR, "no status and no exception"
        case (404, None):
            return Category.NOT_FOUND, None
        case (410, None):
            return Category.GONE, None
        case (429, None):
            return Category.TOO_MANY_REQUESTS, None
        case (int(s), None) if 200 <= s < 400:
            return Category.OK, None
        case (int(s), None) if 400 <= s < 500:
            return Category.OTHER_CLIENT_ERROR, None
        case (int(s), None) if 500 <= s < 600:
            return Category.SERVER_ERROR, None
        case _:
            return Category.OTHER_ERROR, f"unexpected status {status_code}"


def session_factory(
    workers: int = WORKERS,
) -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "*/*"})
    retry = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET"],
        backoff_factor=1,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=workers,
        pool_maxsize=workers * 2,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch_status(
    session: requests.Session,
    url: str,
    timeout: tuple[float, float] = HTTP_TIMEOUT,
) -> int:

    with session.head(url, timeout=timeout, allow_redirects=True) as resp:
        status = resp.status_code

    if status in HEAD_FALLBACK_STATUSES:
        with session.get(
            url, timeout=timeout, allow_redirects=True, stream=True
        ) as resp:
            return resp.status_code

    return status


def check_task(row: ResourceRow, session: requests.Session) -> CheckResult:
    result = CheckResult(row=row)
    try:
        status = fetch_status(session, row.url)
        result.http_status = status
        result.category, result.error_detail = classify_response(status, None)
    except Exception as exc:
        result.category, result.error_detail = classify_response(None, exc)
    result.checked_at = datetime.now(UTC)
    return result


def host_key(url: str) -> str:
    try:
        return urlsplit(url).netloc.lower() or url
    except Exception:
        return url


def interleave_rows_by_host(rows: list[ResourceRow]) -> list[ResourceRow]:
    buckets: dict[str, deque[ResourceRow]] = defaultdict(deque)
    for row in rows:
        host = host_key(row.url)
        buckets[host].append(row)

    interleaved_rows: list[ResourceRow] = []

    while buckets:
        for host in list(buckets):
            interleaved_rows.append(buckets[host].popleft())
            if not buckets[host]:
                del buckets[host]  # no rows left for this host
    return interleaved_rows


class Repository:
    """Handles all db access. One connection opened in __enter__."""

    SELECT_SQL = """
        SELECT p.id, p.name, r.id, r.url, g.name as org_name, g.id as org_id
        FROM package p
        JOIN resource r ON r.package_id = p.id
        LEFT JOIN "group" g on p.owner_org = g.id
        WHERE p.state = 'active'
          AND p.type = 'dataset'
          AND r.state = 'active'
          AND r.url IS NOT NULL
          AND TRIM(r.url) <> ''
        ORDER BY p.id, r.id
    """
    UPDATE_RESOURCE_SQL = "UPDATE resource SET state = 'deleted' WHERE id = %(resource_id)s AND state = 'active'"
    UPDATE_RESOURCE_ACTIVE_SQL = "UPDATE resource SET state = 'active' WHERE id = %(resource_id)s AND state = 'deleted'"
    UPDATE_PACKAGE_MTIME_SQL = (
        "UPDATE package SET metadata_modified = NOW() WHERE id = %(package_id)s"
    )

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._conn: psycopg2.extensions.connection | None = None

    def __enter__(self):
        self._conn = psycopg2.connect(self._dsn)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def fetch_resources(self) -> list[ResourceRow]:
        assert self._conn is not None, "Repository not entered"
        with self._conn, self._conn.cursor() as cur:
            cur.execute(self.SELECT_SQL)
            return [
                ResourceRow(
                    package_id=package_id,
                    package_name=package_name,
                    resource_id=resource_id,
                    url=url,
                )
                for package_id, package_name, resource_id, url, org_name, org_id in cur
            ]

    def mark_resource_deleted(self, resource_id: str, package_id: str) -> int:
        assert self._conn is not None, "Repository not entered"
        with self._conn, self._conn.cursor() as cur:
            cur.execute(self.UPDATE_RESOURCE_SQL, {"resource_id": resource_id})
            rowcount = cur.rowcount
            if rowcount > 0:
                cur.execute(self.UPDATE_PACKAGE_MTIME_SQL, {"package_id": package_id})
        return rowcount

    def mark_resource_active(self, resource_id: str, package_id: str) -> int:
        assert self._conn is not None, "Repository not entered"
        with self._conn, self._conn.cursor() as cur:
            cur.execute(self.UPDATE_RESOURCE_ACTIVE_SQL, {"resource_id": resource_id})
            rowcount = cur.rowcount
            if rowcount > 0:
                cur.execute(self.UPDATE_PACKAGE_MTIME_SQL, {"package_id": package_id})
        return rowcount


class Reporter:
    """Handles the CSV report writing. Flushes after every row."""

    def __init__(self, path: str) -> None:
        self._path = path

    def __enter__(self) -> "Reporter":
        new_file = not os.path.exists(self._path) or os.path.getsize(self._path) == 0
        self._fh = open(self._path, "a", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(
            self._fh, fieldnames=REPORT_HEADERS, quoting=csv.QUOTE_ALL
        )
        if new_file:
            self._writer.writeheader()
            self._fh.flush()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._fh.close()

    def write(self, result: CheckResult) -> None:
        self._writer.writerow(
            {
                "package-id": result.row.package_id,
                "package-name": result.row.package_name,
                "resource-id": result.row.resource_id,
                "resource-url": result.row.url,
                "org-name": result.row.org_name,
                "org-id": result.row.org_id,
                "http-status": "" if result.http_status is None else result.http_status,
                "category": result.category.name,
                "error-detail": result.error_detail or "",
                "to-delete": "true" if result.to_delete else "false",
                "checked-at": result.checked_at.isoformat(timespec="seconds"),
            }
        )
        self._fh.flush()


def run(
    *,
    logger: logging.Logger,
    repository: Repository,
    report_path: str,
    reindex_path: str,
    mode: str,
) -> None:

    # **NOTE**
    # This loads full result set in memory. pool.submit also queues all futures upfront.
    # This will result in a fair amount of memory being allocated. Some tests were done
    # locally with dummy data which isn't a substitute for testing with real data
    # Once tested with real data, if there are issues, look into processing data in
    # chunks

    rows_from_db = repository.fetch_resources()
    rows = interleave_rows_by_host(rows_from_db)
    logger.info(f"loaded {len(rows)} resources")

    to_reindex: set[str] = set()

    # Shared session not formally thread safe, but the underlying pool is,
    # and we don't mutate session state or rely on cookies
    session = session_factory()

    with (
        Reporter(report_path) as reporter,
        ThreadPoolExecutor(max_workers=WORKERS) as pool,
    ):
        futures = [pool.submit(check_task, r, session) for r in rows]
        for future in as_completed(futures):
            try:
                result = future.result()
                reporter.write(result)
                logger.info(
                    f"Checked resource: {result.row.resource_id} - url: {result.row.url}- outcome: {result.category}"
                )
                if result.to_delete:
                    to_reindex.add(result.row.package_id)
                    if mode == "live":
                        repository.mark_resource_deleted(
                            result.row.resource_id, result.row.package_id
                        )
            except Exception as e:
                logger.exception("URL check task failed")

    with open(reindex_path, "w", encoding="utf-8") as f:
        for package_id in sorted(to_reindex):
            f.write(f"{package_id}\n")

    logger.info(f"completed {len(rows)} checks, {len(to_reindex)} packages to reindex")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tuning knobs (workers, timeouts) are module-level constants "
        "at the top of this file — edit there to change. Filenames are timestamped "
        "templates (also module-level constants).",
    )
    parser.add_argument(
        "--mode",
        choices=["dry-run", "live"],
        default="dry-run",
        help="'dry-run' (default) reports only; 'live' marks 404/410 resources deleted",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="directory for CSV report and reindex list (default: current directory). "
        "Log file is always written to the current directory.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    log_path = LOG_FILE
    report_path = os.path.join(args.output_dir, REPORT_FILE.format(timestamp=timestamp))
    reindex_path = os.path.join(
        args.output_dir, REINDEX_FILE.format(timestamp=timestamp)
    )
    logger = setup_logging(log_path)
    logger.info(f"mode: {args.mode}")
    logger.info(f"report path: {report_path}")
    logger.info(f"reindex path: {reindex_path}")
    logger.info(f"workers: {WORKERS}, http_timeout: {HTTP_TIMEOUT}")

    dsn = os.environ.get("POSTGRES_URL")
    if not dsn:
        logger.error("POSTGRES_URL env var is not set")
        return 1

    with Repository(dsn) as repository:
        run(
            logger=logger,
            repository=repository,
            report_path=report_path,
            reindex_path=reindex_path,
            mode=args.mode,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
