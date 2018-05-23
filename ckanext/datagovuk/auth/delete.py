import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


def package_delete(context, data_dict=None):
    return {
        'success': False,
        'msg': 'Only system administrators can delete datasets'
    }

