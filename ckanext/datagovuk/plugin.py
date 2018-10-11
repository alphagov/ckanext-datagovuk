import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan import model
from ckan.lib.plugins import DefaultTranslation
from ckan.config.routing import SubMapper

import ckanext.datagovuk.auth as auth
import ckanext.datagovuk.schema as schema_defs
import ckanext.datagovuk.action.create
import ckanext.datagovuk.action.get

from ckanext.datagovuk.logic.theme_validator import valid_theme
from ckanext.harvest.model import HarvestSource, HarvestJob, HarvestObject

class DatagovukPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm, DefaultTranslation):
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IDatasetForm, inherit=True)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IConfigurer

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')

    # IAuthFunctions

    def get_auth_functions(self):
        return {
            'group_create': auth.group_create,
            'organization_create': auth.organization_create,
            'user_auth': auth.user_auth,
            'package_update': auth.package_update,
            'package_delete': auth.package_delete
        }

    # IDatasetForm

    def _modify_package_schema(self, schema):
        schema.update({
            'theme-primary': [toolkit.get_validator('ignore_missing'),
                              toolkit.get_validator('valid_theme'),
                              toolkit.get_converter('convert_to_extras')],
            'licence-custom': [toolkit.get_validator('ignore_missing'),
                              toolkit.get_converter('convert_to_extras')],
            'schema-vocabulary': [toolkit.get_validator('ignore_missing'),
                                  toolkit.get_converter('convert_to_extras')],
            'codelist': [toolkit.get_validator('ignore_missing'),
                         toolkit.get_converter('convert_to_extras')],
            'author_email': [toolkit.get_validator('ignore_missing'),
                             unicode],
            'maintainer_email': [toolkit.get_validator('ignore_missing'),
                             unicode],
        })
        for contact_key in ['contact-name', 'contact-email', 'contact-phone', 'foi-name', 'foi-email', 'foi-web', 'foi-phone']:
            schema.update({
                contact_key: [toolkit.get_validator('ignore_missing'),
                              toolkit.get_converter('convert_to_extras')]
            })
        schema['resources'].update({
                'resource-type' : [toolkit.get_validator('ignore_missing')],
                'datafile-date' : [toolkit.get_validator('ignore_missing')],
             })
        return schema

    def create_package_schema(self):
        from ckan.logic.schema import default_create_package_schema
        schema = schema_defs.create_package_schema(default_create_package_schema())
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        from ckan.logic.schema import default_update_package_schema
        schema = schema_defs.update_package_schema(default_update_package_schema())
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        from ckan.logic.schema import default_show_package_schema
        schema = schema_defs.show_package_schema(default_show_package_schema())
        schema.update({
            'theme-primary': [toolkit.get_converter('convert_from_extras'),
                              toolkit.get_validator('ignore_missing')],
            'licence-custom': [toolkit.get_converter('convert_from_extras'),
                               toolkit.get_validator('ignore_missing')],
            'schema-vocabulary': [toolkit.get_converter('convert_from_extras'),
                                  toolkit.get_validator('ignore_missing')],
            'codelist': [toolkit.get_converter('convert_from_extras'),
                         toolkit.get_validator('ignore_missing')],
        })
        for contact_key in ['contact-name', 'contact-email', 'contact-phone', 'foi-name', 'foi-email', 'foi-web', 'foi-phone']:
            schema.update({
                contact_key: [toolkit.get_converter('convert_from_extras'),
                              toolkit.get_validator('ignore_missing')]
            })
        schema['resources'].update({
                'resource-type' : [toolkit.get_validator('ignore_missing')],
                'datafile-date' : [toolkit.get_validator('ignore_missing')]
            })
        return schema

    def is_fallback(self):
        # This is the default dataset form
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    # IPackageController

    def after_show(self, context, data_dict):
        if 'type' in data_dict and data_dict['type'] != 'harvest':
            harvest_object = model.Session.query(HarvestObject) \
                    .filter(HarvestObject.package_id==data_dict['id']) \
                    .filter(HarvestObject.current==True) \
                    .first()

            if harvest_object:
                data_dict['harvest'] = []
                for key, value in [
                    ('harvest_object_id', harvest_object.id),
                    ('harvest_source_id', harvest_object.source.id),
                    ('harvest_source_title', harvest_object.source.title),
                        ]:
                    data_dict['harvest'].append({'key': key, 'value': value})

        return data_dict

    # IActions

    def get_actions(self):
        return dict(
            user_create=ckanext.datagovuk.action.create.user_create,
            user_auth=ckanext.datagovuk.action.get.user_auth
        )

    # IValidators

    def get_validators(self):
        from ckanext.datagovuk.logic.user_email_validator import correct_email_suffix
        from ckanext.datagovuk.logic.validators import user_password_validator
        return {
            'correct_email_suffix': correct_email_suffix,
            'valid_theme': valid_theme,
            'user_password_validator_dgu': user_password_validator,
        }

    # IRoutes

    def before_map(self, route_map):
        user_controller = 'ckanext.datagovuk.controllers.user:UserController'
        healthcheck_controller = 'ckanext.datagovuk.controllers.healthcheck:HealthcheckController'
        with SubMapper(route_map, controller=user_controller) as m:
            m.connect('register', '/user/register', action='register')
            m.connect('/user/logged_in', action='logged_in')
            m.connect('/user/edit', action='edit')
            m.connect('/user/edit/{id:.*}', action='edit')
            m.connect('/user/reset', action='request_reset')
        route_map.connect('healthcheck', '/healthcheck', controller=healthcheck_controller, action='healthcheck')
        return route_map

    def after_map(self, route_map):
        # Deletes all the organization routes
        delete_routes_by_path_startswith(route_map, '/organization')

        harvest_org_controller = 'ckanext.datagovuk.controllers.organization:OrganizationController'
        route_map.connect('harvest_org_list', '/publisher/harvest/' + '{id}', controller=harvest_org_controller, action='source_list')

        # Recreates the organization routes with /publisher instead.
        with SubMapper(route_map, controller='organization') as m:
            m.connect('organizations_index', '/publisher', action='index')
            m.connect('organization_index', '/publisher', action='index')
            m.connect('organization_new', '/publisher/new', action='new')
            for action in [
            'delete',
            'admins',
            'member_new',
            'member_delete',
            'history']:
                m.connect('organization_' + action,
                        '/publisher/' + action + '/{id}',
                        action=action)

            m.connect('organization_activity', '/publisher/activity/{id}/{offset}',
                    action='activity')
            m.connect('organization_read', '/publisher/{id}', action='read')
            m.connect('organization_about', '/publisher/about/{id}',
                    action='about')
            m.connect('organization_read', '/publisher/{id}', action='read',
                    ckan_icon='sitemap')
            m.connect('organization_edit', '/publisher/edit/{id}',
                    action='edit')
            m.connect('organization_members', '/publisher/members/{id}',
                    action='members')
            m.connect('organization_bulk_process',
                    '/publisher/bulk_process/{id}',
                    action='bulk_process')

        route_map.connect('harvest_index', '/harvest', action='index')
        route_map.connect('site_analytics', '/data/site-usage', action='index')

        return route_map

    # ITemplateHelpers

    def get_helpers(self):
        import ckanext.datagovuk.helpers as h
        return {
            'themes': h.themes,
            'activate_upload': h.activate_upload,
            'schemas': h.schemas,
            'split_values': h.split_values,
            'codelist': h.codelist,
            'alphabetise_dict': h.alphabetise_dict,
            'roles': h.roles,
        }

    import ckanext.datagovuk.ckan_patches  # import does the monkey patching

def delete_routes_by_path_startswith(map, path_startswith):
    """
    This function will remove from the routing map any
    path that starts with the provided argument (/ required).

    Not really a great thing to be doing, but CKAN doesn't
    provide a way to i18n URLs because it'll likely cause
    clashes with other group subclasses.
    """
    matches_to_delete = []
    for match in map.matchlist:
        if match.routepath.startswith(path_startswith):
            matches_to_delete.append(match)
    for match in matches_to_delete:
        map.matchlist.remove(match)
