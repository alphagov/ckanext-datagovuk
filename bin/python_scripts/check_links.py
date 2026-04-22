import argparse
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

import requests
from requests.adapters import HTTPAdapter

LOG_FILE = "check_links.log"
USER_AGENT = "data.gov.uk-link-checker/1.0 (+https://www.data.gov.uk)"
HTTP_TIMEOUT = (5, 10)  # (connect, read) seconds
DEFAULT_WORKERS = 10
BATCH_SIZE = 500
HEAD_FALLBACK_STATUSES = {400, 403, 405, 501}


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
    return parser.parse_args(argv)


class CheckOutcome(StrEnum):
    OK = "OK"
    BROKEN_404 = "BROKEN_404"
    CLIENT_ERROR = "CLIENT_ERROR"
    SERVER_ERROR = "SERVER_ERROR"
    TIMEOUT = "TIMEOUT"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    OTHER_ERROR = "OTHER_ERROR"


@dataclass(frozen=True)
class ResourceRow:
    """Represents a package (dataset) resource and its url from db"""

    package_id: str
    package_name: str
    resource_id: str
    url: str


@dataclass(frozen=True)
class UrlCheckResult:
    http_status: int | None
    outcome: CheckOutcome
    error_detail: str | None = None


@dataclass(frozen=True)
class ResourceCheckResult:
    """A report row for one checked package resource URL"""

    row: ResourceRow
    http_status: int | None
    outcome: CheckOutcome
    error_detail: str | None
    checked_at: datetime

    @property
    def to_delete(self) -> bool:
        return self.outcome is CheckOutcome.BROKEN_404

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
            outcome=url_check.outcome,
            error_detail=url_check.error_detail,
            checked_at=checked_at,
        )


def classify_response(
    status_code: int | None, exc: BaseException | None
) -> tuple[CheckOutcome, str | None]:
    match (status_code, exc):
        case (_, requests.Timeout()):
            return CheckOutcome.TIMEOUT, str(exc)
        case (_, requests.ConnectionError()):
            return CheckOutcome.CONNECTION_ERROR, str(exc)
        case (_, BaseException()):
            return CheckOutcome.OTHER_ERROR, str(exc)
        case (None, None):
            return CheckOutcome.OTHER_ERROR, "no status and no exception"
        case (404, None):
            return CheckOutcome.BROKEN_404, None
        case (int(s), None) if 200 <= s < 400:
            return CheckOutcome.OK, None
        case (int(s), None) if 400 <= s < 500:
            return CheckOutcome.CLIENT_ERROR, None
        case (int(s), None) if 500 <= s < 600:
            return CheckOutcome.SERVER_ERROR, None
        case _:
            return CheckOutcome.OTHER_ERROR, f"unexpected status {status_code}"


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
        outcome, detail = classify_response(status, None)
    except requests.RequestException as exc:
        status = None
        outcome, detail = classify_response(None, exc)

    return UrlCheckResult(
        http_status=status,
        outcome=outcome,
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


def run(logger: logging.Logger):
    logger.info("Do the work here")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logger = setup_logging(args.log_path)
    logger.info(args.mode)
    logger.info(args.log_path)
    run(logger=logger)
    return 0


if __name__ == "__main__":
    sys.exit(main())
