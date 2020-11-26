"""Tests for DGU monkey patches of CKAN."""
import pytest
from mock import patch

from ckan import model
from ckan.tests import factories#, helpers


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
# @patch('ckan.cli.user.click.prompt', return_value='newpassword')
@patch('ckanext.datagovuk.lib.mailer.mailer.mail_user')
# def test_setpass_sends_email_alert_to_user(cli, mock_mailer):
def test_setpass_sends_email_alert_to_user(mock_mailer, cli):
    from click.testing import CliRunner
    from ckanext.datagovuk.ckan_patches.cli import set_password

    user_dict = factories.User(password='hello123')

    # runner = CliRunner()
    # result = runner.invoke(set_password, [user_dict['name']], input="newpass\nnewpass")
    # result = runner.invoke(set_password, cli, input="newpass\nnewpass")
    from ckan.cli.cli import ckan
    result = cli.invoke(ckan, ['user', 'setpass', user_dict['name']], input="newpass\nnewpass")

    # print(result)
    print(result.output)

    # mocker.patch('ckan.lib.cli.user.click.prompt', return_value='newpassword')
    # mock_mailer = mocker.patch('ckanext.datagovuk.lib.mailer.mailer.mail_user')

    # user_cmd = ckan.lib.cli.UserCmd('test')
    # user_cmd.args =['setpass', user_dict['name']]

    # user_cmd.setpass()

    # print(user_dict)
    # set_password(user_dict['name'])

    assert mock_mailer.called
    args, kwargs = mock_mailer.call_args
    assert args[0].id == user_dict['id']
    assert args[0].email == user_dict['email']
    assert args[1] == 'Your data.gov.uk publisher password has changed'
    assert args[2] == "Your password has been changed, if you haven't done it yourself, let us know"
