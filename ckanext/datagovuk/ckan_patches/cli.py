import ckan.lib.cli

from ckanext.datagovuk.lib.mailer import send_password_alert


def setpass(self):
    ckan.lib.cli.UserCmd.original_setpass(self)

    if len(self.args) > 1:
        import ckan.model as model

        username = self.args[1]
        user = model.User.get(username)
        send_password_alert(user)


ckan.lib.cli.UserCmd.original_setpass = ckan.lib.cli.UserCmd.setpass
ckan.lib.cli.UserCmd.setpass = setpass
