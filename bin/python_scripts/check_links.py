import sys
import argparse
import logging

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
        help="default: 'dry-run' doesn't update db, creates report"
    )
    parser.add_argument("--log-path", default=LOG_FILE)
    return parser.parse_args(argv)


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

