"""Tests for plugin.py."""
import unittest

from ckan.lib.navl.dictization_functions import augment_data
from ckan.lib.navl.validators import ignore

from ckanext.datagovuk.plugin import DatagovukPlugin
from ckanext.datagovuk.action import create, get

sample_data = {
    ('extras', 0, u'id'): u'test-id',
    ('name',): u'test-package',
    ('extras', 1, u'id'): u'test-id',
    ('extras', 1, u'key'): u'access_constraints',
    ('extras', 0, u'value'): u'True',
    ('id',): u'test-dataset-id',
    ('harvest', 0, 'key'): 'harvest_object_id',
    ('harvest', 0, 'value'): u'harvest_obj_val',
    ('harvest', 1, 'key'): 'harvest_source_id',
    ('harvest', 1, 'value'): u'harvest_source_id_val',
    ('harvest', 2, 'key'): 'harvest_source_title',
    ('harvest', 2, 'value'): u'harvest_source_title_val',
}

sample_data_invalid = {
    ('extras', 0, u'id'): u'test-id',
    ('name',): u'test-package',
    ('extras', 1, u'id'): u'test-id',
    ('extras', 1, u'key'): u'access_constraints',
    ('extras', 0, u'value'): u'True',
    ('id',): u'test-dataset-id',
    ('invalid', 0, 'key'): 'invalid_id',
    ('invalid', 0, 'value'): u'invalid_id_val',
}


class TestPlugin(unittest.TestCase):
    def test_plugin_action_mapping(self):
        action_mapping = DatagovukPlugin().get_actions()

        self.assertEqual(action_mapping['resource_create'], create.resource_create)
        self.assertEqual(action_mapping['user_create'], create.user_create)
        self.assertEqual(action_mapping['user_auth'], get.user_auth)

    def test_plugin_schema_update(self):
        package_schema = DatagovukPlugin().update_package_schema()
        data = augment_data(sample_data, package_schema)

        assert ('__junk',) not in data

    def test_plugin_schema_update_invalid(self):
        package_schema = DatagovukPlugin().update_package_schema()

        data = augment_data(sample_data_invalid, package_schema)

        assert ('__junk',) in data
        assert ('invalid', 0, 'key') in data[('__junk',)]
        assert ('invalid', 0, 'value') in data[('__junk',)]

    def test_plugin_before_send(self):
        mock_event  = {
            'logentry': {
                'message': 'System error'
            }
        }
        response = DatagovukPlugin().before_send(mock_event, '')

        assert response == mock_event

    def test_plugin_before_send_ignores_data_errors(self):
        mock_events = [
            {'logentry': {'message': 'Found more than one dataset with the same guid xxx'}},
            {'logentry': {'message': 'Errors found for object with GUID xxx'}},
            {'logentry': {'message': 'Job timeout: xxx is taking longer than yyy minutes'}},
            {'logentry': {'message': 'Job xxx was aborted or timed out, object yyy set to error'}},
            {'logentry': {'message': 'Too many consecutive retries for object'}},
            {'logentry': {'message': 'Harvest object does not exist: xxx'}}
        ]

        for mock_event in mock_events:
            response = DatagovukPlugin().before_send(mock_event, '')
            assert not response
