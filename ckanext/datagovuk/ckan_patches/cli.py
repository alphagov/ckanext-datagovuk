import click

import ckan.cli.user
from ckan.cli.user import user
import ckan.model as model
from ckanext.datagovuk.lib.mailer import send_password_alert

original_set_password = ckan.cli.user.set_password


@user.command(u'setpass', short_help=u'Set password for the user')
@click.argument(u'username')
@click.pass_context
def set_password(ctx, username):
    ctx.invoke(original_set_password, username=username)

    _user = model.User.get(username)
    send_password_alert(_user)
