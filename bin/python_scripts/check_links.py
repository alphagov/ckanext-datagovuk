import argparse
import logging
import sys
from dataclasses import dataclass, field
from enum import StrEnum

import requests

LOG_FILE = "check_links.log"


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
    OTHER_4XX = "OTHER_4XX"
    FIVE_XX = "5XX"
    TIMEOUT = "TIMEOUT"
    CONN_ERROR = "CONN_ERROR"
    SKIP_NON_HTTP = "SKIP_NON_HTTP"
    OTHER_ERROR = "OTHER_ERROR"


@dataclass(frozen=True)
class ResourceRow:
    """
    Represents a package (dataset) resource and its url from db
    """

    package_id: str
    package_name: str
    resource_id: str
    url: str


@dataclass
class CheckResult:
    """
    Represents a row in a csv report file showing results of resource url checks
    """

    row: ResourceRow
    http_status: int | None
    outcome: CheckOutcome
    error_detail: str | None
    checked_at: CheckOutcome

    @property
    def to_delete(self) -> bool:
        return self.outcome is CheckOutcome.BROKEN_404


def classify_response(
    status_code: int | None, exc: BaseException | None
) -> tuple[CheckOutcome, str | None]:
    match (status_code, exc):
        case (_, requests.Timeout()):
            return CheckOutcome.TIMEOUT, str(exc)
        case (_, requests.ConnectionError()):
            return CheckOutcome.CONN_ERROR, str(exc)
        case (_, BaseException()):
            return CheckOutcome.OTHER_ERROR, str(exc)
        case (None, None):
            return CheckOutcome.OTHER_ERROR, "no status and no exception"
        case (404, None):
            return CheckOutcome.BROKEN_404, None
        case (int(s), None) if 200 <= s < 400:
            return CheckOutcome.OK, None
        case (int(s), None) if 400 <= s < 500:
            return CheckOutcome.OTHER_4XX, None
        case (int(s), None) if 500 <= s < 600:
            return CheckOutcome.FIVE_XX, None
        case _:
            return CheckOutcome.OTHER_ERROR, f"unexpected status {status_code}"


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
