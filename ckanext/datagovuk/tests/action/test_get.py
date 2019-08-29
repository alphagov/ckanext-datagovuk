import unittest

from ckanext.datagovuk.action.get import remove_pii_from_list, remove_pii, PII_LIST


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


class TestRemovePII(unittest.TestCase):
    def test_removes_pii_from_package_search(self):
        res = remove_pii_from_list(sample_package_search_result)
        assert not any(elem in PII_LIST for elem in res)

    def test_removes_pii_from_package_show(self):
        res = remove_pii(sample_package_show_result.copy())
        assert not any(elem in PII_LIST for elem in res)

    def test_removes_pii_works_even_if_pii_element_doesnt_exist(self):
        modified_sample_package_show_result = sample_package_show_result.copy()
        del modified_sample_package_show_result['contact-name']

        res = remove_pii(modified_sample_package_show_result)
        assert not any(elem in PII_LIST for elem in res)
