import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation

import ckanext.datagovuk.auth as auth
import ckanext.datagovuk.schema as schema_defs
import ckanext.datagovuk.action.create
import ckanext.datagovuk.action.get


class DatagovukPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm, DefaultTranslation):
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IDatasetForm, inherit=True)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')

    # IAuthFunctions

    def get_auth_functions(self):
        return {
            'group_create': auth.group_create,
            'organization_create': auth.organization_create,
            'user_auth': auth.user_auth
        }

    # IDatasetForm

    def _modify_package_schema(self, schema):
        schema.update({
            'theme-primary': [toolkit.get_validator('ignore_missing'),
                              toolkit.get_converter('convert_to_extras')]
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
                              toolkit.get_validator('ignore_missing')]
        })
        return schema

    def is_fallback(self):
        # This is the default dataset form
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    # IActions

    def get_actions(self):
        return dict(
            user_create=ckanext.datagovuk.action.create.user_create,
            user_auth=ckanext.datagovuk.action.get.user_auth
        )

    # IValidators

    def get_validators(self):
        from ckanext.datagovuk.logic.user_email_validator import correct_email_suffix
        return {
            'correct_email_suffix': correct_email_suffix,
        }

    # IRoutes

    def before_map(self, route_map):
        user_controller = 'ckanext.datagovuk.controllers.user:UserController'
        route_map.connect('register',
                          '/user/register',
                          controller=user_controller,
                          action='register')

        return route_map

    def after_map(self, route_map):
        route_map.connect('harvest_index', '/harvest', action='index')
        return route_map

    # ITemplateHelpers

    def get_helpers(self):
        return {'themes': ckanext.datagovuk.helpers.themes}

    import ckanext.datagovuk.ckan_patches  # import does the monkey patching
