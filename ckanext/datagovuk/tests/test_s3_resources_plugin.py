#!/usr/bin/env python3
import cgi
from StringIO import StringIO

import pylons.config as config
from botocore.exceptions import ClientError
from ckanext.datagovuk.plugin import DatagovukPlugin
from mock import Mock, patch
from nose.tools import assert_raises


class MockAction:
    def __init__(self, _type):
        self._type = _type

    def __call__(self, *arg):
        if self._type == "package_show":
            return {"name": "test"}


@patch.dict(
    "pylons.config",
    {
        "ckan.datagovuk.s3_aws_access_key_id": "key-id",
        "ckan.datagovuk.s3_aws_secret_access_key": "secret-key",
        "ckan.datagovuk.s3_bucket_name": "test-bucket",
        "ckan.datagovuk.s3_url_prefix": "https://s3.amazonaws.com/test/",
        "ckan.datagovuk.s3_aws_region_name": "eu-west-1",
    },
)
class TestS3ResourcesPlugin:
    upload = cgi.FieldStorage()
    upload.file = StringIO("hello world")
    resource = {
        "package_id": u"some-pointless-data-3",
        "clear_upload": u"",
        "url": "organogram-senior.csv",
        "timestamp": "2020-01-09T12-11-41Z",
        "datafile-date": u"",
        "upload": upload,
        "name": "2020-01-09 Organogram (Senior)",
    }

    @patch.dict("pylons.config", {}, clear=True)
    def test_s3_config_exception(self):
        plugin = DatagovukPlugin()
        with assert_raises(KeyError) as context:
            plugin.before_create_or_update({}, {"upload": "dummy value"})

        assert context.exception.message == "Required S3 config options missing"

    @patch("boto3.resource")
    @patch("ckanext.datagovuk.upload.toolkit.abort")
    @patch("ckanext.datagovuk.upload.toolkit")
    def test_before_create_or_update(self, mock_toolkit, mock_abort, mock_resource):
        mock_toolkit.get_action = MockAction

        plugin = DatagovukPlugin()
        resource = self.resource.copy()

        plugin.before_create_or_update({}, resource)
        assert not mock_abort.called
        assert config.get("ckan.datagovuk.s3_url_prefix") in resource["url"]

    @patch("boto3.resource")
    @patch("ckanext.datagovuk.upload.toolkit.abort")
    @patch("ckanext.datagovuk.upload.toolkit")
    def test_before_create_or_update_empty_upload(
        self, mock_toolkit, mock_abort, mock_resource
    ):
        mock_toolkit.get_action = MockAction

        plugin = DatagovukPlugin()
        resource = self.resource.copy()
        resource["upload"] = ""

        plugin.before_create_or_update({}, resource)
        assert not mock_abort.called
        assert config.get("ckan.datagovuk.s3_url_prefix") not in resource["url"]

    @patch("boto3.resource")
    @patch("ckanext.datagovuk.upload.toolkit.abort")
    @patch("ckanext.datagovuk.upload.toolkit")
    def test_before_create_or_update_undefined_upload(
        self, mock_toolkit, mock_abort, mock_resource
    ):
        mock_toolkit.get_action = MockAction

        plugin = DatagovukPlugin()
        resource = self.resource.copy()
        del resource["upload"]

        plugin.before_create_or_update({}, resource)
        assert not mock_abort.called
        assert config.get("ckan.datagovuk.s3_url_prefix") not in resource["url"]

    @patch("boto3.resource")
    @patch("ckanext.datagovuk.upload.toolkit.abort")
    @patch("ckanext.datagovuk.upload.toolkit")
    def test_before_create_or_update_upload_api(
        self, mock_toolkit, mock_abort, mock_resource
    ):
        mock_toolkit.get_action = MockAction

        plugin = DatagovukPlugin()
        resource = self.resource.copy()
        resource["format"] = "API"

        plugin.before_create_or_update({}, resource)
        assert not mock_abort.called
        assert config.get("ckan.datagovuk.s3_url_prefix") not in resource["url"]

    @patch("boto3.resource")
    @patch("ckanext.datagovuk.upload.toolkit.abort")
    @patch("ckanext.datagovuk.upload.toolkit")
    def test_upload_early_abort(self, mock_toolkit, mock_abort, mock_resource):
        mock_toolkit.get_action = MockAction

        plugin = DatagovukPlugin()
        resource = self.resource.copy()
        resource["upload"] = "dummy data"  # *not* a FieldStorage

        plugin.before_create_or_update({}, resource)
        assert not mock_abort.called
        assert config.get("ckan.datagovuk.s3_url_prefix") not in resource["url"]

    @patch("botocore.client.BaseClient._make_api_call")
    @patch("ckanext.datagovuk.upload.toolkit.abort")
    @patch("ckanext.datagovuk.upload.toolkit")
    def test_upload_s3_exception(self, mock_toolkit, mock_abort, mock_api_call):
        mock_toolkit.get_action = MockAction
        mock_api_call.side_effect = ClientError({"Error": {}}, "Unknown")

        plugin = DatagovukPlugin()
        resource = self.resource.copy()

        with assert_raises(ClientError):
            plugin.before_create_or_update({}, resource)
        assert config.get("ckan.datagovuk.s3_url_prefix") not in resource["url"]
