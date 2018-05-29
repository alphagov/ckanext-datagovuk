from ckan.common import _
from ckan.common import config
from ckan.plugins.toolkit import Invalid
from ckanext.datagovuk.helpers import themes

import re

def valid_theme(key, data, errors, context):
    value = data.get(key)
    if value in themes():
        return
    else:
        raise Invalid(_('Primary theme {theme} is not valid'.format(theme=value)))

