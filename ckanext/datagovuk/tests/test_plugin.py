import pytest
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


@pytest.mark.usefixtures("with_plugins")
class TestPlugin:
    def test_plugin_action_mapping(self):
        action_mapping = DatagovukPlugin().get_actions()

        assert action_mapping['resource_create'] == create.resource_create
        assert action_mapping['user_create'] == create.user_create
        assert action_mapping['user_auth'] == get.user_auth

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
