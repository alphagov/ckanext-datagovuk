from unittest.mock import MagicMock, Mock

import pytest
import requests

from python_scripts.check_links import (
    HTTP_TIMEOUT,
    CheckOutcome,
    ResourceRow,
    check_url,
    classify_response,
)


@pytest.mark.parametrize(
    "status, exc, expected_cat",
    [
        (200, None, CheckOutcome.OK),
        (301, None, CheckOutcome.OK),
        (404, None, CheckOutcome.BROKEN_404),
        (403, None, CheckOutcome.CLIENT_ERROR),
        (410, None, CheckOutcome.CLIENT_ERROR),
        (500, None, CheckOutcome.SERVER_ERROR),
        (503, None, CheckOutcome.SERVER_ERROR),
        (None, requests.Timeout("timeout"), CheckOutcome.TIMEOUT),
        (None, requests.ConnectionError("connection error"), CheckOutcome.CONNECTION_ERROR),
        (None, ValueError("some other error"), CheckOutcome.OTHER_ERROR),
        (None, None, CheckOutcome.OTHER_ERROR),
    ],
)
def test_classify_maps_http_and_exceptions_to_categories(status, exc, expected_cat):
    category, detail = classify_response(status, exc)
    assert category is expected_cat
    if exc or (status is None and exc is None):
        assert detail is not None


def test_check_url_uses_head_status():
    session = requests.Session()
    session.head = Mock(return_value=Mock(status_code=200))

    result = check_url(session, "https://opendata.gov.uk")

    assert result.http_status == 200
    assert result.outcome is CheckOutcome.OK
    session.head.assert_called_once_with(
        "https://opendata.gov.uk",
        timeout=HTTP_TIMEOUT,
        allow_redirects=True,
    )


def test_check_url_falls_back_to_get_for_head_fallback_status():
    session = requests.Session()

    session.head = Mock(return_value=Mock(status_code=405))

    get_response = MagicMock()
    get_response.status_code = 200
    get_response.__enter__.return_value = get_response
    get_response.__exit__.return_value = False
    session.get = Mock(return_value=get_response)

    result = check_url(session, "https://opendata.gov.uk")

    assert result.http_status == 200
    assert result.outcome is CheckOutcome.OK

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
