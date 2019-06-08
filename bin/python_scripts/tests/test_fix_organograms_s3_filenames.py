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
    assert mapping[0] == ('test1', urls[1], 'test1/2019-05-01T12-00-00Z-senior.csv')
    assert mapping[1] == ('test1', urls[2], 'test1/2019-05-01T12-00-00Z-junior.csv')


def test_url_mappings_logs_error(mocker):
    logger_error = mocker.patch('python_scripts.fix_organograms_s3_filenames.logger.error')

    urls = [
        'test0/-posts-2019-05-02T12-00-00Z.csv',
        'test1/senior-posts-2019-05-01T12-00-00Z.csv',
        'test1/junior-posts-2019-05-01T12-00-05Z.csv',
        'test1/junior-posts-2019-05-02T12-00-05Z.csv',
        'test1/senior-posts-2019-05-05T12-00-00Z.csv',
        'test2/2019-05-02.csv',
    ]

    mapping = get_url_mapping(mock_bucket(urls))
    assert len(mapping) == 2

    logger_error.assert_called_once_with(
        'No pairing for junior: %s, senior: %s',
        ['test1/junior-posts-2019-05-02T12-00-05Z.csv'],
        ['test1/senior-posts-2019-05-05T12-00-00Z.csv']
    )


def test_url_mapping_with_multiple_organograms(mocker):
    urls = [
        'test-1/organogram-junior-posts-2019-03-22T15-01-14Z.csv',  # 0
        'test-1/organogram-junior-posts-2019-03-22T15-04-20Z.csv',
        'test-1/organogram-senior-posts-2019-03-22T15-01-10Z.csv',
        'test-1/organogram-senior-posts-2019-03-22T15-04-16Z.csv',
        'test-2/organogram-junior-posts-2019-02-25T07-07-33Z.csv',
        'test-2/organogram-junior-posts-2019-02-28T11-09-03Z.csv',  # 5
        'test-2/organogram-junior-posts-2019-03-07T12-58-31Z.csv',
        'test-2/organogram-senior-posts-2019-02-25T07-07-15Z.csv',
        'test-2/organogram-senior-posts-2019-02-28T11-08-46Z.csv',
        'test-2/organogram-senior-posts-2019-03-07T12-58-16Z.csv',
    ]

    mapping = get_url_mapping(mock_bucket(urls))

    assert mapping[0] == ('test-1', urls[2], 'test-1/2019-03-22T15-01-10Z-organogram-senior.csv')
    assert mapping[1] == ('test-1', urls[0], 'test-1/2019-03-22T15-01-10Z-organogram-junior.csv')
    assert mapping[2] == ('test-1', urls[3], 'test-1/2019-03-22T15-04-16Z-organogram-senior.csv')
    assert mapping[3] == ('test-1', urls[1], 'test-1/2019-03-22T15-04-16Z-organogram-junior.csv')
    assert mapping[4] == ('test-2', urls[7], 'test-2/2019-02-25T07-07-15Z-organogram-senior.csv')
    assert mapping[5] == ('test-2', urls[4], 'test-2/2019-02-25T07-07-15Z-organogram-junior.csv')
    assert mapping[6] == ('test-2', urls[8], 'test-2/2019-02-28T11-08-46Z-organogram-senior.csv')
    assert mapping[7] == ('test-2', urls[5], 'test-2/2019-02-28T11-08-46Z-organogram-junior.csv')
    assert mapping[8] == ('test-2', urls[9], 'test-2/2019-03-07T12-58-16Z-organogram-senior.csv')
    assert mapping[9] == ('test-2', urls[6], 'test-2/2019-03-07T12-58-16Z-organogram-junior.csv')
