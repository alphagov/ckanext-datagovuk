from bs4 import BeautifulSoup
import pytest
import unittest

import mock

from six.moves.urllib.parse import urljoin

import ckan.plugins
from ckan import model
from ckan.common import config
from ckan.tests import factories, helpers
from ckan.plugins.toolkit import url_for
from ckan.lib.mailer import MailerException, create_reset_key


@pytest.mark.usefixtures("clean_db", "with_plugins")
class TestEditUser:
    def test_edit_user_form(self, app):
        user = factories.User(password='pass1234')
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for("user.edit"),
            extra_environ=env,
        )

        page = BeautifulSoup(response.get_data(as_text=True), 'html.parser')
        form = {e['name']: e.get('value', '') for e in page.find_all('input')}

        # Check the existing values
        assert form['name'] == user['name']
        assert form['fullname'] == user['fullname']
        assert form['email'] == user['email']
        assert form['password1'] == ''
        assert form['password2'] == ''

        response = app.post(
            url=url_for("user.edit"),
            extra_environ=env,
            data={
                "name": user['name'],
                "fullname": "user fullname",
                "email": "test@test.com",
                "save": "",
                "old_password": "pass1234",
                "password1": "Abc12345",
                "password2": "Abc12345"
            }
        )
        user = model.Session.query(model.User).get(user['id'])
        assert user.fullname == 'user fullname'
        assert user.email == 'test@test.com'

    def test_create_user_via_post_responds_403(self, app):
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
        assert not model.User.by_email("test@gov.uk")

    def test_create_user_via_get_shows_dgu_register_page(self, app):
        response = app.get(
            url=url_for(controller='user', action='register'),
            status=200
        )
        assert 'https://data.gov.uk/support' in response

    def test_edit_user_form_password_too_short(self, app):
        user = factories.User(password='pass1234')
        env = {'REMOTE_USER': user['name'].encode('ascii')}

        response = app.post(
            url=url_for("user.edit"),
            extra_environ=env,
            data={
                "name": user['name'],
                "fullname": user['fullname'],
                "email": user['email'],
                "save": "",
                "old_password": "pass1234",
                "password1": "Abc1234",
                "password2": "Abc1234"
            }
        )
        assert 'Your password must be 8 characters or longer' in response.get_data(as_text=True)

    def test_edit_user_form_password_no_lower_case(self, app):
        user = factories.User(password='pass1234')
        env = {'REMOTE_USER': user['name'].encode('ascii')}

        response = app.post(
            url=url_for("user.edit"),
            extra_environ=env,
            data={
                "name": user['name'],
                "email": user['email'],
                "save": "",
                "old_password": "pass1234",
                "password1": "ABC12345",
                "password2": "ABC12345"
            }
        )

        assert 'Your password must contain at least one upper and one lower case character' in response.get_data(as_text=True)

    def test_edit_user_form_password_no_upper_case(self, app):
        user = factories.User(password='pass1234')
        env = {'REMOTE_USER': user['name'].encode('ascii')}

        response = app.post(
            url=url_for("user.edit"),
            extra_environ=env,
            data={
                "name": user['name'],
                "email": user['email'],
                "save": "",
                "old_password": "pass1234",
                "password1": "abc12345",
                "password2": "abc12345"
            }
        )

        assert 'Your password must contain at least one upper and one lower case character' in response.get_data(as_text=True)

    def test_edit_user_form_passwords_not_matching(self, app):
        user = factories.User(password='pass1234')
        env = {'REMOTE_USER': user['name'].encode('ascii')}

        response = app.post(
            url=url_for("user.edit"),
            extra_environ=env,
            data={
                "name": user['name'],
                "email": user['email'],
                "save": "",
                "old_password": "pass1234",
                "password1": "Abc123456",
                "password2": "Abc12345"
            }
        )

        assert 'The passwords you entered do not match' in response.get_data(as_text=True)

    def test_edit_user_form_password_missing(self, app):
        user = factories.User(password='pass1234')
        env = {'REMOTE_USER': user['name'].encode('ascii')}

        response = app.post(
            url=url_for("user.edit"),
            extra_environ=env,
            data={
                "name": user['name'],
                "email": user['email'],
                "save": "",
                "old_password": "pass1234",
                "password1": "",
                "password2": ""
            }
        )
        assert 'Please enter both passwords' in response.get_data(as_text=True)


@pytest.mark.usefixtures("clean_db")
class TestUserMe:
    def test_user_me_logged_in(self, app):
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for("user.me"),
            follow_redirects=False,
            extra_environ=env,
            status=302,
        )

        assert response.location == urljoin(config.get('ckan.site_url'), url_for("dashboard.datasets"))

    def test_user_me_not_logged_in(self, app):
        response = app.get(
            url=url_for("user.me"),
            follow_redirects=False,
            status=302,
        )

        assert response.location == urljoin(config.get('ckan.site_url'), url_for("user.login"))

    def test_use_from_logged_in(self, app):
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for("user.logged_in"),
            follow_redirects=False,
            extra_environ=env,
            status=302,
        )

        assert response.location == urljoin(config.get('ckan.site_url'), url_for("dashboard.datasets"))


class TestRegisterUser:
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
        assert not model.User.by_email("test@gov.uk")

    def test_get_still_works(self):
        app = helpers._get_test_app()
        response = app.get(
            url_for("user.register"),
            status=200,
        )
        assert "contact us" in response.body.lower()
