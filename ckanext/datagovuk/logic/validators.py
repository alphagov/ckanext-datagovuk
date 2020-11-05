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
    elif not isinstance(value, str):
        errors[('password',)].append(_('Passwords must be strings'))
    elif value == '':
        pass
    elif len(value) < 8:
        errors[('password',)].append(_('Your password must be 8 characters or longer'))
    elif not bool(re.search('[A-Z]', value)) or not bool(re.search('[a-z]', value)):
        errors[('password',)].append(_('Your password must contain at least one upper and one lower case character'))

# This replaces the stock validator with one with a better error message.
# Courtesy of our friends to the north.
# https://github.com/okfn/ckanext-glasgow/blob/master/ckanext/glasgow/logic/validators.py#L387
def extra_key_not_in_root_schema(key, data, errors, context):
    for schema_key in context.get('schema_keys', []):
        if schema_key == data[key]:
            raise Invalid(_('"{}" clashes with an existing reserved schema field'
                            ' that has the same name'.format(schema_key)))
