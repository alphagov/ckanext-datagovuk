import os
import uuid

import ckan.plugins.toolkit as toolkit
import ckan.tests.factories as factories
from ckan.model import Package
from ckanext.datagovuk.harvesters.inventory_harvester import InventoryHarvester
from ckanext.harvest.model import setup as db_setup
from ckanext.harvest.model import (HarvestObject, HarvestGatherError,
                                   HarvestObjectError, HarvestSource,
                                   HarvestJob)

class TestInventory:

    def setup(self):
        db_setup()

        self.sysadmin = factories.Sysadmin()
        self.publisher = factories.Organization()
        self.source = HarvestSource(
            url = 'file:///',
            type = 'inventory',
            publisher_id = self.publisher['id']
        )
        self.source.save()

    def teardown(self):
        self.source.delete()

    def test_harvester(self):
        job = HarvestJob(source = self.source)

        harvester = InventoryHarvester()

        # Gather all of the datasets from the XML content and make sure
        # we have created some harvest objects
        result = harvester.gather_stage(job, test_content=self._get_file_content('inventory.xml'))
        assert(len(result) == 79)

        # We only want one for testing
        harvest_object_id = result[0]

        # Make sure we can create a dataset by running the import stage
        harvest_obj = HarvestObject.get(harvest_object_id)
        harvester.import_stage(harvest_obj)
        assert(harvest_obj.package_id is not None)

        # Get the newly created package and make sure it is in the correct
        # organisation
        pkg = toolkit.get_action('package_show')(
            { 'ignore_auth': True, 'user': self.sysadmin['name'] },
            { 'id': harvest_obj.package_id },
        )
        assert(pkg['organization']['id'] == self.publisher['id'])

    def _get_file_content(self, filename):
        f = os.path.join(
            os.path.dirname(__file__),
            'data',
            filename
        )
        return open(os.path.abspath(f), 'r').read()