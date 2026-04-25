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
)


@pytest.fixture
def make_result():
    def _factory(
        *,
        package_id: str = "pkg-1",
        package_name: str = "pkg-name",
        resource_id: str = "res-1",
        url: str = "https://opendata.gov.uk",
        http_status: int | None = 200,
        category: Category = Category.OK,
        error_detail: str | None = None,
    ) -> CheckResult:
        return CheckResult(
            row=ResourceRow(
                package_id=package_id,
                package_name=package_name,
                resource_id=resource_id,
                url=url,
            ),
            http_status=http_status,
            category=category,
            error_detail=error_detail,
            checked_at=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
        )

    return _factory


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
            "http-status",
            "category",
            "error-detail",
            "to-delete",
            "checked-at",
        ],
    ]


def test_reporter_writes_result_row(tmp_path, make_result):
    path = tmp_path / "report.csv"
    with Reporter(str(path)) as reporter:
        reporter.write(make_result(http_status=404, category=Category.NOT_FOUND))

    rows = list(csv.reader(path.read_text().splitlines()))
    assert rows[1] == [
        "pkg-1",
        "pkg-name",
        "res-1",
        "https://opendata.gov.uk",
        "404",
        "404",
        "",
        "true",
        "2026-01-02T03:04:05+00:00",
    ]


def test_reporter_appends_to_existing_file_without_duplicate_header(
    tmp_path, make_result
):
    path = tmp_path / "report.csv"
    with Reporter(str(path)) as reporter:
        reporter.write(make_result(resource_id="res-1"))
    with Reporter(str(path)) as reporter:
        reporter.write(make_result(resource_id="res-2"))

    raw_lines = path.read_text().splitlines()
    assert len(raw_lines) == 3  # 1 header + 2 data rows

    rows = list(csv.DictReader(raw_lines))
    assert rows[0]["resource-id"] == "res-1"
    assert rows[1]["resource-id"] == "res-2"


def _row(url: str = "https://opendata.gov.uk") -> ResourceRow:
    return ResourceRow(
        package_id="pkg-id",
        package_name="pkg-name",
        resource_id="res-id",
        url=url,
    )


def test_check_task_uses_head_status():
    session = requests.Session()
    session.head = Mock(return_value=Mock(status_code=200))

    result = check_task(_row(), session)

    assert result.http_status == 200
    assert result.category is Category.OK
    session.head.assert_called_once_with(
        "https://opendata.gov.uk",
        timeout=HTTP_TIMEOUT,
        allow_redirects=True,
    )


def test_check_task_falls_back_to_get_for_head_fallback_status():
    session = requests.Session()

    session.head = Mock(return_value=Mock(status_code=405))

    get_response = MagicMock()
    get_response.status_code = 200
    get_response.__enter__.return_value = get_response
    get_response.__exit__.return_value = False
    session.get = Mock(return_value=get_response)

    result = check_task(_row(), session)

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
