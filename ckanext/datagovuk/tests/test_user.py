from nose.tools import assert_true, assert_false, assert_equal, assert_in
from routes import url_for

import ckan.plugins
from ckan import model
from ckan.tests import factories, helpers
from ckanext.datagovuk.controllers.user import UserController

webtest_submit = helpers.webtest_submit
submit_and_follow = helpers.submit_and_follow

class TestUserController(helpers.FunctionalTestBase):
    @classmethod
    def setup_class(cls):
        return

    @classmethod
    def teardown_class(cls):
        return

    def test_edit_user_form(self):
        user = factories.User(password='pass')
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='user', action='edit'),
            extra_environ=env,
        )

        form = response.forms['user-edit-form']

        # Check the existing values
        assert_equal(form['name'].value, user['name'])
        assert_equal(form['fullname'].value, user['fullname'])
        assert_equal(form['email'].value, user['email'])
        assert_equal(form['password1'].value, '')
        assert_equal(form['password2'].value, '')

        # Modify the values
        form['fullname'] = 'user fullname'
        form['email'] = 'test@test.com'
        form['old_password'] = 'pass'
        form['password1'] = 'Abc12345'
        form['password2'] = 'Abc12345'
        response = submit_and_follow(app, form, env, 'save')

        user = model.Session.query(model.User).get(user['id'])
        assert_equal(user.fullname, 'user fullname')
        assert_equal(user.email, 'test@test.com')

    def test_edit_user_form_password_too_short(self):
        user = factories.User(password='pass')
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='user', action='edit'),
            extra_environ=env,
        )

        form = response.forms['user-edit-form']

        # Modify the values
        form['old_password'] = 'pass'
        form['password1'] = 'Abc1234'
        form['password2'] = 'Abc1234'
        response = webtest_submit(form, 'save', status=200, extra_environ=env)

        assert_true('Your password must be 8 characters or longer' in response)

    def test_edit_user_form_password_no_lower_case(self):
        user = factories.User(password='pass')
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='user', action='edit'),
            extra_environ=env,
        )

        form = response.forms['user-edit-form']

        # Modify the values
        form['old_password'] = 'pass'
        form['password1'] = 'ABC12345'
        form['password2'] = 'ABC12345'
        response = webtest_submit(form, 'save', status=200, extra_environ=env)

        assert_true('Your password must contain at least one upper and one lower case character' in response)

    def test_edit_user_form_password_no_upper_case(self):
        user = factories.User(password='pass')
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='user', action='edit'),
            extra_environ=env,
        )

        form = response.forms['user-edit-form']

        # Modify the values
        form['old_password'] = 'pass'
        form['password1'] = 'abc12345'
        form['password2'] = 'abc12345'
        response = webtest_submit(form, 'save', status=200, extra_environ=env)

        assert_true('Your password must contain at least one upper and one lower case character' in response)

    def test_edit_user_form_passwords_not_matching(self):
        user = factories.User(password='pass')
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='user', action='edit'),
            extra_environ=env,
        )

        form = response.forms['user-edit-form']

        # Modify the values
        form['old_password'] = 'pass'
        form['password1'] = 'Abc123456'
        form['password2'] = 'Abc12345'
        response = webtest_submit(form, 'save', status=200, extra_environ=env)

        assert_true('The passwords you entered do not match' in response)

    def test_edit_user_form_password_missing(self):
        user = factories.User(password='pass')
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='user', action='edit'),
            extra_environ=env,
        )

        form = response.forms['user-edit-form']

        # Modify the values
        form['old_password'] = 'pass'
        form['password1'] = ''
        form['password2'] = ''
        response = webtest_submit(form, 'save', status=200, extra_environ=env)

        assert_true('Please enter both passwords' in response)

