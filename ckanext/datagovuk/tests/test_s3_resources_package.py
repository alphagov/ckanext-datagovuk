from mock import patch

from ckanext.datagovuk.controllers.package import S3ResourcesPackageController


class MockAction:
    pkg = None
    rsc = None

    def __init__(self, _type):
        self._type = _type

    def __call__(self, *arg):
        if self._type == 'package_show':
            return self.pkg or {'name': 'test'}
        elif self._type == 'resource_show':
            return self.rsc or {
                'url_type': 'test',
                'name': 'resource-id',
                'url': 'http://test-resource'
            }


class TestS3ResourcesPackageController:

    @patch.dict('ckanext.datagovuk.controllers.package.config',
                {'ckan.datagovuk.s3_url_prefix': 'https://s3.amazonaws.com/test-upload/'})
    @patch('ckanext.datagovuk.controllers.package.toolkit.abort')
    @patch('ckanext.datagovuk.controllers.package.toolkit')
    @patch('ckanext.datagovuk.controllers.package.redirect')
    def test_resource_downloads(self, mock_redirect, mock_toolkit, mock_abort):
        mock_toolkit.get_action = MockAction

        s3_resource = S3ResourcesPackageController()

        s3_resource.resource_download('test-id', 'resource-id')

        assert not mock_abort.called
        assert mock_redirect.called
        assert mock_redirect.call_count == 1
        assert mock_redirect.call_args[0][0] == "https://s3.amazonaws.com/test-upload/test/resources/resource-id.zip"


    @patch.dict('ckanext.datagovuk.controllers.package.config',
                {'ckan.datagovuk.s3_url_prefix': 'https://s3.amazonaws.com/test-upload/'})
    @patch('ckanext.datagovuk.controllers.package.toolkit.abort')
    @patch('ckanext.datagovuk.controllers.package.toolkit')
    @patch('ckanext.datagovuk.controllers.package.redirect')
    def test_resource_downloads_upload(self, mock_redirect, mock_toolkit, mock_abort):
        mock_toolkit.get_action = MockAction

        mock_toolkit.get_action.rsc = {
            'id': 'resource-id',
            'url_type': 'upload',
            'name': 'resource-id',
            'url': 'http://test-resource'
        }

        s3_resource = S3ResourcesPackageController()

        s3_resource.resource_download('test-id', 'resource-id')

        assert not mock_abort.called
        assert mock_redirect.called
        assert mock_redirect.call_count == 1
        assert mock_redirect.call_args[0][0] == "https://s3.amazonaws.com/test-upload/test/resources/resource-id.zip"
