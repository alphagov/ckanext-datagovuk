import pytest
import requests

from python_scripts.check_links import (
    CheckOutcome,
    classify_response,
)


@pytest.mark.parametrize(
    "status, exc, expected_cat",
    [
        (200, None, CheckOutcome.OK),
        (301, None, CheckOutcome.OK),
        (404, None, CheckOutcome.BROKEN_404),
        (403, None, CheckOutcome.OTHER_4XX),
        (410, None, CheckOutcome.OTHER_4XX),
        (500, None, CheckOutcome.FIVE_XX),
        (503, None, CheckOutcome.FIVE_XX),
        (None, requests.Timeout("timeout"), CheckOutcome.TIMEOUT),
        (None, requests.ConnectionError("connection error"), CheckOutcome.CONN_ERROR),
        (None, ValueError("some other error"), CheckOutcome.OTHER_ERROR),
        (None, None, CheckOutcome.OTHER_ERROR),
    ],
)
def test_classify_maps_http_and_exceptions_to_categories(status, exc, expected_cat):
    category, detail = classify_response(status, exc)
    assert category is expected_cat
    if exc or (status is None and exc is None):
        assert detail is not None
