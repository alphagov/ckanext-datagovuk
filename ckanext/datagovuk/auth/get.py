import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


def user_auth(context, data_dict=None):
    # sysadmins only
    return {'success': False}
