import json
import unittest

from ckanext.datagovuk.pii_helpers import (
    remove_pii_from_api_search_dataset, remove_pii_from_list, remove_pii,
    PII_LIST
)


sample_package_search_result = {
    "count": 1,
    "sort": "score desc, metadata_modified desc",
    "facets": {},
    "results": [
        {
            "license_title": "Creative Commons Attribution",
            "maintainer": None,
            "contact-phone": "",
            "relationships_as_object": [],
            "private": False,
            "maintainer_email": None,
            "num_tags": 0,
            "organization": {
                "description": "",
                "created": "2019-08-28T12:00:00",
                "title": "test",
                "name": "test",
                "is_organization": True,
                "state": "active",
                "image_url": "",
                "revision_id": "revision_id",
                "type": "organization",
                "id": "org_id",
                "approval_status": "approved"
            },
            "foi-email": "test-foi@example.com",
            "id": "data_id",
            "metadata_created": "2019-08-28T11:00:00",
            "licence-custom": "",
            "metadata_modified": "2019-08-28T11:00:00",
            "author": None,
            "author_email": None,
            "state": "active",
            "version": None,
            "license_id": "cc-by",
            "foi-web": "",
            "resources": [
                {
                    "mimetype": None,
                    "cache_url": None,
                    "hash": "",
                    "description": "",
                    "name": "Example dataset",
                    "format": "",
                    "url": "https://example.com/datasets/dataset_id",
                    "datafile-date": "",
                    "cache_last_updated": None,
                    "resource-type": "data-link",
                    "package_id": "dataset_id",
                    "created": "2019-08-28T12:00:00",
                    "state": "active",
                    "mimetype_inner": None,
                    "last_modified": None,
                    "position": 0,
                    "revision_id": "revision_id",
                    "url_type": None,
                    "id": "resource_id",
                    "resource_type": None,
                    "size": None
                }
            ],
            "num_resources": 1,
            "contact-email": "test@example.com",
            "tags": [],
            "foi-name": "",
            "groups": [],
            "creator_user_id": "user_id",
            "relationships_as_subject": [],
            "codelist": "",
            "contact-name": "Test User",
            "name": "test",
            "isopen": True,
            "schema-vocabulary": "",
            "url": None,
            "type": "dataset",
            "notes": "",
            "owner_org": "org_id",
            "license_url": "http://www.opendefinition.org/licenses/cc-by",
            "title": "test",
            "revision_id": "revision_id",
            "foi-phone": "",
            "theme-primary": ""
        }
    ],
    "search_facets": {}
}

sample_package_show_result = {
    "license_title": "Creative Commons Attribution",
    "maintainer": None,
    "contact-phone": "",
    "relationships_as_object": [],
    "private": False,
    "maintainer_email": None,
    "num_tags": 0,
    "organization": {
        "description": "",
        "created": "2019-08-28T12:00:00",
        "title": "test",
        "name": "test",
        "is_organization": True,
        "state": "active",
        "image_url": "",
        "revision_id": "revision_id",
        "type": "organization",
        "id": "org_id",
        "approval_status": "approved"
    },
    "foi-email": "test-foi@example.com",
    "id": "id",
    "metadata_created": "2019-08-28T11:00:00",
    "licence-custom": "",
    "metadata_modified": "2019-08-28T11:00:00",
    "author": None,
    "author_email": None,
    "state": "active",
    "version": None,
    "license_id": "cc-by",
    "foi-web": "",
    "resources": [
        {
            "mimetype": None,
            "cache_url": None,
            "hash": "",
            "description": "",
            "name": "Example",
            "format": "",
            "url": "https://example.com/datasets/dataset_id",
            "datafile-date": "",
            "cache_last_updated": None,
            "resource-type": "data-link",
            "package_id": "dataset_id",
            "created": "2019-08-28T11:00:00",
            "state": "active",
            "mimetype_inner": None,
            "last_modified": None,
            "position": 0,
            "revision_id": "revision_id",
            "url_type": None,
            "id": "resource_id",
            "resource_type": None,
            "size": None
        }
    ],
    "num_resources": 1,
    "contact-email": "test@example.com",
    "tags": [],
    "foi-name": "",
    "groups": [],
    "creator_user_id": "user_id",
    "relationships_as_subject": [],
    "codelist": "",
    "contact-name": "Test User",
    "name": "test",
    "isopen": True,
    "schema-vocabulary": "",
    "url": None,
    "type": "dataset",
    "notes": "",
    "owner_org": "owner_id",
    "license_url": "http://www.opendefinition.org/licenses/cc-by",
    "title": "test",
    "revision_id": "revision_id",
    "foi-phone": "",
    "theme-primary": ""
}

