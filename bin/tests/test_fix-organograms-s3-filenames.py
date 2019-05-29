#
# To run tests:
# in the bin directory >
# pytest --disable-pytest-warnings
#

import pytest

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


def test_fix_organograms_s3_filenames_without_moto(mocker, mock_os_environ):
    class MockObject:
        def __init__(self, key):
            self.key = key

    files = [
        MockObject('-posts-2019-05-02.csv'),
        MockObject('senior-posts-2019-05-01.csv'),
        MockObject('junior-posts-2019-05-02.csv'),
        MockObject('2019-05-02.csv'),
    ]

    class MockBoto3Resource:
        def __init__(self, *args, **kwargs):
            pass

        def Bucket(self, *args):

            class MockBucket:
                class MockObjects:
                    def all(self):
                        return files

                def __init__(self):
                    self.objects = self.MockObjects()

            return MockBucket()

    mocker.patch('boto3.resource', MockBoto3Resource)

    main('dry-run')
    assert False
