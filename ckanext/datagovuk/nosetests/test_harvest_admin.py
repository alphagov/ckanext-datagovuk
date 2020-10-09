from routes import url_for

from ckanext.harvest import model as harvest_model
from ckan.tests import factories
import ckanext.harvest.tests.factories as harvest_factories

from ckan.tests.helpers import FunctionalTestBase
from ckanext.datagovuk.tests.db_test import DBTest


class TestHarvestAdmin(FunctionalTestBase, DBTest):
    def setUp(self):
        super(self.__class__, self).setUp()

        harvest_model.setup()

        self.env = {'REMOTE_USER': factories.Sysadmin()['name'].encode('ascii')}
        self.source = harvest_factories.HarvestSource()
        self.app = self._get_test_app()

    def test_clear_button_is_removed(self):
        response = self._get_harvest_admin_page()

        self.assertIn('View harvest source', response.body)
        self.assertNotIn('Clear', response.body)

    def _get_harvest_admin_page(self):
        response = self.app.get(
            url=url_for('harvest_admin', id=self.source['id']),
            extra_environ=self.env,
        )
        return response
