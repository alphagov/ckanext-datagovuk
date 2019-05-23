#
# To run tests:
# pytest --disable-pytest-warnings
#

import pytest

import boto3
from moto import mock_s3
boto3.client('s3')

from bin.fix_organograms_s3_filenames import main


@pytest.fixture
def mock_os_environ(mocker):
    os_environ = {
        'AWS_ACCESS_KEY_ID': 'aws key',
        'AWS_SECRET_ACCESS_KEY': 'aws secret',
        'AWS_REGION': 'us-west-1',
        'AWS_ORG_BUCKET': 'aws-bucket'
    }

    mocker.patch.dict('os.environ', os_environ)

    return os_environ


@mock_s3
def test_fix_organograms_s3_filenames(mocker, mock_os_environ):
    conn = boto3.resource('s3', region_name=mock_os_environ['AWS_REGION'])
    conn.create_bucket(Bucket=mock_os_environ['AWS_ORG_BUCKET'])

    bucket = conn.Bucket(mock_os_environ['AWS_ORG_BUCKET'])

    filenames = [
        'senior-posts-2019-05-01.csv',
        'junior-posts-2019-05-02.csv',
        '2019-05-02.csv',
        '-posts-2019-05-02.csv'
    ]

    for filename in filenames:
        obj = bucket.Object(filename)
        obj.put(Body='A,B,C')

    main('dry-run')
    assert False
