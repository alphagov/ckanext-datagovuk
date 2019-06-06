#
# To run tests:
# in the ./bin/python_scripts directory >
# pytest --disable-pytest-warnings
#

import pytest
from mock import call

from python_scripts.fix_organograms_s3_filenames import get_url_mapping


class MockObject:
    def __init__(self, key):
        self.key = key


def mock_bucket(_urls):
    urls = [MockObject(url) for url in _urls]

    class MockBucket:
        class MockObjects:
            def all(self):
                return urls

        def __init__(self):
            self.objects = self.MockObjects()

    return MockBucket()


def test_url_mappings_set_senior_timestamp_for_junior(mocker):
    urls = [
        'test0/-posts-2019-05-02T12-00-00Z.csv',
        'test1/senior-posts-2019-05-01T12-00-00Z.csv',
        'test1/junior-posts-2019-05-01T12-00-05Z.csv',
        'test2/2019-05-02.csv',
    ]

    mapping = get_url_mapping(mock_bucket(urls))

    assert len(mapping) == 2
    assert mapping[0][0] == 'test1'
    assert mapping[0][1] == urls[1]
    assert mapping[0][2] == 'test1/2019-05-01T12-00-00Z-senior.csv'
    assert mapping[1][0] == 'test1'
    assert mapping[1][1] == urls[2]
    assert mapping[1][2] == 'test1/2019-05-01T12-00-00Z-junior.csv'


def test_url_mappings_logs_error(mocker):
    logger_error = mocker.patch('python_scripts.fix_organograms_s3_filenames.logger.error')

    urls = [
        'test0/-posts-2019-05-02T12-00-00Z.csv',
        'test1/senior-posts-2019-05-01T12-00-00Z.csv',
        'test1/junior-posts-2019-05-01T12-00-05Z.csv',
        'test1/senior-posts-2019-05-02T12-00-00Z.csv',
        'test1/junior-posts-2019-05-02T12-00-05Z.csv',
        'test2/2019-05-02.csv',
    ]

    mapping = get_url_mapping(mock_bucket(urls))

    assert mapping == []
    logger_error.assert_called_once_with(
        'Did not find exactly 1 senior and 1 junior matching file: %s, found %s senior, %s junior',
        'test1', 2, 2
    )
