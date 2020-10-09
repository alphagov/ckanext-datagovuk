import logging
import re

import requests

from ckan.plugins.core import implements
from ckanext.harvest.interfaces import IHarvester
from ckanext.datagovuk import helpers as dgu_helpers
from ckanext.datagovuk.harvesters.dgu_base import DguHarvesterBase
from ckanext.datagovuk.lib.inventory import InventoryDocument, InventoryXmlError

log = logging.getLogger(__name__)

SCHEMA_TYPE_MAP = {
    'CSV': 'csvlint',
    'XML': 'xsd',
}


class InventoryHarvester(DguHarvesterBase):
    '''
    Harvesting of LGA Inventories from a single XML document provided at a
    URL.
    '''
    implements(IHarvester)

    IDENTIFIER_KEY = 'inventory_identifier'

    def info(self):
        '''
        Returns a descriptor with information about the harvester.
        '''
        return {
                "name": "inventory",
                "title": "Inventory XML",
                "description": "Dataset metadata published according to the Inventory XML format: http://schemas.opendata.esd.org.uk/Inventory with XSD: https://github.com/datagovuk/ckanext-datagovuk/blob/master/ckanext/datagovuk/data/inventory.xsd"
            }

    def gather_stage(self, harvest_job, test_content=None):
        '''
        Fetches the single inventory document containing all of the
        datasets to be created/modified.

        :param harvest_job: HarvestJob object
        :returns: A list of HarvestObject ids
        '''
        from ckanext.harvest.model import (HarvestJob, HarvestObject,
                                   HarvestObjectExtra as HOExtra,
                                   HarvestGatherError)

        from ckanext.datagovuk.lib.geo import get_boundary
        from ckan import model

        self.last_run = None

        log.debug('Resolving source: %s', harvest_job.source.url)
        content = test_content
        if not content:
            try:
                req = requests.get(harvest_job.source.url)
                e = req.raise_for_status()
                content = req.content
            except requests.exceptions.RequestException as e:
                # e.g. requests.exceptions.ConnectionError
                self._save_gather_error(
                    'Failed to get content from URL: %s Error:%s %s' %
                    (harvest_job.source.url, e.__class__.__name__, e),
                    harvest_job)
                return None

        try:
            doc = InventoryDocument(content)
        except InventoryXmlError as e:
            self._save_gather_error(
                'Failed to parse or validate the XML document: %s %s' %
                (e.__class__.__name__, e), harvest_job)
            return None

        doc_metadata = doc.top_level_metadata()

        # TODO: Somehow update the publisher details with the geo boundary
        spatial_coverage_url = doc_metadata.get('spatial-coverage-url')

        # Find any previous harvests and store. If modified since then continue
        # otherwise bail. Store the last process date so we can check the
        # datasets
        doc_last_modified = doc_metadata['modified']
        previous = model.Session.query(HarvestJob)\
            .filter(HarvestJob.source_id==harvest_job.source_id)\
            .filter(HarvestJob.status!='New')\
            .order_by("gather_finished desc").first()
        # We thought about using the document's modified date to see if it is
        # unchanged from the previous harvest, but it's hard to tell if the
        # previous harvest was not successful due to whatever reason, so don't
        # skip the doc because of its modified date.

        # We create a new HarvestObject for each inv:Dataset within the
        # Inventory document
        ids = []
        harvested_identifiers = set()
        for dataset_node in doc.dataset_nodes():
            dataset = doc.dataset_to_dict(dataset_node)

            if dataset['identifier'] in harvested_identifiers:
                HarvestGatherError.create(
                    'Dataset with duplicate identifier "%s" - discarding'
                    % dataset['identifier'], harvest_job)
                continue
            harvested_identifiers.add(dataset['identifier'])

            guid = self.build_guid(doc_metadata['identifier'], dataset['identifier'])
            # Use the most recent modification date out of the doc and dataset,
            # since they might have forgotten to enter or update the dataset
            # date.
            dataset_last_modified = dataset['modified'] or doc_last_modified
            if dataset_last_modified and doc_last_modified:
                dataset_last_modified = max(dataset_last_modified, doc_last_modified)
            if previous:
                # object may be in the previous harvest, or an older one
                existing_object = model.Session.query(HarvestObject)\
                                       .filter_by(guid=guid)\
                                       .filter_by(current=True)\
                                       .first()
                if not existing_object:
                    status = 'new'
                    package_id = None
                elif (not existing_object.metadata_modified_date) or \
                        existing_object.metadata_modified_date.date() < dataset_last_modified:
                    status = 'changed'
                    package_id = existing_object.package_id
                else:
                    log.debug('Dataset unchanged: %s this="%s" previous="%s"',
                              dataset['title'], dataset_last_modified,
                              existing_object.metadata_modified_date)
                    continue
            else:
                status = 'new'
                package_id = None
            obj = HarvestObject(guid=guid,
                                package_id=package_id,
                                job=harvest_job,
                                content=doc.serialize_node(dataset_node),
                                harvest_source_reference=guid,
                                metadata_modified_date=dataset_last_modified,
                                extras=[HOExtra(key='status', value=status)],
                                )
            obj.save()
            ids.append(obj.id)

        return ids

    def fetch_stage(self, harvest_object):
        '''
        Check that we have content from the gather stage and just return
        success
        :returns: True if everything went right, False if errors were found
        '''
        # There is no fetching because all the content for the objects were got
        # in one request during the gather stage.
        return bool(harvest_object.content)

    @classmethod
    def build_guid(cls, doc_identifier, dataset_identifier):
        assert doc_identifier  # e.g. http://redbridge.gov.uk/
        assert dataset_identifier  # e.g. payments/payments-over-500
        return '%s/%s' % (doc_identifier, dataset_identifier)

    def get_package_dict(self, harvest_object, package_dict_defaults,
                         source_config, existing_dataset):
        '''
        Constructs a package_dict suitable to be passed to package_create or
        package_update. See documentation on
        ckan.logic.action.create.package_create for more details

        * name - a new package must have a unique name; if it had a name in the
          previous harvest, that will be in the package_dict_defaults.
        * resource.id - should be the same as the old object if updating a
          package
        * errors - call self._save_object_error() and return False
        * default values for name, owner_org, tags etc can be merged in using:
            package_dict = package_dict_defaults.merge(package_dict_harvested)
        '''
        from ckan.lib.helpers import resource_formats
        from ckan import model
        from ckanext.harvest.model import (HarvestObjectExtra as HOExtra,
                                           HarvestGatherError)

        res_formats = resource_formats()

        inv_dataset = InventoryDocument.dataset_to_dict(
            InventoryDocument.parse_xml_string(harvest_object.content)
            )

        pkg = dict(
            title=inv_dataset['title'],
            notes=inv_dataset['description'],
            state='active' if inv_dataset['active'] else 'deleted',
            resources=[],
            extras={self.IDENTIFIER_KEY: inv_dataset['identifier'],
                    'harvest_source_reference': harvest_object.guid
                    }
            )
        # License
        rights = inv_dataset.get('rights')
        if rights:
            license_id, licence = \
                dgu_helpers.get_licence_fields_from_free_text(rights)
            pkg['license_id'] = license_id
            if licence:
                pkg['extras']['licence'] = licence
                log.info('Custom licence %r', rights)
        else:
            pkg['license_id'] = ''

        # Resources
        inv_resources = [r for r in inv_dataset['resources'] if r['active']]
        existing_resource_urls = dict((r.url, r.id)
                                      for r in existing_dataset.resources) \
                                 if existing_dataset else {}
        pkg['resources'] = []
        for inv_resource in inv_resources:
            format_ = res_formats.get(inv_resource['mimetype'].lower().strip())
            if format_:
                format_ = format_[1]
            else:
                format_ = inv_resource['mimetype']
            description = inv_resource['title']
            if inv_resource['availability']:
                description += ' - %s' % inv_resource['availability']
            # if it is temporal, it should be a timeseries,
            # if it is not data, it should be an additional resource
            resource_type = 'file' if inv_resource['resource_type'] == 'Data' \
                else 'documentation'
            # Schema
            if inv_resource['conforms_to']:
                schema_url = inv_resource['conforms_to']
                schema_type = SCHEMA_TYPE_MAP.get(format_)
            else:
                schema_url = schema_type = ''
            res = {'url': inv_resource['url'],
                   'format': format_,
                   'description': description,
                   'resource_type': resource_type,
                   'schema-url': schema_url,
                   'schema-type': schema_type,
                   }
            if res['url'] in existing_resource_urls:
                res['id'] = existing_resource_urls[res['url']]
            pkg['resources'].append(res)

        # Local Authority Services and Functions
        if inv_dataset['services']:
            log.info('Local Authority Services: %r', inv_dataset['services'])
            # e.g. {http://id.esd.org.uk/service/190}
            pkg['extras']['la_service'] = ' '.join(inv_dataset['services'])
        else:
            pkg['extras']['la_service'] = ''
        if inv_dataset['functions']:
            log.info('Local Authority Functions %r', inv_dataset['functions'])
            pkg['extras']['la_function'] = ' '.join(inv_dataset['functions'])
        else:
            pkg['extras']['la_function'] = ''

        pkg = package_dict_defaults.merge(pkg)
        if not pkg.get('name'):
            # append the publisher name to differentiate similar titles better
            # than just a numbers suffix
            pkg['name'] = self._munge_title_to_name(pkg['title'])

        # Themes based on services/functions
        if 'tags' not in pkg:
            pkg['tags'] = []

        pkg['extras'] = self.extras_from_dict(pkg['extras'])
        return pkg
