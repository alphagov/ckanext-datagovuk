#!/usr/bin/env python3
import unittest
from mock import patch

from ckanext.datagovuk.plugin import DatagovukPlugin
from nose.tools import assert_raises


class TestS3ResourcesPlugin(unittest.TestCase):
    plugin = DatagovukPlugin()

    def test_s3_config_exception(self):
        with assert_raises(KeyError) as context:
            self.plugin.before_create_or_update({}, {"upload": "dummy value"})

        assert context.exception.message == "Required S3 config options missing"

    @patch("ckanext.datagovuk.plugin.upload.config_exists")
    def test_upload_early_abort(self, mock_check_config):
        resource = {
            "package_id": u"some-pointless-data-1",
            "url": "organogram-senior.csv",
            "timestamp": "2020-01-09T12-11-41Z",
            "name": "2020-01-09 Organogram (Senior)",
        }

        self.plugin.before_create_or_update({}, resource)
        assert not mock_check_config.called

    @patch("ckanext.datagovuk.plugin.upload.config_exists")
    def test_format_api_early_abort(self, mock_check_config):
        resource = {
            "package_id": u"some-pointless-data-1",
            "url": "organogram-senior.csv",
            "timestamp": "2020-01-09T12-11-41Z",
            "name": "2020-01-09 Organogram (Senior)",
            "format": "API",
            "upload": "test.csv"
        }

        self.plugin.before_create_or_update({}, resource)
        assert not mock_check_config.called
