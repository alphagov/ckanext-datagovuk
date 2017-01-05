import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.datagovuk.auth as auth
import ckanext.datagovuk.schema as schema_defs
import ckanext.datagovuk.action.create


class DatagovukPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IDatasetForm, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        pass

    # IAuthFunctions

    def get_auth_functions(self):
        return {
            'group_create': auth.group_create,
            'organization_create': auth.organization_create
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
        actions = dict(
            user_create=ckanext.datagovuk.action.create.user_create
            )
        return actions

    import ckanext.datagovuk.ckan_patches  # import does the monkey patching
