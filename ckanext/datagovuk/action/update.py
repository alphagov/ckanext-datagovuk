from ckan.common import _
from ckan.lib import mailer
from ckan.logic import get_action
from ckan.logic.action.update import user_update
import ckan.model as model

from ckanext.datagovuk.lib.mailer import send_password_alert

log = __import__('logging').getLogger(__name__)


def dgu_user_update(context, data_dict):
    user_dict = user_update(context, data_dict)

    reset_password = context.get('reset_password')
    password_changed = 'password1' in data_dict and data_dict['password1'] != data_dict['old_password']

    if reset_password or password_changed:
        log.info('User password %s: %s', 'is being reset' if reset_password else 'has changed', data_dict['name'])

        user = context['user_obj']
        send_password_alert(user)
    return user_dict
