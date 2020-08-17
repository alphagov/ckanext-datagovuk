from copy import deepcopy
from fnmatch import fnmatchcase

from six import iteritems, string_types
from six.moves import collections_abc

from ckan.common import config
import ckan.plugins.toolkit as toolkit

EXTRA_KEYS = [
    "contact-email", "contact-name", "contact-phone",
    "core-dataset", "date_released", "date_update_future",
    "date_updated", "foi-email", "foi-name",
    "foi-phone", "foi-web", "geographic_coverage",
    "geographic_granularity", "precision",
    "temporal_coverage-from", "temporal_coverage-to",
    "temporal_granularity", "theme-primary", "unpublished",
    "update_frequency", "theme-secondary"
]

def create_package_schema(schema_dict):
    return schema_dict

def update_package_schema(schema_dict):
    return schema_dict

def show_package_schema(schema_dict):
    schema_dict.update({
        'odi-certificate': [toolkit.get_converter('convert_from_extras'),
                            toolkit.get_converter('convert_to_json_if_string'),
                            toolkit.get_validator('ignore_missing')]
    })

    # Promote all of the extras to the top level
    for k in EXTRA_KEYS:
        schema_dict.update({
            k: [toolkit.get_converter('convert_from_extras'),
            toolkit.get_converter('convert_to_json_if_string'),
                toolkit.get_validator('ignore_missing')]
        })

    return schema_dict

def user_new_form_schema():
    from ckan.logic.schema import user_new_form_schema as default_user_new_form_schema
    schema = default_user_new_form_schema()
    schema.update({'email': [
               toolkit.get_validator('not_empty'),
               toolkit.get_validator('correct_email_suffix'),
               unicode]})
    schema['password1'] = [unicode, toolkit.get_validator('user_both_passwords_entered'),
                           toolkit.get_validator('user_password_validator_dgu'), toolkit.get_validator('user_passwords_match')]
    return schema

def user_edit_form_schema():
    from ckan.logic.schema import user_edit_form_schema as default_user_edit_form_schema
    schema = default_user_edit_form_schema()
    schema['password1'] = [unicode, toolkit.get_validator('user_both_passwords_entered'),
                       toolkit.get_validator('user_password_validator_dgu'), toolkit.get_validator('user_passwords_match')]
    return schema

# based on known text-type or specifically unindexed fields in schema.xml, specified as
# fnmatch-style patterns as it allows us to list them with the same wildcards used there.
_index_long_string_safe_key_patterns = (
    "title",
    "notes",
    "text",
    "urls",
    "depends_on",
    "dependency_of",
    "derives_from",
    "has_derivation",
    "links_to",
    "linked_from",
    "child_of",
    "parent_of",
    "harvest",
    "extras_*",
    "res_extras_*",
    # specifically unindexed by schema, using indexed="false"
    "data_dict",
    "validated_data_dict",
)

def _fnmatches_any(key, safe_key_patterns):
    return any(fnmatchcase(key, kp) for kp in safe_key_patterns)

def _trim_strings_for_index_inner(value, limit):
    if isinstance(value, string_types):
        return value[:limit]
    elif isinstance(value, collections_abc.Mapping):
        return {
            k: _trim_strings_for_index_inner(v, limit)
            for k, v in iteritems(value)
        }
    elif isinstance(value, collections_abc.Sequence):
        # already eliminated possibility of this being a string
        return [_trim_strings_for_index_inner(v, limit) for v in value]

    return value

def trim_strings_for_index(
    data_dict,
    safe_key_patterns=_index_long_string_safe_key_patterns,
):
    """
    return a copy of @data_dict, with any string values truncated to a length
    (determined by config variable `ckan.datagovuk.trim_strings_for_index_default_limit`
    unless they are under a toplevel key matching one of @safe_key_patterns.
    """
    limit = config.get(
        "ckan.datagovuk.trim_strings_for_index_default_limit",
        15000,  # approx half solr6's string-field length limit
    )

    return {
        k: (
            deepcopy(v)  # don't modify, but return a clean copy
            if _fnmatches_any(k, safe_key_patterns) else
            _trim_strings_for_index_inner(v, limit)  # recurse into, trimming strings
        ) for k, v in iteritems(data_dict)
    }
