from ckan.common import _
from ckan.common import config
from ckan.plugins.toolkit import Invalid

import re

def correct_email_suffix(key, data, errors, context):
    value = data.get(key)
    suffix = config.get('ckan.valid_email_regexes')
    permitted_regexes = suffix.split()
    for regex in permitted_regexes:
        if re.search(regex, value):
            return
    raise Invalid(_('Email {email} does not end with a valid suffix').format(email=value))

