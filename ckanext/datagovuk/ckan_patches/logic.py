from ckan.logic.validators import name_validator
from ckan.logic import schema
from ckan.logic.action import create


def default_user_schema():
    schema_ = schema.default_user_schema_original()

    # name validation is made more relaxed - allowing any characters, as Drupal
    # used to
    schema_['name'].remove(name_validator)

    return schema_

schema.default_user_schema_original = schema.default_user_schema
schema.default_user_schema = default_user_schema


def default_update_user_schema():
    schema_ = schema.default_update_user_schema_original()

    # name validation is made more relaxed - allowing any characters, as Drupal
    # used to
    schema_['name'].remove(name_validator)

    return schema_

schema.default_update_user_schema_original = schema.default_update_user_schema
schema.default_update_user_schema = default_update_user_schema
