import ckan.logic.schema
from ckan.plugins.toolkit import (
    check_access,
    navl_validate,
    ValidationError,
    get_action,
    )
import ckan.lib.dictization.model_save as model_save
import ckan.lib.dictization.model_dictize as model_dictize


log = __import__('logging').getLogger(__name__)


# defined as they are in ckan/action/create.py to save further hacks to the
# function copied from there
_check_access = check_access
_validate = navl_validate


def user_create(context, data_dict):
    '''Create a new user.

    You must be authorized to create users.

    :param name: the name of the new user, a string between 2 and 100
        characters in length, containing only lowercase alphanumeric
        characters, ``-`` and ``_``
    :type name: string
    :param email: the email address for the new user
    :type email: string
    :param password: the password of the new user, a string of at least 4
        characters
    :type password: string
    :param id: the id of the new user (optional)
    :type id: string
    :param fullname: the full name of the new user (optional)
    :type fullname: string
    :param about: a description of the new user (optional)
    :type about: string
    :param openid: (optional)
    :type openid: string

    :returns: the newly created user
    :rtype: dictionary

    '''
    model = context['model']
    schema = context.get('schema') or ckan.logic.schema.default_user_schema()
    session = context['session']

    _check_access('user_create', context, data_dict)

    if 'name' not in data_dict:
        data_dict['name'] = data_dict['email']

    data, errors = _validate(data_dict, schema, context)

    if errors:
        session.rollback()
        raise ValidationError(errors)

    # user schema prevents non-sysadmins from providing password_hash
    if 'password_hash' in data:
        data['_password'] = data.pop('password_hash')

    user = model_save.user_dict_save(data, context)

    # Flush the session to cause user.id to be initialised, because
    # activity_create() (below) needs it.
    session.flush()

    activity_create_context = {
        'model': model,
        'user': context['user'],
        'defer_commit': True,
        'ignore_auth': True,
        'session': session
    }
    activity_dict = {
        'user_id': user.id,
        'object_id': user.id,
        'activity_type': 'new user',
    }
    get_action('activity_create')(activity_create_context, activity_dict)

    if not context.get('defer_commit'):
        model.repo.commit()

    # A new context is required for dictizing the newly constructed user in
    # order that all the new user's data is returned, in particular, the
    # api_key.
    #
    # The context is copied so as not to clobber the caller's context dict.
    user_dictize_context = context.copy()
    user_dictize_context['keep_apikey'] = True
    user_dictize_context['keep_email'] = True
    user_dict = model_dictize.user_dictize(user, user_dictize_context)

    context['user_obj'] = user
    context['id'] = user.id

    model.Dashboard.get(user.id)  # Create dashboard for user.

    # DGU Hack: added encoding so we don't barf on unicode user names
    log.debug('Created user {name}'.format(name=user.name.encode('utf8')))
    return user_dict
