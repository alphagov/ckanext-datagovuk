from ckan.views.dataset import search
from ckan.views.api import action
from ckanext.datagovuk.pii_helpers import remove_pii_from_api_search_dataset


def dataset_search():
    data = action('package_search')
    return remove_pii_from_api_search_dataset(data.json)
