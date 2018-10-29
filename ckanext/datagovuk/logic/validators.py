import re
import ckan.lib.navl.dictization_functions as df

from ckan.common import _

Invalid = df.Invalid
StopOnError = df.StopOnError
Missing = df.Missing
missing = df.missing

def user_password_validator(key, data, errors, context):
    value = data[key]

    if isinstance(value, Missing):
        pass
    elif not isinstance(value, basestring):
        errors[('password',)].append(_('Passwords must be strings'))
    elif value == '':
        pass
    elif len(value) < 8:
        errors[('password',)].append(_('Your password must be 8 characters or longer'))
    elif not bool(re.search('[A-Z]', value)) or not bool(re.search('[a-z]', value)):
        errors[('password',)].append(_('Your password must contain at least one upper and one lower case character'))
