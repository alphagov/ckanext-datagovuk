"""Tests for user_auth API"""
from nose.tools import assert_true, assert_false, assert_raises

from ckan import model
from ckan import logic
from ckan.tests import factories, helpers


class TestUserAuth:
    @classmethod
    def setup_class(cls):
        helpers.reset_db()

    def setup(self):
        sysadmin = factories.Sysadmin()
        self.context = {'model': model, 'user': sysadmin['name']}

        user_dict = factories.User(email='hello@localhost')
        self.user = model.User.get(user_dict['id'])
        self.user.password = 'hello'
        self.user.save()

    def test_valid_call(self):
        resp = helpers.call_action(
            'user_auth',
            self.context,
            email=self.user.email,
            password='hello'
        )
        assert resp['email'] == self.user.email, resp

    def test_missing_email(self):
        assert_raises(
            logic.ValidationError,
            helpers.call_action,
            'user_auth',
            self.context,
            name='',
            password='hello'
        )

    def test_missing_password(self):
        assert_raises(
            logic.ValidationError,
            helpers.call_action,
            'user_auth',
            self.context,
            name=self.user.name,
            password=''
        )

    def test_bad_email(self):
        assert_raises(
            logic.ValidationError,
            helpers.call_action,
            'user_auth',
            self.context,
            name='not-correct@localhost',
            password='hello'
        )

    def test_bad_password(self):
        assert_raises(
            logic.ValidationError,
            helpers.call_action,
            'user_auth',
            self.context,
            name=self.user.name,
            password='goodbye'
        )

    def test_bad_username_and_password(self):
        assert_raises(
            logic.ValidationError,
            helpers.call_action,
            'user_auth',
            self.context,
            name='wrong',
            password='password'
        )
