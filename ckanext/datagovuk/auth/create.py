import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


def group_create(context, data_dict=None):
    user_name = context['user']
    return {
        'success': False,
        'msg': 'Only system administrators can create groups'
    }

def organization_create(context, data_dict=None):
    user_name = context['user']
    return {
        'success': False,
        'msg': 'Only system administrators can create organisations'
    }
