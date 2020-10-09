from copy import deepcopy
import json

from bs4 import BeautifulSoup
import mock
from routes import url_for

import ckan.plugins
from ckan import model
from ckan.lib.search import PackageSearchIndex
from ckan.tests import factories, helpers
from ckanext.datagovuk.tests.db_test import DBTest

webtest_submit = helpers.webtest_submit
submit_and_follow = helpers.submit_and_follow


class TestPackageController(helpers.FunctionalTestBase, DBTest):
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
            url=url_for(controller='package', action='new'),
            extra_environ=env,
        )
        return env, response

    ## Tests for API methods

    def test_package_create_show(self):
        organization = self._create_org()
        dataset_in = factories.Dataset(name='some-dataset', title='A test dataset', owner_org=organization['id'])

        dataset_out = helpers.call_action('package_show', id=dataset_in['id'])

        self.assertEqual(dataset_out['name'], dataset_in['name'])
        self.assertEqual(dataset_out['title'], dataset_in['title'])

    def test_resource_create_show(self):
        organization = self._create_org()
        dataset_in = factories.Dataset(owner_org=organization['id'])
        resource_in = factories.Resource(package_id=dataset_in['id'])

        dataset_out = helpers.call_action('package_show', id=dataset_in['id'])
        resource_out = dataset_out['resources'][0]

        self.assertEqual(resource_out['name'], resource_in['name'])
        self.assertEqual(resource_out['description'], resource_in['description'])
        self.assertEqual(resource_out['format'], resource_in['format'])
        self.assertEqual(resource_out['url'], resource_in['url'])


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
            url_for(controller='package',
                    action='new_resource',
                    id=dataset['name']),
            extra_environ=env,
        )

        page = BeautifulSoup(response.html.decode('utf-8'), 'html.parser')
        form = response.forms['resource-edit']
        assert not 'resource-type' in form.fields
        assert 'url' in form.fields
        assert 'upload' in form.fields
        assert 'name' in form.fields
        assert 'datafile-date' in form.fields
        assert 'format' in form.fields


    ## Test standard dataset file upload
    def test_resource_create_standard_file_upload(self):
        user = factories.User()
        organization = factories.Organization(
            users=[{'name': user['id'], 'capacity': 'admin'}]
        )
        dataset = factories.Dataset(owner_org=organization['id'])

        app = helpers._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url_for(controller='package',
                    action='new_resource',
                    id=dataset['name']),
            extra_environ=env,
        )

        page = BeautifulSoup(response.html.decode('utf-8'), 'html.parser')

        form = response.forms['resource-edit']
        assert 'resource-type' in form.fields
        assert 'url' in form.fields
        assert not 'upload' in form.fields
        assert 'name' in form.fields
        assert 'datafile-date' in form.fields
        assert 'format' in form.fields


    ## Tests for indexing the package

    @mock.patch("pysolr.Solr", autospec=True)
    def test_package_indexing_truncates_unsafe_fields(self, mock_solr):
        app = self._get_test_app()
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

                self.assertEqual(len(mock_solr.return_value.add.mock_calls), 1)
                self.assertEqual(len(mock_solr.return_value.add.mock_calls[0][2]["docs"]), 1)

                actual = mock_solr.return_value.add.mock_calls[0][2]["docs"][0]
                # indexer adds a bunch of keys we don't care about and can't predict
                actual_common = {
                    k: v
                    for k, v in actual.items()
                    if k in expected
                }
                self.assertEqual(
                    expected,
                    actual_common,
                )

                try:
                    # data_dict must still be valid json
                    json.loads(actual["data_dict"])
                except Exception as e:
                    self.fail(e)
            finally:
                index.clear()


    ## Tests for rendering the forms

    def test_form_renders(self):
        app = self._get_test_app()
        env, response = self._get_package_new_page(app)
        self.assertIn('dataset-edit', response.forms)

    def test_resource_form_renders(self):
        app = self._get_test_app()
        env, response = self._get_package_new_page(app)
        form = response.forms['dataset-edit']
        form['name'] = u'resource-form-renders'

        response = submit_and_follow(app, form, env, 'save')
        self.assertIn('resource-edit', response.forms)

    def test_previous_button_works(self):
        app = self._get_test_app()
        env, response = self._get_package_new_page(app)
        form = response.forms['dataset-edit']
        form['name'] = u'previous-button-works'

        response = submit_and_follow(app, form, env, 'save')
        form = response.forms['resource-edit']

        response = submit_and_follow(app, form, env, 'save', 'go-dataset')
        self.assertIn('dataset-edit', response.forms)

    def test_previous_button_populates_form(self):
        app = self._get_test_app()
        env, response = self._get_package_new_page(app)
        form = response.forms['dataset-edit']
        form['name'] = u'previous-button-populates-form'

        response = submit_and_follow(app, form, env, 'save')
        form = response.forms['resource-edit']

        response = submit_and_follow(app, form, env, 'save', 'go-dataset')
        form = response.forms['dataset-edit']
        self.assertIn('title', form.fields)
        self.assertEqual(form['name'].value, u'previous-button-populates-form')

    ## Test form validation

    def test_name_required(self):
        app = self._get_test_app()
        env, response = self._get_package_new_page(app)
        form = response.forms['dataset-edit']

        response = webtest_submit(form, 'save', status=200, extra_environ=env)
        self.assertIn('dataset-edit', response.forms)
        self.assertIn('Name: Missing value', response)

    ## Test user authentication

    def test_user_not_in_organization_cannot_edit(self):
        user = factories.User()
        organization = factories.Organization()
        dataset = factories.Dataset(owner_org=organization['id'])
        app = helpers._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url_for(controller='package',
                    action='edit',
                    id=dataset['name']),
            extra_environ=env,
            status=403,
        )

        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.post(
            url_for(controller='package',
                    action='edit',
                    id=dataset['name']),
            {'notes': 'edited description'},
            extra_environ=env,
            status=403,
        )

    def test_organization_admin_can_edit(self):
        user = factories.User()
        organization = factories.Organization(
            users=[{'name': user['id'], 'capacity': 'admin'}]
        )
        dataset = factories.Dataset(owner_org=organization['id'])
        app = helpers._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url_for(controller='package',
                    action='edit',
                    id=dataset['name']),
            extra_environ=env,
        )
        form = response.forms['dataset-edit']
        form['notes'] = u'edited description'
        submit_and_follow(app, form, env, 'save')

        result = helpers.call_action('package_show', id=dataset['id'])
        self.assertEqual(u'edited description', result['notes'])

    def test_organization_editor_can_edit(self):
        user = factories.User()
        organization = factories.Organization(
            users=[{'name': user['id'], 'capacity': 'editor'}]
        )
        dataset = factories.Dataset(owner_org=organization['id'])
        app = helpers._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url_for(controller='package',
                    action='edit',
                    id=dataset['name']),
            extra_environ=env,
        )
        form = response.forms['dataset-edit']
        form['notes'] = u'edited description'
        submit_and_follow(app, form, env, 'save')

        result = helpers.call_action('package_show', id=dataset['id'])
        self.assertEqual(u'edited description', result['notes'])
