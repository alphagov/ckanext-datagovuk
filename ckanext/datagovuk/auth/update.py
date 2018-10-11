import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


def package_update(context, data_dict=None):
    return {
        'success': True,
        'msg': 'Only system administrators can edit datasets'
    }

