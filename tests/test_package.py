from copy import deepcopy
import json
import pytest
import six
from six.moves.urllib.parse import urlparse

from bs4 import BeautifulSoup
import mock
from ckantoolkit import url_for

import ckan.plugins
from ckan import model
from ckan.lib.search import PackageSearchIndex
from ckan.tests import factories, helpers


@pytest.fixture
def user_env():
    user = factories.User()
    return {"REMOTE_USER": six.ensure_str(user["name"])}


def _get_location(res):
    location = res.headers['location']
    return urlparse(location)._replace(scheme='', netloc='').geturl()


@pytest.mark.usefixtures("clean_db", "with_plugins", "with_request_context")
class TestPackageController:
    @classmethod
    def _create_org(self):
        user = factories.User()
        organization = factories.Organization(
            users=[{'name': user['id'], 'capacity': 'admin'}]
        )
        return organization

    @classmethod
    def _get_package_new_page(self, app):
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='dataset', action='new'),
            extra_environ=env,
        )
        return env, response

    ## Tests for API methods

    def test_package_create_show(self):
        organization = self._create_org()
        dataset_in = factories.Dataset(name='some-dataset', title='A test dataset', owner_org=organization['id'])

        dataset_out = helpers.call_action('package_show', id=dataset_in['id'])

        assert dataset_out['name'] == dataset_in['name']
        assert dataset_out['title'] == dataset_in['title']

    def test_resource_create_show(self):
        organization = self._create_org()
        dataset_in = factories.Dataset(owner_org=organization['id'])
        resource_in = factories.Resource(package_id=dataset_in['id'])

        dataset_out = helpers.call_action('package_show', id=dataset_in['id'])
        resource_out = dataset_out['resources'][0]

        assert resource_out['name'] == resource_in['name']
        assert resource_out['description'] == resource_in['description']
        assert resource_out['format'] == resource_in['format']
        assert resource_out['url'] == resource_in['url']


    ## Test organogram file upload
    @mock.patch("ckan.lib.helpers.uploader.get_storage_path", return_value='./')
    def test_resource_create_organogram_file_upload(self, mock_uploads_enabled):
        '''
        This should fail in 2.8 as the `upload` button isn't showing due to a
        javascript issue. Setting up Jasmine might help us test the forms more
        thoroughly.
        '''
        user = factories.User()
        organization = factories.Organization(
            users=[{'name': user['id'], 'capacity': 'admin'}]
        )
        dataset = factories.Dataset(owner_org=organization['id'])
        dataset['schema-vocabulary'] = '538b857a-64ba-490e-8440-0e32094a28a7'
        helpers.call_action('package_update', **dataset)

        app = helpers._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url_for(
                "{}_resource.new".format(dataset["type"]),
                id=dataset['name']),
            extra_environ=env,
        )

        page = BeautifulSoup(response.get_data(), 'html.parser')
        form = page.find('form', id='resource-edit')
        fields = [f.attrs['name'] for f in form.find_all('input')]
        assert 'resource-type' not in fields
        assert 'url' in fields
        assert 'upload' in fields
        assert 'name' in fields
        assert 'datafile-date' in fields
        assert 'format' in fields

    ## Test standard dataset file upload
    def test_resource_create_standard_file_upload(self, app):
        user = factories.User()
        organization = factories.Organization(
            users=[{'name': user['id'], 'capacity': 'admin'}]
        )
        dataset = factories.Dataset(owner_org=organization['id'])

        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url_for(
                "{}_resource.new".format(dataset["type"]),
                id=dataset['name']),
            extra_environ=env,
        )

        page = BeautifulSoup(response.get_data(as_text=True), 'html.parser')
        form = page.find('form', id='resource-edit')
        fields = [f.attrs['name'] for f in form.find_all('input')]
        assert 'resource-type' in fields
        assert 'url' in fields
        assert not 'upload' in fields
        assert 'name' in fields
        assert 'datafile-date' in fields
        assert 'format' in fields


    ## Tests for indexing the package

    @mock.patch("pysolr.Solr", autospec=True)
    def test_package_indexing_truncates_unsafe_fields(self, mock_solr, app):
        with app.flask_app.test_request_context():
            index = PackageSearchIndex()
            try:
                submitted = {
                    "id": "test-index",
                    "name": "monkey",
                    "title": "Monkey",
                    "state": "active",
                    "private": False,
                    "type": "dataset",
                    "owner_org": None,
                    "metadata_created": "2020-06-06T12:12:12.000000Z",
                    "metadata_modified": "2020-06-06T12:12:12.000000Z",
                    "notes": "something " + ("really " * 20000) + "long",
                    "extras_foo": [
                        "another " + ("really " * 20000) + "long field",
                        {"something": "smaller"},
                    ],
                    "status": {
                        "boo": 1,
                        "bar": 0,
                        "baz": [
                            "short",
                            "short",
                            "l" + ("o" * 30000) + "ng",
                        ],
                    },
                }
                submitted["foo"] = deepcopy(submitted["extras_foo"])

                expected = deepcopy(submitted)
                expected["foo"][0] = expected["foo"][0][:15000]
                expected["status"]["baz"][2] = expected["status"]["baz"][2][:15000]
                # indexer alters these
                expected["metadata_created"] = mock.ANY
                expected["metadata_modified"] = mock.ANY

                index.index_package(submitted)

                assert len(mock_solr.return_value.add.mock_calls) == 1
                assert len(mock_solr.return_value.add.mock_calls[0][2]["docs"]) == 1

                actual = mock_solr.return_value.add.mock_calls[0][2]["docs"][0]
                # indexer adds a bunch of keys we don't care about and can't predict
                actual_common = {
                    k: v
                    for k, v in actual.items()
                    if k in expected
                }
                assert expected == actual_common

                try:
                    # data_dict must still be valid json
                    json.loads(actual["data_dict"])
                except Exception as e:
                    self.fail(e)
            finally:
                index.clear()


    ## Tests for rendering the forms

    def test_form_renders(self, app):
        self._create_org()
        env, response = self._get_package_new_page(app)
        assert 'dataset-edit' in response.get_data(as_text=True)

    @pytest.mark.skip("Originally copied from CKAN but since removed from 2.9")
    def test_resource_form_renders(self, app):
        self._create_org()
        env, form = self._get_package_new_page(app)
        form = response.forms['dataset-edit']
        form['name'] = u'resource-form-renders'

        response = submit_and_follow(app, form, env, 'save')
        assert 'resource-edit' in response.forms

    def test_previous_button_works(self, app, user_env):
        url = url_for("dataset.new")
        response = app.post(url, environ_overrides=user_env, data={
            "name": "previous-button-works",
            "save": "",
            "_ckan_phase": 1
        }, follow_redirects=False)

        location = _get_location(response)
        response = app.post(location, environ_overrides=user_env, data={
            "id": "",
            "save": "go-dataset"
        }, follow_redirects=False)

        assert '/dataset/edit/' in response.headers['location']

    def test_previous_button_populates_form(self, app, user_env):
        url = url_for("dataset.new")
        response = app.post(url, environ_overrides=user_env,
            data={
                "name": "previous-button-populates-form",
                "save": "",
                "_ckan_phase": 1
            },
            follow_redirects=False)

        location = _get_location(response)
        response = app.post(location, environ_overrides=user_env, data={
            "id": "",
            "save": "go-dataset"
        })

        assert 'name="title"' in response
        assert 'value="previous-button-populates-form"'

    ## Test form validation

    @pytest.mark.usefixtures("with_request_context")
    def test_name_required(self, app, user_env):
        response = app.post(
            url=url_for("dataset.new"), extra_environ=user_env, data={"save": ""}
        )
        assert "Name: Missing value" in response.get_data(as_text=True)

    ## Test user authentication

    def test_user_not_in_organization_cannot_edit(self, app):
        user = factories.User()
        organization = factories.Organization()
        dataset = factories.Dataset(owner_org=organization["id"])
        env = {"REMOTE_USER": six.ensure_str(user["name"])}
        response = app.get(
            url_for("dataset.edit", id=dataset["name"]),
            extra_environ=env,
            status=403,
        )

        env = {"REMOTE_USER": six.ensure_str(user["name"])}
        response = app.post(
            url_for("dataset.edit", id=dataset["name"]),
            data={"notes": "edited description"},
            extra_environ=env,
            status=403,
        )

    def test_organization_admin_can_edit(self, app):
        user = factories.User()
        organization = factories.Organization(
            users=[{"name": user["id"], "capacity": "admin"}]
        )
        dataset = factories.Dataset(owner_org=organization["id"])
        env = {"REMOTE_USER": six.ensure_str(user["name"])}
        response = app.post(
            url_for("dataset.edit", id=dataset["name"]), extra_environ=env,
            data={
                "notes": u"edited description",
                "save": ""
            }, follow_redirects=False
        )
        result = helpers.call_action("package_show", id=dataset["id"])
        assert u"edited description" == result["notes"]

    def test_organization_editor_can_edit(self, app):
        user = factories.User()
        organization = factories.Organization(
            users=[{"name": user["id"], "capacity": "editor"}]
        )
        dataset = factories.Dataset(owner_org=organization["id"])
        env = {"REMOTE_USER": six.ensure_str(user["name"])}
        response = app.post(
            url_for("dataset.edit", id=dataset["name"]), extra_environ=env,
            data={
                "notes": u"edited description",
                "save": ""
            }, follow_redirects=False

        )
        result = helpers.call_action("package_show", id=dataset["id"])
        assert u"edited description" == result["notes"]
