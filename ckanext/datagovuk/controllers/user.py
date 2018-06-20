from ckan.controllers.user import UserController
import ckan.lib.helpers as h

from ckan.common import _, c, request, response

class UserController(UserController):
    def _new_form_to_db_schema(self):
        from ckanext.datagovuk.schema import user_new_form_schema
        return user_new_form_schema()

    def me(self, locale=None):
        if not c.user:
            h.redirect_to(locale=locale, controller='user', action='login',
                          id=None)
        user_ref = c.userobj.get_reference_preferred_for_uri()
        h.redirect_to(locale=locale, controller='user', action='dashboard_datasets')
