from ckan.controllers.user import UserController

class UserController(UserController):
    def _new_form_to_db_schema(self):
        from ckanext.datagovuk.schema import user_new_form_schema
        return user_new_form_schema()

