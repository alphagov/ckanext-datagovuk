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
            {'logentry': {'message': 'Harvest object does not exist: xxx'}},
            {'logentry': {'message': 'Harvest job does not exist: xxx'}},
            {'logentry': {'message': 'Gather stage failed'}},
            {'logentry': {'message': '404 Not Found: Group not found'}},
            {'logentry': {'message': 'User  not authorised to create packages'}},
            {'logentry': {'message': 'User  not authorised to read resource xxx'}},
            {'logentry': {'message': 'User  not authorised to read package xxx'}},
            {'logentry': {'message': '404 Not Found: Dataset not found'}},
            {'logentry': {'message': '404 Not Found: Resource not found'}},
            {'logentry': {'message': 'Action resource_create requires an authenticated user'}},
            {'logentry': {'message': '401 Unauthorized: Not authorised to see this page'}},
            {'logentry': {'message': 
                '404 Not Found: The requested URL was not found on the server. If you entered the URL '
                'manually please check your spelling and try again.'}
            },
            {'logentry': {'message': 'The email address \'test@example.gov\' belongs to a registered user.'}},
            {'logentry': {
                'message': "None - {'author_email': ['Email example@test.uk  is not a valid "
                "format'], 'maintainer_email': ['Email example2@test.uk  is not a valid format']}"
                }
            },
            {'logentry': {'message': 'CSW identifier \'xxx-yyy-111-222\' already used, skipping'}},
            {'logentry': {'message': 'CSW identifier \'{xxx-yyy-111-222}\' already used, skipping'}},
            {'logentry': {
                'message': '''Exception during import: Traceback (most recent call last):
  File "/data/vhost/ckan/shared/venv/lib/python2.7/site-packages/ckanext/spatial/harvesters/gemini.py", line 74, in import_stage
    return self.import_gemini_object(harvest_object)
  File "/data/vhost/ckan/shared/venv/lib/python2.7/site-packages/ckanext/spatial/harvesters/gemini.py", line 110, in import_gemini_object
    package_dict = self.write_package_from_gemini_string(unicode_gemini_string, harvest_object)
  File "/data/vhost/ckan/shared/venv/lib/python2.7/site-packages/ckanext/spatial/harvesters/gemini.py", line 177, in write_package_from_gemini_string
    harvest_object.harvest_source_id
Exception: Harvest object xxx (https://example.harvest.source/xxx.xml) has a GUID yyy already in use by xxx1 (https:/example1.harvest.source/test.xml) in harvest source zzz
                '''
                }
            },
            {
                'logentry': {
                    'message': 'Errors found by ETL were not picked up by spreadsheet: ["Sheet \"(final data) '
                    'senior-staff\" cell E11: The \"Job/Team Function\" can only be \"N/A\" if the \"Post Unique '
                    'Reference\" is \"0\" (individual is paid but not in post).","Sheet \"(final data) senior-staff\" '
                    'cell H11: The \"Unit\" can only be \"N/A\" if the \"Post Unique Reference\" is \"0\" '
                    '(individual is paid but not in post)."]'
                }
            },
            {'logentry': {'message': 'Organogram template XLS file expected but got: : Organogram to upload - org.csv'}},
            {'logentry': {'message': '404 Not Found: User not found'}},
        ]

        for mock_event in mock_events:
            response = DatagovukPlugin().before_send(mock_event, '')
            assert not response
