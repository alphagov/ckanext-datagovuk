"""Tests for DGU monkey patches of CKAN."""
from mock import patch

from ckan import model
import ckan.lib.cli
from ckan.tests.lib.test_cli import paster
from ckan.tests import factories, helpers
from ckanext.datagovuk.tests.db_test import DBTest


class TestLogin(DBTest):
    def test_validate_password__ok(self):
        user_dict = factories.User(password='helloworld')
        user = model.User.get(user_dict['id'])

        self.assertTrue(user.validate_password('helloworld'))

    def test_validate_password__wrong_password(self):
        user_dict = factories.User(password='helloworld')
        user = model.User.get(user_dict['id'])

        self.assertFalse(user.validate_password('goodbyeworld'))

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
        self.assertTrue(user.validate_password('pass'))


class TestSetPass(DBTest):
    def setup(self):
        helpers.reset_db()

    @patch('ckan.lib.cli.UserCmd.password_prompt', return_value='newpassword')
    @patch('ckanext.datagovuk.lib.mailer.mailer.mail_user')
    def test_setpass_sends_email_alert_to_user(self, mock_mailer, mock_password_prompt):
        user_dict = factories.User(password='hello123')

        user_cmd = ckan.lib.cli.UserCmd('test')
        user_cmd.args =['setpass', user_dict['name']]

        user_cmd.setpass()

        assert mock_mailer.called
        args, kwargs = mock_mailer.call_args
        assert args[0].id == user_dict['id']
        assert args[0].email == user_dict['email']
        assert args[1] == 'Your data.gov.uk publisher password has changed'
        assert args[2] == "Your password has been changed, if you haven't done it yourself, let us know"
