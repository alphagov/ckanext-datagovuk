from mock import patch

import ckan.model as model
from ckan.tests import factories, helpers
from ckanext.datagovuk.action.update import dgu_user_update


class TestWhenUpdatingUser(object):

    def setup(self):
        helpers.reset_db()

    @patch('ckanext.datagovuk.action.update.user_update')
    @patch('ckanext.datagovuk.lib.mailer.mailer.mail_user')
    def test_an_email_alert_gets_sent_when_password_changes(self, mock_mailer, mock_user_update):
        user_dict = factories.User(password='hello123')
        user_dict.update(password1='password', old_password= 'oldpassword')

        context = {
            "user_obj": model.User.get(user_dict['name'])
        }

        dgu_user_update(context, user_dict)
        assert mock_mailer.called
        args, kwargs = mock_mailer.call_args
        assert args[0].email == user_dict['email']
        assert args[1] == 'Your data.gov.uk publisher password has changed'
        assert args[2] == "Your password has been changed, if you haven't done it yourself, let us know"

    @patch('ckanext.datagovuk.action.update.user_update')
    @patch('ckanext.datagovuk.lib.mailer.mailer.mail_user')
    def test_an_email_alert_gets_sent_when_password_resets(self, mock_mailer, mock_user_update):
        user_dict = factories.User(password='hello123')

        context = {
            "reset_password": True,
            "user_obj": model.User.get(user_dict['name'])
        }

        dgu_user_update(context, user_dict)
        assert mock_mailer.called
        args, kwargs = mock_mailer.call_args
        assert args[0].email == user_dict['email']
        assert args[1] == 'Your data.gov.uk publisher password has changed'
        assert args[2] == "Your password has been changed, if you haven't done it yourself, let us know"
