from nose.tools import assert_true, assert_false, assert_equal, assert_in
from routes import url_for

import ckan.plugins
from ckan import model
from ckan.tests import factories, helpers
from ckanext.harvest.model import setup as db_setup

webtest_submit = helpers.webtest_submit
submit_and_follow = helpers.submit_and_follow

class TestPackageController(helpers.FunctionalTestBase):
    @classmethod
    def setup_class(cls):
        helpers.reset_db()
        db_setup()

    @classmethod
    def setup(cls):
        helpers.reset_db()
        db_setup()

    @classmethod
    def teardown_class(cls):
        return

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

    ## Tests for rendering the forms

    def test_form_renders(self):
        app = self._get_test_app()
        env, response = self._get_package_new_page(app)
        assert_true('dataset-edit' in response.forms)

    def test_resource_form_renders(self):
        app = self._get_test_app()
        env, response = self._get_package_new_page(app)
        form = response.forms['dataset-edit']
        form['name'] = u'resource-form-renders'

        response = submit_and_follow(app, form, env, 'save')
        assert_true('resource-edit' in response.forms)

    def test_previous_button_works(self):
        app = self._get_test_app()
        env, response = self._get_package_new_page(app)
        form = response.forms['dataset-edit']
        form['name'] = u'previous-button-works'

        response = submit_and_follow(app, form, env, 'save')
        form = response.forms['resource-edit']

        response = submit_and_follow(app, form, env, 'save', 'go-dataset')
        assert_true('dataset-edit' in response.forms)

    def test_previous_button_populates_form(self):
        app = self._get_test_app()
        env, response = self._get_package_new_page(app)
        form = response.forms['dataset-edit']
        form['name'] = u'previous-button-populates-form'

        response = submit_and_follow(app, form, env, 'save')
        form = response.forms['resource-edit']

        response = submit_and_follow(app, form, env, 'save', 'go-dataset')
        form = response.forms['dataset-edit']
        assert_true('title' in form.fields)
        assert_equal(form['name'].value, u'previous-button-populates-form')

    ## Test form validation

    def test_name_required(self):
        app = self._get_test_app()
        env, response = self._get_package_new_page(app)
        form = response.forms['dataset-edit']

        response = webtest_submit(form, 'save', status=200, extra_environ=env)
        assert_true('dataset-edit' in response.forms)
        assert_true('Name: Missing value' in response)

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
        assert_equal(u'edited description', result['notes'])

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
        assert_equal(u'edited description', result['notes'])

