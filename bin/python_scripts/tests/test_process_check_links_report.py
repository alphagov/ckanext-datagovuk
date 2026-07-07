import csv
import logging
from unittest.mock import MagicMock, call

import pytest

from python_scripts.old_check_links import REPORT_HEADERS
from python_scripts.process_check_links_report import apply


@pytest.fixture
def logger():
    return logging.getLogger("test_process_check_links_report")


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


def test_dry_run_skips_writing_reindex_and_updating_db(tmp_path, write_csv, logger):
    input_path = write_csv(
        [
            _row(resource_id="res-1", package_id="pkg-1", to_delete="true"),
            _row(resource_id="res-2", package_id="pkg-2", to_delete="true"),
            _row(resource_id="res-3", package_id="pkg-3", to_delete="false"),
        ]
    )
    reindex_path = str(tmp_path / "reindex.txt")
    output_report_path = str(tmp_path / "output_report_path.csv")
    repo = MagicMock()

    apply(
        logger=logger,
        repository=repo,
        input_path=input_path,
        reindex_path=reindex_path,
        output_report_path=output_report_path,
        mode="dry-run",
        set_state="deleted",
    )

    repo.updated_resource.assert_not_called()

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
    output_report_path = str(tmp_path / "output_report_path.csv")
    repo = MagicMock()
    repo.update_resource.return_value = 2

    apply(
        logger=logger,
        repository=repo,
        input_path=input_path,
        reindex_path=reindex_path,
        output_report_path=output_report_path,
        mode="live",
        set_state="deleted",
    )

    assert repo.update_resource.call_args_list == [
        call("res-1", "pkg-1", "deleted"),
        call("res-2", "pkg-2", "deleted"),
    ]
    with open(reindex_path) as f:
        assert f.read().splitlines() == ["pkg-1", "pkg-2"]


def test_live_records_update_deleted_with_timestamp(tmp_path, write_csv, logger):
    input_path = write_csv(
        [
            _row(resource_id="res-1", package_id="pkg-1", to_delete="true"),
            _row(resource_id="res-skip", package_id="pkg-skip", to_delete="false"),
            _row(resource_id="res-2", package_id="pkg-2", to_delete="true"),
        ]
    )
    reindex_path = str(tmp_path / "reindex.txt")
    output_report_path = str(tmp_path / "output_report_path.csv")
    repo = MagicMock()
    repo.update_resource.return_value = 2

    apply(
        logger=logger,
        repository=repo,
        input_path=input_path,
        reindex_path=reindex_path,
        output_report_path=output_report_path,
        mode="live",
        set_state="deleted",
    )

    assert repo.update_resource.call_args_list == [
        call("res-1", "pkg-1", "deleted"),
        call("res-2", "pkg-2", "deleted"),
    ]
    with open(output_report_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            assert row.get("update-applied", "") == "deleted"
            assert row.get("update-applied-on", "") != ""


def test_live_records_update_active_with_timestamp(tmp_path, write_csv, logger):
    input_path = write_csv(
        [
            _row(resource_id="res-1", package_id="pkg-1", to_delete="true"),
            _row(resource_id="res-skip", package_id="pkg-skip", to_delete="false"),
            _row(resource_id="res-2", package_id="pkg-2", to_delete="true"),
        ]
    )
    reindex_path = str(tmp_path / "reindex.txt")
    output_report_path = str(tmp_path / "output_report_path.csv")
    repo = MagicMock()
    repo.update_resource.return_value = 2

    apply(
        logger=logger,
        repository=repo,
        input_path=input_path,
        reindex_path=reindex_path,
        output_report_path=output_report_path,
        mode="live",
        set_state="active",
    )

    assert repo.update_resource.call_args_list == [
        call("res-1", "pkg-1", "active"),
        call("res-2", "pkg-2", "active"),
    ]
    with open(output_report_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            assert row.get("update-applied", "") == "active"
            assert row.get("update-applied-on", "") != ""
