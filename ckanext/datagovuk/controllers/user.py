from ckan.controllers.user import UserController, set_repoze_user
from ckan.common import _, c, request, response
import ckan.lib.base as base
import ckan.model as model
import ckan.lib.helpers as h
import ckan.authz as authz
import ckan.logic as logic
import ckan.logic.schema as schema
import ckan.lib.captcha as captcha
import ckan.lib.mailer as mailer
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.lib.authenticator as authenticator
import ckan.plugins as p


check_access = logic.check_access
get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
UsernamePasswordError = logic.UsernamePasswordError

DataError = dictization_functions.DataError
unflatten = dictization_functions.unflatten

class UserController(UserController):
    def _new_form_to_db_schema(self):
        from ckanext.datagovuk.schema import user_new_form_schema
        return user_new_form_schema()

    def _save_edit(self, id, context):
        try:
            if id in (c.userobj.id, c.userobj.name):
                current_user = True
            else:
                current_user = False
            old_username = c.userobj.name

            data_dict = logic.clean_dict(unflatten(
                logic.tuplize_dict(logic.parse_params(request.params))))
            context['message'] = data_dict.get('log_message', '')
            data_dict['id'] = id

            data_dict['email'] = data_dict['name']

            email_changed = data_dict['email'] != c.userobj.email

            if (data_dict['password1'] and data_dict['password2']) \
                    or email_changed:
                identity = {'login': c.user,
                            'password': data_dict['old_password']}
                auth = authenticator.UsernamePasswordAuthenticator()

                if auth.authenticate(request.environ, identity) != c.user:
                    raise UsernamePasswordError

            if 'activity_streams_email_notifications' not in data_dict:
                data_dict['activity_streams_email_notifications'] = False

            user = get_action('user_update')(context, data_dict)
            h.flash_success(_('Profile updated'))

            if current_user and data_dict['name'] != old_username:
                set_repoze_user(data_dict['name'])
            h.redirect_to(controller='user', action='read', id=user['name'])
        except NotAuthorized:
            abort(403, _('Unauthorized to edit user %s') % id)
        except NotFound, e:
            abort(404, _('User not found'))
        except DataError:
            abort(400, _(u'Integrity Error'))
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.edit(id, data_dict, errors, error_summary)
        except UsernamePasswordError:
            errors = {'oldpassword': [_('Password entered was incorrect')]}
            error_summary = {_('Old Password'): _('incorrect password')}
            return self.edit(id, data_dict, errors, error_summary)

