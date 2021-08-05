#!/usr/bin/env python3
import cgi
from io import StringIO
import pytest
import unittest

from ckan.common import config
from botocore.exceptions import ClientError
from ckanext.datagovuk.plugin import DatagovukPlugin
from ckanext.datagovuk.upload import upload_resource_to_s3
from mock import Mock, patch
from nose.tools import assert_raises


class MockAction:
    def __init__(self, _type):
        self._type = _type

    def __call__(self, *arg):
        if self._type == "package_show":
            return {"name": "test"}


@pytest.mark.ckan_config("ckan.datagovuk.s3_aws_access_key_id", "key-id")
@pytest.mark.ckan_config("ckan.datagovuk.s3_aws_secret_access_key", "secret-key")
@pytest.mark.ckan_config("ckan.datagovuk.s3_bucket_name", "test-bucket")
@pytest.mark.ckan_config("ckan.datagovuk.s3_url_prefix", "https://s3.amazonaws.com/test/")
@pytest.mark.ckan_config("ckan.datagovuk.s3_aws_region_name", "eu-west-1")
class TestUpload:
    upload = cgi.FieldStorage()
    upload.file = StringIO("hello world")
    resource = {
        "package_id": u"some-pointless-data-1",
        "clear_upload": u"",
        "url": "organogram-senior.csv",
        "timestamp": "2020-01-09T12-11-41Z",
        "datafile-date": u"",
        "upload": upload,
        "name": "2020-01-09 Organogram (Senior)",
    }

    @patch("ckanext.datagovuk.upload.update_timestamp")
    @patch("boto3.resource")
    @patch("ckanext.datagovuk.upload.toolkit.abort")
    @patch("ckanext.datagovuk.upload.toolkit")
    def test_upload(self, mock_toolkit, mock_abort, mock_resource, mock_update_timestamp):
        mock_toolkit.get_action = MockAction

        resource = self.resource.copy()

        upload_resource_to_s3({}, resource)
        assert not mock_abort.called
        assert config.get("ckan.datagovuk.s3_url_prefix") in resource["url"]
        assert resource["url"].endswith("organogram-senior.csv")
        assert mock_update_timestamp.called

    @patch("ckanext.datagovuk.upload.update_timestamp")
    @patch("boto3.resource")
    @patch("ckanext.datagovuk.upload.toolkit")
    def test_upload_url_doesnt_upload_to_s3(self, mock_toolkit, mock_resource, mock_update_timestamp):
        mock_toolkit.get_action = MockAction

        resource = self.resource.copy()
        resource['url'] = "http://example.com/test.csv"
        del resource["upload"]

        upload_resource_to_s3({}, resource)
        assert not mock_update_timestamp.called

    @patch("botocore.client.BaseClient._make_api_call")
    @patch("ckanext.datagovuk.upload.toolkit")
    def test_upload_s3_exception(self, mock_toolkit, mock_api_call):
        mock_toolkit.get_action = MockAction
        mock_api_call.side_effect = ClientError({"Error": {}}, "Unknown")

        resource = self.resource.copy()

        with assert_raises(ClientError):
            upload_resource_to_s3({}, resource)
        assert config.get("ckan.datagovuk.s3_url_prefix") not in resource["url"]
