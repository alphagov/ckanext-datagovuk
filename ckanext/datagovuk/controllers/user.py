from ckan.controllers.user import UserController
import ckan.lib.helpers as h

from ckan.common import _, c, request, response

class UserController(UserController):
    def _new_form_to_db_schema(self):
        from ckanext.datagovuk.schema import user_new_form_schema
        return user_new_form_schema()

    def _edit_form_to_db_schema(self):
        from ckanext.datagovuk.schema import user_edit_form_schema
        return user_edit_form_schema()

    def me(self, locale=None):
        if not c.user:
            h.redirect_to(locale=locale, controller='user', action='login',
                          id=None)
        user_ref = c.userobj.get_reference_preferred_for_uri()
        h.redirect_to(locale=locale, controller='user', action='dashboard_datasets')

    def _get_form_password(self):
        password1 = request.params.getone('password1')
        password2 = request.params.getone('password2')
        if (password1 is not None and password1 != ''):
            if not len(password1) >= 8:
                raise ValueError(_('Your password must be 8 '
                                 'characters or longer.'))
            elif not password1 == password2:
                raise ValueError(_('The passwords you entered'
                                 ' do not match.'))
            return password1
        raise ValueError(_('You must provide a password'))

