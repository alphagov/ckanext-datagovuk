import ckan.logic.schema
from ckan.plugins.toolkit import (
    abort,
    check_access,
    navl_validate,
    ValidationError,
    get_action,
)
import ckan.lib.dictization.model_save as model_save
import ckan.lib.dictization.model_dictize as model_dictize

from ckan.model import User


log = __import__('logging').getLogger(__name__)


# defined as they are in ckan/action/create.py to save further hacks to the
# function copied from there
_check_access = check_access
_validate = navl_validate


def user_auth(context, data_dict):
    '''Authenticates a user

    You must be a system administrator to authenticate users.

    :param email: the email address of the user
    :type email: string
    :param password: the password of the user
    :type password: string

    :returns: the newly created user
    :rtype: dictionary

    '''
    model = context['model']
    session = context['session']

    _check_access('user_auth', context, data_dict)

    email = data_dict.get('email')
    password = data_dict.get('password')

    if not (email and password):
        raise ValidationError(['email and password are both required'])

    users = User.by_email(email)
    user = users[0] if users else None

    if (user is None) or \
            (not user.is_active()) or \
            (not user.validate_password(password)):
        raise ValidationError(['There was a problem authenticating this user'])

    user_dict = model_dictize.user_dictize(user, context)

    ## Get the user's organisation list to return with the login details
    fOrgList = get_action('organization_list_for_user')
    user_dict['organisations'] = fOrgList(context, {'id': user.name})

    # DGU Hack: added encoding so we don't barf on unicode user names
    log.debug('Authenticated user {name}'.format(name=user.name.encode('utf8')))
    return user_dict
