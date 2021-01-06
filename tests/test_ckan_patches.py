"""Tests for DGU monkey patches of CKAN."""
import pytest
from mock import patch

from ckan import model
from ckan.tests import factories


@pytest.mark.usefixtures("clean_db")
def test_validate_password__ok():
    user_dict = factories.User(password='helloworld')
    user = model.User.get(user_dict['id'])

    assert user.validate_password('helloworld')


@pytest.mark.usefixtures("clean_db")
def test_validate_password__wrong_password():
    user_dict = factories.User(password='helloworld')
    user = model.User.get(user_dict['id'])

    assert not user.validate_password('goodbyeworld')


@pytest.mark.ckan_config('ckan.plugins', 'datagovuk test_harvester')
@pytest.mark.usefixtures("clean_db", "with_plugins")
@patch('ckanext.datagovuk.lib.mailer.mailer.mail_user')
def test_setpass_sends_email_alert_to_user(mock_mailer, cli):
    from click.testing import CliRunner

    user_dict = factories.User(password='hello123')

    from ckan.cli.cli import ckan
    cli.invoke(ckan, ['user', 'setpass', user_dict['name']], input="newpass\nnewpass\n")

    assert mock_mailer.called
    args, kwargs = mock_mailer.call_args
    assert args[0].id == user_dict['id']
    assert args[0].email == user_dict['email']
    assert args[1] == 'Your data.gov.uk publisher password has changed'
    assert args[2] == "Your password has been changed, if you haven't done it yourself, let us know"
