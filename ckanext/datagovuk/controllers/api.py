from ckan.controllers.api import ApiController
from ckanext.datagovuk.pii_helpers import remove_pii_from_api_search_dataset


class DGUApiController(ApiController):
    # default values for ver and register were extracted from sample api/search/dataset requests in core ckan api.py
    # https://github.com/ckan/ckan/blob/20a506ddbce33c92e3dfc510e1f1d7097caa45f9/ckan/controllers/api.py#L493
    def api_search_dataset(self, ver=1, register='dataset'):
        data = super(DGUApiController, self).search(ver, register)
        return remove_pii_from_api_search_dataset(data)