sample_api_search_dataset = '''
{
    "count": 1,
    "results": [
        {
            "data_dict": "{\\"license_title\\": \\"Creative Commons Attribution\\", \\"maintainer\\": null, \\"relationships_as_object\\": [], \\"private\\": false, \\"maintainer_email\\": null, \\"num_tags\\": 0, \\"id\\": \\"dataset_id\\", \\"metadata_created\\": \\"2019-08-28T11:00:00\\", \\"metadata_modified\\": \\"2019-08-28T11:00:00\\", \\"author\\": null, \\"author_email\\": null, \\"state\\": \\"active\\", \\"version\\": null, \\"creator_user_id\\": \\"user_id\\", \\"type\\": \\"dataset\\", \\"resources\\": [{\\"hash\\": \\"\\", \\"description\\": \\"\\", \\"format\\": \\"\\", \\"resource-type\\": \\"data-link\\", \\"package_id\\": \\"dataset_id\\", \\"mimetype_inner\\": null, \\"url_type\\": null, \\"id\\": \\"id\\", \\"size\\": null, \\"mimetype\\": null, \\"cache_url\\": null, \\"name\\": \\"Example dataset\\", \\"created\\": \\"2019-08-28T11:00:00\\", \\"url\\": \\"https: //example.com/datasets/dataset_id\\", \\"datafile-date\\": \\"\\", \\"cache_last_updated\\": null, \\"state\\": \\"active\\", \\"last_modified\\": null, \\"position\\": 0, \\"revision_id\\": \\"revision_id\\", \\"resource_type\\": null}], \\"num_resources\\": 1, \\"tags\\": [], \\"groups\\": [], \\"license_id\\": \\"cc-by\\", \\"relationships_as_subject\\": [], \\"organization\\": {\\"description\\": \\"\\", \\"title\\": \\"test\\", \\"created\\": \\"2019-08-28T12:00:00\\", \\"approval_status\\": \\"approved\\", \\"is_organization\\": true, \\"state\\": \\"active\\", \\"image_url\\": \\"\\", \\"revision_id\\": \\"revision_id\\", \\"type\\": \\"organization\\", \\"id\\": \\"org_id\\", \\"name\\": \\"test\\"}, \\"name\\": \\"test\\", \\"isopen\\": true, \\"url\\": null, \\"notes\\": \\"\\", \\"owner_org\\": \\"org_id\\", \\"extras\\": [{\\"state\\": \\"active\\", \\"value\\": \\"\\", \\"package_id\\": \\"dataset_id\\", \\"key\\": \\"codelist\\", \\"revision_id\\": \\"revision_id\\", \\"id\\": \\"id\\"}, {\\"state\\": \\"active\\", \\"value\\": \\"test@example.com\\", \\"package_id\\": \\"dataset_id\\", \\"key\\": \\"contact-email\\", \\"revision_id\\": \\"revision_id\\", \\"id\\": \\"id\\"}, {\\"state\\": \\"active\\", \\"value\\": \\"Test User\\", \\"package_id\\": \\"dataset_id\\", \\"key\\": \\"contact-name\\", \\"revision_id\\": \\"revision_id\\", \\"id\\": \\"id\\"}, {\\"state\\": \\"active\\", \\"value\\": \\"\\", \\"package_id\\": \\"dataset_id\\", \\"key\\": \\"contact-phone\\", \\"revision_id\\": \\"revision_id\\", \\"id\\": \\"id\\"}, {\\"state\\": \\"active\\", \\"value\\": \\"test-foi@example.com\\", \\"package_id\\": \\"dataset_id\\", \\"key\\": \\"foi-email\\", \\"revision_id\\": \\"revision_id\\", \\"id\\": \\"id\\"}, {\\"state\\": \\"active\\", \\"value\\": \\"\\", \\"package_id\\": \\"dataset_id\\", \\"key\\": \\"foi-name\\", \\"revision_id\\": \\"revision_id\\", \\"id\\": \\"id\\"}, {\\"state\\": \\"active\\", \\"value\\": \\"\\", \\"package_id\\": \\"dataset_id\\", \\"key\\": \\"foi-phone\\", \\"revision_id\\": \\"revision_id\\", \\"id\\": \\"id\\"}, {\\"state\\": \\"active\\", \\"value\\": \\"\\", \\"package_id\\": \\"dataset_id\\", \\"key\\": \\"foi-web\\", \\"revision_id\\": \\"revision_id\\", \\"id\\": \\"id\\"}, {\\"state\\": \\"active\\", \\"value\\": \\"\\", \\"package_id\\": \\"dataset_id\\", \\"key\\": \\"licence-custom\\", \\"revision_id\\": \\"revision_id\\", \\"id\\": \\"id\\"}, {\\"state\\": \\"active\\", \\"value\\": \\"\\", \\"package_id\\": \\"dataset_id\\", \\"key\\": \\"schema-vocabulary\\", \\"revision_id\\": \\"revision_id\\", \\"id\\": \\"id\\"}, {\\"state\\": \\"active\\", \\"value\\": \\"\\", \\"package_id\\": \\"dataset_id\\", \\"key\\": \\"theme-primary\\", \\"revision_id\\": \\"revision_id\\", \\"id\\": \\"id\\"}], \\"license_url\\": \\"http://www.opendefinition.org/licenses/cc-by\\", \\"title\\": \\"test\\", \\"revision_id\\": \\"revision_id\\"}",
            "site_id": "dgu",
            "res_name": [
                "Example dataset"
            ],
            "id": "dataset_id",
            "metadata_created": "2019-08-28T11:00:00Z",
            "capacity": "public",
            "metadata_modified": "2019-08-28T11:00:00Z",
            "entity_type": "package",
            "author": null,
            "author_email": null,
            "state": "active",
            "license_id": "cc-by",
            "indexed_ts": "2019-08-28T11:00:00Z",
            "dataset_type": "dataset",
            "validated_data_dict": "{\\"owner_org\\": \\"org_id\\", \\"maintainer\\": null, \\"groups\\": [], \\"relationships_as_object\\": [], \\"private\\": false, \\"maintainer_email\\": null, \\"num_tags\\": 0, \\"foi-email\\": \\"test-foi@example.com\\", \\"id\\": \\"dataset_id\\", \\"metadata_created\\": \\"2019-08-28T11:00:00\\", \\"licence-custom\\": \\"\\", \\"metadata_modified\\": \\"2019-08-28T11:00:00\\", \\"author\\": null, \\"author_email\\": null, \\"state\\": \\"active\\", \\"version\\": null, \\"license_id\\": \\"cc-by\\", \\"foi-web\\": \\"\\", \\"resources\\": [{\\"cache_last_updated\\": null, \\"cache_url\\": null, \\"mimetype_inner\\": null, \\"hash\\": \\"\\", \\"description\\": \\"\\", \\"format\\": \\"\\", \\"url\\": \\"https: //example.com/datasets/dataset_id\\", \\"datafile-date\\": \\"\\", \\"created\\": \\"2019-08-28T11:00:00\\", \\"resource-type\\": \\"data-link\\", \\"state\\": \\"active\\", \\"package_id\\": \\"dataset_id\\", \\"last_modified\\": null, \\"mimetype\\": null, \\"url_type\\": null, \\"position\\": 0, \\"revision_id\\": \\"revision_id\\", \\"size\\": null, \\"id\\": \\"id\\", \\"resource_type\\": null, \\"name\\": \\"Example dataset\\"}], \\"num_resources\\": 1, \\"contact-email\\": \\"test@example.com\\", \\"tags\\": [], \\"title\\": \\"test\\", \\"foi-name\\": \\"\\", \\"contact-phone\\": \\"\\", \\"creator_user_id\\": \\"user_id\\", \\"relationships_as_subject\\": [], \\"codelist\\": \\"\\", \\"contact-name\\": \\"Test User\\", \\"name\\": \\"test\\", \\"isopen\\": true, \\"schema-vocabulary\\": \\"\\", \\"url\\": null, \\"type\\": \\"dataset\\", \\"notes\\": \\"\\", \\"license_title\\": \\"Creative Commons Attribution\\", \\"license_url\\": \\"http://www.opendefinition.org/licenses/cc-by\\", \\"organization\\": {\\"description\\": \\"\\", \\"title\\": \\"test\\", \\"created\\": \\"2019-08-28T12:00:00\\", \\"approval_status\\": \\"approved\\", \\"is_organization\\": true, \\"state\\": \\"active\\", \\"image_url\\": \\"\\", \\"revision_id\\": \\"revision_id\\", \\"type\\": \\"organization\\", \\"id\\": \\"org_id\\", \\"name\\": \\"test\\"}, \\"revision_id\\": \\"revision_id\\", \\"foi-phone\\": \\"\\", \\"theme-primary\\": \\"\\"}", 
            "res_url": [
                "https://example.com/datasets/dataset_id"
            ],
            "name": "test",
            "title": "test",
            "extras": {
                "foi-email": "test-foi@example.com",
                "contact-name": "Test User",
                "contact-email": "test@example.com"
            },
            "organization": "test",
            "revision_id": "revision_id",
            "index_id": "index_id"
        }
    ]
}'''

