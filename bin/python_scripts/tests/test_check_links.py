import csv
from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock

import pytest
import requests

from python_scripts.check_links import (
    HTTP_TIMEOUT,
    Category,
    CheckResult,
    Reporter,
    ResourceRow,
    check_task,
    classify_response,
    host_key,
    interleave_rows_by_host,
)


@pytest.fixture
def make_row():
    def _make(resource_id: str, url: str) -> ResourceRow:
        return ResourceRow(
            package_id="pkg-id",
            package_name="pkg-name",
            resource_id=resource_id,
            org_name="public sector organisation",
            org_id="org-1",
            url=url,
        )

    return _make


def stub_result(
    row: ResourceRow,
    http_status: int | None = 200,
    category: Category = Category.OK,
) -> CheckResult:
    return CheckResult(
        row=row,
        http_status=http_status,
        category=category,
        error_detail=None,
    )


@pytest.mark.parametrize(
    "status, exc, expected_cat",
    [
        (200, None, Category.OK),
        (301, None, Category.OK),
        (404, None, Category.NOT_FOUND),
        (403, None, Category.OTHER_CLIENT_ERROR),
        (410, None, Category.GONE),
        (429, None, Category.TOO_MANY_REQUESTS),
        (500, None, Category.SERVER_ERROR),
        (503, None, Category.SERVER_ERROR),
        (None, requests.Timeout("timeout"), Category.TIMEOUT),
        (None, requests.ConnectionError("connection error"), Category.CONNECTION_ERROR),
        (None, ValueError("some other error"), Category.OTHER_ERROR),
        (None, None, Category.OTHER_ERROR),
    ],
)
def test_classify_maps_http_and_exceptions_to_categories(status, exc, expected_cat):
    category, detail = classify_response(status, exc)
    assert category is expected_cat
    if exc or (status is None and exc is None):
        assert detail is not None


@pytest.mark.parametrize(
    "category, expected",
    [
        (Category.OK, False),
        (Category.NOT_FOUND, True),
        (Category.GONE, True),
        (Category.TOO_MANY_REQUESTS, False),
        (Category.OTHER_CLIENT_ERROR, False),
        (Category.SERVER_ERROR, False),
        (Category.TIMEOUT, False),
        (Category.CONNECTION_ERROR, False),
        (Category.OTHER_ERROR, False),
    ],
)
def test_to_delete_only_for_definitively_gone(category, expected):
    result = CheckResult(
        row=ResourceRow(
            package_id="pkg-id",
            package_name="pkg-name",
            resource_id="res-id",
            url="https://opendata.gov.uk",
        ),
        http_status=None,
        category=category,
        error_detail=None,
        checked_at=datetime.now(UTC),
    )
    assert result.to_delete is expected


def test_reporter_creates_file_with_header(tmp_path):
    path = tmp_path / "report.csv"
    with Reporter(str(path)):
        pass

    rows = list(csv.reader(path.read_text().splitlines()))
    assert rows == [
        [
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
        ],
    ]


def test_reporter_writes_result_row(tmp_path, make_row):
    path = tmp_path / "report.csv"
    with Reporter(str(path)) as reporter:
        reporter.write(stub_result(
            make_row("res-1", "https://opendata.gov.uk"),
            404,
            Category.NOT_FOUND,
        ))

    rows = list(csv.reader(path.read_text().splitlines()))
    assert rows[1] == [
        "pkg-id",
        "pkg-name",
        "res-1",
        "https://opendata.gov.uk",
        "public sector organisation",
        "org-1",
        "404",
        "NOT_FOUND",
        "",
        "true",
        "",
    ]


def test_reporter_appends_to_existing_file_without_duplicate_header(
    tmp_path, make_row
):
    path = tmp_path / "report.csv"
    with Reporter(str(path)) as reporter:
        reporter.write(stub_result(make_row("res-1", "https://opendata.gov.uk")))
    with Reporter(str(path)) as reporter:
        reporter.write(stub_result(make_row("res-2", "https://opendata.gov.uk")))

    raw_lines = path.read_text().splitlines()
    assert len(raw_lines) == 3  # 1 header + 2 data rows

    rows = list(csv.DictReader(raw_lines))
    assert rows[0]["resource-id"] == "res-1"
    assert rows[1]["resource-id"] == "res-2"


def test_check_task_uses_head_status(make_row):
    session = requests.Session()
    head_response = MagicMock()
    head_response.status_code = 200
    head_response.__enter__.return_value = head_response
    head_response.__exit__.return_value = False
    session.head = Mock(return_value=head_response)

    result = check_task(make_row("res-id", "https://opendata.gov.uk"), session)

    assert result.http_status == 200
    assert result.category is Category.OK
    session.head.assert_called_once_with(
        "https://opendata.gov.uk",
        timeout=HTTP_TIMEOUT,
        allow_redirects=True,
    )


def test_check_task_falls_back_to_get_for_head_fallback_status(make_row):
    session = requests.Session()

    head_response = MagicMock()
    head_response.status_code = 405
    head_response.__enter__.return_value = head_response
    head_response.__exit__.return_value = False
    session.head = Mock(return_value=head_response)

    get_response = MagicMock()
    get_response.status_code = 200
    get_response.__enter__.return_value = get_response
    get_response.__exit__.return_value = False
    session.get = Mock(return_value=get_response)

    result = check_task(make_row("res-id", "https://opendata.gov.uk"), session)

    assert result.http_status == 200
    assert result.category is Category.OK

    session.head.assert_called_once_with(
        "https://opendata.gov.uk",
        timeout=HTTP_TIMEOUT,
        allow_redirects=True,
    )
    session.get.assert_called_once_with(
        "https://opendata.gov.uk",
        timeout=HTTP_TIMEOUT,
        allow_redirects=True,
        stream=True,
    )


def test_interleave_rows_by_host_round_robins_across_hosts(make_row):
    rows = [
        make_row("r1", "https://govtdept.opendata.gov.uk/1"),
        make_row("r2", "https://govtdept.opendata.gov.uk/2"),
        make_row("r3", "https://localgovt.opendata.gov.uk/1"),
        make_row("r4", "https://otherpublicbody.opendata.gov.uk/1"),
        make_row("r5", "https://localgovt.opendata.gov.uk/2"),
        make_row("r6", "https://govtdept.opendata.gov.uk/3"),
    ]

    result = interleave_rows_by_host(rows)

    assert [(r.resource_id, host_key(r.url)) for r in result] == [
        ("r1", "govtdept.opendata.gov.uk"),
        ("r3", "localgovt.opendata.gov.uk"),
        ("r4", "otherpublicbody.opendata.gov.uk"),
        ("r2", "govtdept.opendata.gov.uk"),
        ("r5", "localgovt.opendata.gov.uk"),
        ("r6", "govtdept.opendata.gov.uk"),
    ]


def test_interleave_rows_by_host_preserves_order_for_single_host(make_row):
    rows = [
        make_row("r1", "https://govtdept.opendata.gov.uk/1"),
        make_row("r2", "https://govtdept.opendata.gov.uk/2"),
        make_row("r3", "https://govtdept.opendata.gov.uk/3"),
    ]

    assert interleave_rows_by_host(rows) == rows
