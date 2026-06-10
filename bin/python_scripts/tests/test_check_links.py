import csv
from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock

import pytest
import requests

from python_scripts.check_links import (
    HTTP_TIMEOUT,
    REPORT_HEADERS,
    Category,
    CheckResult,
    Reporter,
    ResourceRow,
    check_task,
    classify_response,
    host_key,
    interleave_rows_by_host,
    session_factory,
)


@pytest.fixture
def make_row():
    def _make(
        resource_id: str,
        url: str,
        resource_created: datetime | None = datetime(2020, 1, 1, 0, 0, tzinfo=UTC),
        resource_last_modified: datetime | None = datetime(
            2026, 1, 1, 0, 0, tzinfo=UTC
        ),
        resource_metadata_modified: datetime | None = datetime(
            2026, 1, 1, 0, 0, tzinfo=UTC
        ),
        package_metadata_created: datetime | None = datetime(
            2010, 1, 1, 0, 0, tzinfo=UTC
        ),
        package_metadata_modified: datetime | None = datetime(
            2026, 1, 1, 0, 0, tzinfo=UTC
        ),
    ) -> ResourceRow:
        return ResourceRow(
            package_id="pkg-id",
            package_name="pkg-name",
            resource_id=resource_id,
            org_name="public sector organisation",
            org_id="org-1",
            url=url,
            resource_created=resource_created,
            resource_last_modified=resource_last_modified,
            resource_metadata_modified=resource_metadata_modified,
            package_metadata_created=package_metadata_created,
            package_metadata_modified=package_metadata_modified,
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


def _stub_dns_connection_error() -> requests.ConnectionError:
    # stub error requests raises when the host fails to resolve.
    return requests.ConnectionError(
        "HTTPSConnectionPool(host='no-such-host.example', port=443): Max retries "
        "exceeded (Caused by NameResolutionError(\"Failed to resolve "
        "'no-such-host.example' ([Errno -2] Name or service not known)\"))"
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
        (None, _stub_dns_connection_error(), Category.DNS_ERROR),
        (
            None,
            requests.ConnectionError(ConnectionRefusedError(111, "Connection refused")),
            Category.CONNECTION_REFUSED,
        ),
        (None, requests.exceptions.SSLError("bad handshake"), Category.CONNECTION_ERROR),
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
        (Category.DNS_ERROR, True),
        (Category.CONNECTION_REFUSED, True),
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
    assert rows == [REPORT_HEADERS]


def test_reporter_writes_result_row(tmp_path, make_row):
    path = tmp_path / "report.csv"
    with Reporter(str(path)) as reporter:
        reporter.write(
            stub_result(
                make_row("res-1", "https://opendata.gov.uk"),
                404,
                Category.NOT_FOUND,
            )
        )

    rows = list(csv.reader(path.read_text().splitlines()))
    assert rows[1] == [
        "https://www.data.gov.uk/dataset/pkg-id/pkg-name",
        "pkg-id",
        "pkg-name",
        "2010-01-01",
        "2026-01-01",
        "res-1",
        "https://opendata.gov.uk",
        "2020-01-01",
        "2026-01-01",
        "2026-01-01",
        "public sector organisation",
        "org-1",
        "404",
        "NOT_FOUND",
        "",
        "true",
        "",
    ]


def test_reporter_renders_none_dates_as_empty(tmp_path, make_row):
    path = tmp_path / "report.csv"
    row = make_row(
        "res-1",
        "https://opendata.gov.uk",
        resource_last_modified=None,
        resource_metadata_modified=None,
        package_metadata_created=None,
        package_metadata_modified=None,
    )
    with Reporter(str(path)) as reporter:
        reporter.write(stub_result(row))

    rows = list(csv.DictReader(path.read_text().splitlines()))
    assert rows[0]["resource-last-modified"] == ""
    assert rows[0]["resource-metadata-modified"] == ""
    assert rows[0]["package-metadata-created"] == ""
    assert rows[0]["package-metadata-modified"] == ""
    assert rows[0]["resource-created"] == "2020-01-01"


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


def test_check_task_classifies_server_error_with_status(make_row):
    session = requests.Session()
    head_response = MagicMock()
    head_response.status_code = 503
    head_response.__enter__.return_value = head_response
    head_response.__exit__.return_value = False
    session.head = Mock(return_value=head_response)

    result = check_task(make_row("res-id", "https://opendata.gov.uk"), session)

    assert result.http_status == 503
    assert result.category is Category.SERVER_ERROR


def test_session_factory_retry_does_not_raise_on_status():
    # Retry must return the final 5xx response rather than raising RetryError,
    # otherwise check_task loses the status code and misclassifies it as
    # OTHER_ERROR instead of SERVER_ERROR.
    session = session_factory()
    retry = session.get_adapter("https://opendata.gov.uk").max_retries
    assert retry.raise_on_status is False
    assert set(retry.status_forcelist) == {500, 502, 503, 504}


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
