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

    def create_package_schema(self):
        from ckan.logic.schema import default_create_package_schema
        return schema_defs.create_package_schema(default_create_package_schema())

    def update_package_schema(self):
        from ckan.logic.schema import default_update_package_schema
        return schema_defs.update_package_schema(default_update_package_schema())

    def show_package_schema(self):
        from ckan.logic.schema import default_show_package_schema
        return schema_defs.show_package_schema(default_show_package_schema())

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

    import ckanext.datagovuk.ckan_patches  # import does the monkey patching
