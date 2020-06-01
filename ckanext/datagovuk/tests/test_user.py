from six.moves.urllib.parse import urljoin

import ckan.plugins
from ckan import model
from ckan.common import config
from ckan.tests import factories, helpers
from ckan.plugins.toolkit import url_for
from ckanext.datagovuk.tests.db_test import DBTest

webtest_submit = helpers.webtest_submit
submit_and_follow = helpers.submit_and_follow


class TestEditUser(helpers.FunctionalTestBase, DBTest):
    def test_edit_user_form(self):
        user = factories.User(password='pass1234')
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for("user.edit"),
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
        form['old_password'] = 'pass1234'
        form['password1'] = 'Abc12345'
        form['password2'] = 'Abc12345'
        response = submit_and_follow(app, form, env, 'save')

        user = model.Session.query(model.User).get(user['id'])
        self.assertEqual(user.fullname, 'user fullname')
        self.assertEqual(user.email, 'test@test.com')

    def test_edit_user_form_password_too_short(self):
        user = factories.User(password='pass1234')
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for("user.edit"),
            extra_environ=env,
        )

        form = response.forms['user-edit-form']

        # Modify the values
        form['old_password'] = 'pass1234'
        form['password1'] = 'Abc1234'
        form['password2'] = 'Abc1234'
        response = webtest_submit(form, 'save', status=200, extra_environ=env)

        self.assertIn('Your password must be 8 characters or longer', response)

    def test_edit_user_form_password_no_lower_case(self):
        user = factories.User(password='pass1234')
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for("user.edit"),
            extra_environ=env,
        )

        form = response.forms['user-edit-form']

        # Modify the values
        form['old_password'] = 'pass1234'
        form['password1'] = 'ABC12345'
        form['password2'] = 'ABC12345'
        response = webtest_submit(form, 'save', status=200, extra_environ=env)

        self.assertIn('Your password must contain at least one upper and one lower case character', response)

    def test_edit_user_form_password_no_upper_case(self):
        user = factories.User(password='pass1234')
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for("user.edit"),
            extra_environ=env,
        )

        form = response.forms['user-edit-form']

        # Modify the values
        form['old_password'] = 'pass1234'
        form['password1'] = 'abc12345'
        form['password2'] = 'abc12345'
        response = webtest_submit(form, 'save', status=200, extra_environ=env)

        self.assertIn('Your password must contain at least one upper and one lower case character', response)

    def test_edit_user_form_passwords_not_matching(self):
        user = factories.User(password='pass1234')
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for("user.edit"),
            extra_environ=env,
        )

        form = response.forms['user-edit-form']

        # Modify the values
        form['old_password'] = 'pass1234'
        form['password1'] = 'Abc123456'
        form['password2'] = 'Abc12345'
        response = webtest_submit(form, 'save', status=200, extra_environ=env)

        self.assertIn('The passwords you entered do not match', response)

    def test_edit_user_form_password_missing(self):
        user = factories.User(password='pass1234')
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for("user.edit"),
            extra_environ=env,
        )

        form = response.forms['user-edit-form']

        # Modify the values
        form['old_password'] = 'pass1234'
        form['password1'] = ''
        form['password2'] = ''
        response = webtest_submit(form, 'save', status=200, extra_environ=env)

        self.assertIn('Please enter both passwords', response)


class TestUserMe(helpers.FunctionalTestBase, DBTest):
    def test_user_me_logged_in(self):
        user = factories.User()
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for("user.me"),
            extra_environ=env,
            status=302,
        )

        self.assertEqual(
            response.location,
            urljoin(config.get('ckan.site_url'), url_for("dashboard.datasets")),
        )

    def test_user_me_not_logged_in(self):
        app = self._get_test_app()
        response = app.get(
            url=url_for("user.me"),
            status=302,
        )

        self.assertEqual(
            response.location,
            urljoin(config.get('ckan.site_url'), url_for("user.login")),
        )

    def test_use_from_logged_in(self):
        user = factories.User()
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for("user.logged_in"),
            extra_environ=env,
            status=302,
        )

        self.assertEqual(
            response.location,
            urljoin(config.get('ckan.site_url'), url_for("dashboard.datasets")),
        )


class TestRegisterUser(helpers.FunctionalTestBase, DBTest):
    def test_register_a_user_blocked(self):
        app = helpers._get_test_app()
        response = app.post(
            url_for("user.register"),
            params={
                "name": 'newuser',
                'fullname': 'New User',
                'email': 'test@gov.uk',
                'password1': 'TestPassword1',
                'password2': 'TestPassword1',
                "save": "1",
            },
            status=403,
        )
        self.assertFalse(model.User.by_email("test@gov.uk"))

    def test_get_still_works(self):
        app = helpers._get_test_app()
        response = app.get(
            url_for("user.register"),
            status=200,
        )
        self.assertIn("contact us", response.body.lower())