sample_api_search_dataset_without_fields = '''
{
    "count": 1,
    "results": [
        {
            "site_id": "dgu",
            "res_name": [
                "Example dataset"
            ],
            "id": "dataset_id",
            "metadata_created": "2019-08-28T11:00:00Z",
            "capacity": "public",
            "metadata_modified": "2019-08-28T11:00:00Z",
            "entity_type": "package",
            "state": "active",
            "license_id": "cc-by",
            "indexed_ts": "2019-08-28T11:00:00Z",
            "dataset_type": "dataset",
            "res_url": [
                "https://example.com/datasets/dataset_id"
            ],
            "name": "test",
            "title": "test",
            "organization": "test",
            "revision_id": "revision_id",
            "index_id": "index_id"
        }
    ]
}'''

sample_api_search_dataset_strings = '''
{
    "count": 2,
    "results": [
        "test-1",
        "test-2"
    ]
}'''


class TestRemovePII(unittest.TestCase):
    def test_removes_pii_from_package_search(self):
        res = remove_pii_from_list(sample_package_search_result)
        assert not any(elem in PII_LIST for elem in res)

    def test_removes_pii_from_package_show(self):
        res = remove_pii(sample_package_show_result.copy())
        assert not any(elem in PII_LIST for elem in res)

    def test_removes_pii_from_api_search_dataset(self):
        res = remove_pii_from_api_search_dataset(sample_api_search_dataset)
        json_res = json.loads(res)['results'][0]
        assert not any(elem in PII_LIST for elem in json_res)

        json_data_dict = json.loads(json_res['data_dict'])
        assert not any(elem in PII_LIST for elem in json_data_dict)

        json_validated_data_dict = json.loads(json_res['validated_data_dict'])
        assert not any(elem in PII_LIST for elem in json_validated_data_dict)

    def test_does_not_error_with_strings_in_response(self):
        remove_pii_from_api_search_dataset(sample_api_search_dataset_strings)

    def test_removes_pii_from_api_search_dataset_without_fields_and_does_not_add_fields(self):
        res = remove_pii_from_api_search_dataset(sample_api_search_dataset_without_fields)
        json_res = json.loads(res)['results'][0]
        assert not any(elem in PII_LIST for elem in json_res)
        assert not any(elem in ['data_dict', 'validated_data_dict', 'extras'] for elem in json_res.keys())

    def test_removes_pii_works_even_if_pii_element_doesnt_exist(self):
        modified_sample_package_show_result = sample_package_show_result.copy()
        del modified_sample_package_show_result['author']

        res = remove_pii(modified_sample_package_show_result)
        assert not any(elem in PII_LIST for elem in res)
