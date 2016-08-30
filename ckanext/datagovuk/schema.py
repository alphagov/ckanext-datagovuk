
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