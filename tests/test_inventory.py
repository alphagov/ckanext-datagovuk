import os
import pytest
import uuid

import ckan.plugins.toolkit as toolkit
import ckan.tests.factories as factories
import ckanext.harvest.tests.factories as harvest_factories
from ckan.model import Package
from ckanext.datagovuk.harvesters.inventory_harvester import InventoryHarvester
from ckanext.harvest import model as harvest_model
from ckanext.harvest.model import (HarvestObject, HarvestGatherError,
                                   HarvestObjectError, HarvestSource,
                                   HarvestJob)


@pytest.fixture
def sample_sysadmin():
    return factories.Sysadmin()


@pytest.fixture
def sample_harvest_source_and_publisher():
    sample_publisher = factories.Organization()
    data_dict = {
        'url': 'file:///',
        'source_type': 'inventory',
        'owner_org': sample_publisher['id'],
    }
    return sample_publisher, harvest_factories.HarvestSourceObj(**data_dict)


@pytest.mark.usefixtures('clean_db', 'clean_index')
class TestInventory:
    def test_harvester(self, sample_harvest_source_and_publisher, sample_sysadmin):
        sample_publisher, sample_harvest_source = sample_harvest_source_and_publisher
        
        job = HarvestJob(source=sample_harvest_source)

        harvester = InventoryHarvester()

        # Gather all of the datasets from the XML content and make sure
        # we have created some harvest objects
        result = harvester.gather_stage(job, test_content=self._get_file_content('inventory.xml'))
        assert len(result) == 79

        # We only want one for testing
        harvest_object_id = result[0]
        harvest_obj = HarvestObject.get(harvest_object_id)

        # Run the fetch stage
        fetch_result = harvester.fetch_stage(harvest_obj)
        assert fetch_result

        # Make sure we can create a dataset by running the import stage
        harvester.import_stage(harvest_obj)
        assert harvest_obj.package_id

        # Get the newly created package and make sure it is in the correct
        # organisation
        pkg = toolkit.get_action('package_show')(
            { 'ignore_auth': True, 'user': sample_sysadmin['name'] },
            { 'id': harvest_obj.package_id },
        )
        assert pkg['organization']['id'] == sample_publisher['id']

    def _get_file_content(self, filename):
        f = os.path.join(
            os.path.dirname(__file__),
            'data',
            filename
        )
        return open(os.path.abspath(f), 'r').read()
