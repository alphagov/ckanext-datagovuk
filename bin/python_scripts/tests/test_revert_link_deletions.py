import csv
import logging
from unittest.mock import MagicMock, call

import pytest

from python_scripts.check_links import REPORT_HEADERS
from python_scripts.revert_link_deletions import revert


@pytest.fixture
def logger():
    return logging.getLogger("test_revert_link_deletions")


@pytest.fixture
def write_csv(tmp_path):
    """Factory: write a CSV matching check_links' report format."""

    def _write(rows: list[dict]) -> str:
        path = tmp_path / "report.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=REPORT_HEADERS, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        return str(path)

    return _write


def _row(
    *,
    package_id: str = "pkg-1",
    resource_id: str = "res-1",
    to_delete: str = "false",
) -> dict:
    return {
        "package-id": package_id,
        "package-name": "pkg-name",
        "resource-id": resource_id,
        "resource-url": "https://opendata.gov.uk",
        "http-status": "200",
        "category": "OK",
        "error-detail": "",
        "to-delete": to_delete,
        "checked-at": "2026-01-02T03:04:05+00:00",
    }


def test_dry_run_writes_reindex_without_touching_db(tmp_path, write_csv, logger):
    input_path = write_csv(
        [
            _row(resource_id="res-1", package_id="pkg-1", to_delete="true"),
            _row(resource_id="res-2", package_id="pkg-2", to_delete="true"),
            _row(resource_id="res-3", package_id="pkg-3", to_delete="false"),
        ]
    )
    reindex_path = str(tmp_path / "reindex.txt")
    repo = MagicMock()

    revert(
        logger=logger,
        repository=repo,
        input_path=input_path,
        reindex_path=reindex_path,
        mode="dry-run",
    )

    repo.mark_resource_active.assert_not_called()
    with open(reindex_path) as f:
        assert f.read().splitlines() == ["pkg-1", "pkg-2"]


def test_live_calls_repository_only_for_to_delete_rows(tmp_path, write_csv, logger):
    input_path = write_csv(
        [
            _row(resource_id="res-1", package_id="pkg-1", to_delete="true"),
            _row(resource_id="res-skip", package_id="pkg-skip", to_delete="false"),
            _row(resource_id="res-2", package_id="pkg-2", to_delete="true"),
        ]
    )
    reindex_path = str(tmp_path / "reindex.txt")
    repo = MagicMock()
    repo.mark_resource_active.return_value = 1

    revert(
        logger=logger,
        repository=repo,
        input_path=input_path,
        reindex_path=reindex_path,
        mode="live",
    )

    assert repo.mark_resource_active.call_args_list == [
        call("res-1", "pkg-1"),
        call("res-2", "pkg-2"),
    ]
    with open(reindex_path) as f:
        assert f.read().splitlines() == ["pkg-1", "pkg-2"]
