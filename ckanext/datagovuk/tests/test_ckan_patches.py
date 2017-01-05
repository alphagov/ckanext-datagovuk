"""Tests for DGU monkey patches of CKAN."""
from nose.tools import assert_true, assert_false

from ckan import model
from ckan.tests import factories, helpers


class TestLogin:
    @classmethod
    def setup_class(cls):
        helpers.reset_db()

    def test_validate_password__ok(self):
        user_dict = factories.User(password='hello')
        user = model.User.get(user_dict['id'])

        assert_true(user.validate_password('hello'))

    def test_validate_password__wrong_password(self):
        user_dict = factories.User(password='hello')
        user = model.User.get(user_dict['id'])

        assert_false(user.validate_password('wrong'))

    def test_validate_password__drupal_ok(self):
        # Drupal hash
        # co@prod2 ~ () $ cd /var/www/drupal/dgud7/current; drush php-eval "include_once DRUPAL_ROOT . '/includes/password.inc'; include_once DRUPAL_ROOT . '/includes/bootstrap.inc'; echo user_hash_password('pass');"
        # $S$D2B6/Pd7ZJNIs9XL4X0QjY2mC4nwZz9pIYe8P3TXzuE9c2dLIytw
        user_dict = factories.User()
        drupal_hash = '$S$D2B6/Pd7ZJNIs9XL4X0QjY2mC4nwZz9pIYe8P3TXzuE9c2dLIytw'
        model.Session.execute(
            'update public.user set password = :pw where id = :id',
            {'pw': drupal_hash, 'id': user_dict['id']})
        model.Session.commit()
        model.Session.remove()

        user = model.User.get(user_dict['id'])
        assert_true(user.validate_password('pass'))

