import argparse
import csv
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

import psycopg2
import requests
from requests.adapters import HTTPAdapter

LOG_FILE = "check_links.log"
REPORT_FILE = "check_links_report.csv"
USER_AGENT = "data.gov.uk-link-checker/1.0 (+https://www.data.gov.uk)"
HTTP_TIMEOUT = (5, 10)  # (connect, read) seconds
DEFAULT_WORKERS = 10
HEAD_FALLBACK_STATUSES = {400, 403, 405, 501}

REPORT_HEADERS = [
    "package-id",
    "package-name",
    "resource-id",
    "resource-url",
    "http-status",
    "category",
    "error-detail",
    "to-delete",
    "checked-at",
]

# TODOs:
#  - Add org to csv output.
#  - Create log of datasets to reindex using solr update scripts
#  - Add more logging to this script covering steps
#  - create some good test data?


def setup_logging(log_path: str = LOG_FILE) -> logging.Logger:
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["dry-run", "live"],
        default="dry-run",
        help="default: 'dry-run' doesn't update db, creates report",
    )
    parser.add_argument("--log-path", default=LOG_FILE)
    parser.add_argument("--report-path", default=REPORT_FILE)
    return parser.parse_args(argv)


class Category(StrEnum):
    OK = "OK"
    BROKEN_404 = "BROKEN_404"
    GONE_410 = "GONE_410"
    CLIENT_ERROR = "CLIENT_ERROR"
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


@dataclass(frozen=True)
class UrlCheckResult:
    http_status: int | None
    category: Category
    error_detail: str | None = None


@dataclass(frozen=True)
class ResourceCheckResult:
    """A report row for one checked package resource URL"""

    row: ResourceRow
    http_status: int | None
    category: Category
    error_detail: str | None
    checked_at: datetime

    @property
    def to_delete(self) -> bool:
        return self.category in {Category.BROKEN_404, Category.GONE_410}

    @classmethod
    def from_url_check(
        cls,
        row: ResourceRow,
        url_check: UrlCheckResult,
        checked_at: datetime,
    ) -> "ResourceCheckResult":
        return cls(
            row=row,
            http_status=url_check.http_status,
            category=url_check.category,
            error_detail=url_check.error_detail,
            checked_at=checked_at,
        )


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
            return Category.BROKEN_404, None
        case (410, None):
            return Category.GONE_410, None
        case (int(s), None) if 200 <= s < 400:
            return Category.OK, None
        case (int(s), None) if 400 <= s < 500:
            return Category.CLIENT_ERROR, None
        case (int(s), None) if 500 <= s < 600:
            return Category.SERVER_ERROR, None
        case _:
            return Category.OTHER_ERROR, f"unexpected status {status_code}"


def session_factory(workers: int) -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "*/*"})
    adapter = HTTPAdapter(pool_connections=workers, pool_maxsize=workers * 2)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch_status(session: requests.Session, url: str) -> int:
    resp = session.head(url, timeout=HTTP_TIMEOUT, allow_redirects=True)
    status = resp.status_code

    if status in HEAD_FALLBACK_STATUSES:
        with session.get(url, timeout=HTTP_TIMEOUT, allow_redirects=True, stream=True) as resp:
            return resp.status_code

    return status


def check_url(
    session: requests.Session,
    url: str,
) -> UrlCheckResult:
    try:
        status = fetch_status(session, url)
        category, detail = classify_response(status, None)
    except Exception as exc:
        status = None
        category, detail = classify_response(None, exc)

    return UrlCheckResult(
        http_status=status,
        category=category,
        error_detail=detail,
    )


def check_task(
    row: ResourceRow,
    session: requests.Session,
) -> ResourceCheckResult:
    return ResourceCheckResult.from_url_check(
        row=row,
        url_check=check_url(session, row.url),
        checked_at=datetime.now(timezone.utc),
    )


class Repository:
    """Handles all db access. One connection opened in __enter__."""

    SELECT_SQL = """
        SELECT p.id, p.name, r.id, r.url
        FROM package p
        JOIN resource r ON r.package_id = p.id
        WHERE p.state = 'active'
          AND p.type = 'dataset'
          AND r.state = 'active'
          AND r.url IS NOT NULL
          AND TRIM(r.url) <> ''
        ORDER BY p.id, r.id
    """
    UPDATE_RESOURCE_SQL = (
        "UPDATE resource SET state = 'deleted' WHERE id = %(resource_id)s AND state = 'active'"
    )
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
                for package_id, package_name, resource_id, url in cur
            ]

    def mark_resource_deleted(self, resource_id: str, package_id: str) -> int:
        assert self._conn is not None, "Repository not entered"
        with self._conn, self._conn.cursor() as cur:
            cur.execute(self.UPDATE_RESOURCE_SQL, {"resource_id": resource_id})
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
        self._fh = open(self._path, "a", newline="", encoding="utf-8")  # noqa: SIM115 — lifecycle managed by __exit__
        self._writer = csv.DictWriter(self._fh, fieldnames=REPORT_HEADERS, quoting=csv.QUOTE_ALL)
        if new_file:
            self._writer.writeheader()
            self._fh.flush()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._fh.close()

    def write(self, result: ResourceCheckResult) -> None:
        self._writer.writerow(
            {
                "package-id": result.row.package_id,
                "package-name": result.row.package_name,
                "resource-id": result.row.resource_id,
                "resource-url": result.row.url,
                "http-status": "" if result.http_status is None else result.http_status,
                "category": result.category.value,
                "error-detail": result.error_detail or "",
                "to-delete": "true" if result.to_delete else "false",
                "checked-at": result.checked_at.isoformat(timespec="seconds"),
            }
        )
        self._fh.flush()


def run(
    logger: logging.Logger,
    repository: Repository,
    report_path: str,
    mode: str,
    workers: int = DEFAULT_WORKERS,
) -> None:
    rows = repository.fetch_resources()
    logger.info(f"loaded {len(rows)} resources")

    session = session_factory(workers)
    with (
        Reporter(report_path) as reporter,
        ThreadPoolExecutor(max_workers=workers) as pool,
    ):
        for result in pool.map(lambda r: check_task(r, session), rows):
            reporter.write(result)
            if mode == "live" and result.to_delete:
                repository.mark_resource_deleted(result.row.resource_id, result.row.package_id)
    logger.info(f"completed {len(rows)} checks")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logger = setup_logging(args.log_path)
    logger.info(f"mode: {args.mode}")

    dsn = os.environ.get("POSTGRES_URL")
    if not dsn:
        logger.error("POSTGRES_URL env var is not set")
        return 1

    with Repository(dsn) as repository:
        run(
            logger=logger,
            repository=repository,
            report_path=args.report_path,
            mode=args.mode,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
