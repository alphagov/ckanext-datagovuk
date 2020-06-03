from routes import url_for

import ckan.plugins
from ckan import model
from ckan.tests import factories, helpers
from ckanext.datagovuk.controllers.user import UserController
from ckanext.datagovuk.tests.db_test import DBTest

webtest_submit = helpers.webtest_submit
submit_and_follow = helpers.submit_and_follow


class TestUserController(helpers.FunctionalTestBase, DBTest):
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
        self.assertEqual(form['name'].value, user['name'])
        self.assertEqual(form['fullname'].value, user['fullname'])
        self.assertEqual(form['email'].value, user['email'])
        self.assertEqual(form['password1'].value, '')
        self.assertEqual(form['password2'].value, '')

        # Modify the values
        form['fullname'] = 'user fullname'
        form['email'] = 'test@test.com'
        form['old_password'] = 'pass'
        form['password1'] = 'Abc12345'
        form['password2'] = 'Abc12345'
        response = submit_and_follow(app, form, env, 'save')

        user = model.Session.query(model.User).get(user['id'])
        self.assertEqual(user.fullname, 'user fullname')
        self.assertEqual(user.email, 'test@test.com')

    def test_create_user_via_post_responds_403(self):
        app = self._get_test_app()
        app.post(
            url=url_for(controller='user', action='register'),
            params={
                "name": 'newuser',
                'fullname': 'New User',
                'email': 'test@gov.uk',
                'password1': 'TestPassword1',
                'password2': 'TestPassword1',
                "save": "1",
            },
            status=403
        )
        self.assertFalse(model.User.by_email("test@gov.uk"))

    def test_create_user_via_get_shows_dgu_register_page(self):
        app = self._get_test_app()
        response = app.get(
            url=url_for(controller='user', action='register'),
            status=200
        )
        assert 'https://data.gov.uk/support' in response

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

        self.assertIn('Your password must be 8 characters or longer', response)

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

        self.assertIn('Your password must contain at least one upper and one lower case character', response)

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

        self.assertIn('Your password must contain at least one upper and one lower case character', response)

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

        self.assertIn('The passwords you entered do not match', response)

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

        self.assertIn('Please enter both passwords', response)
