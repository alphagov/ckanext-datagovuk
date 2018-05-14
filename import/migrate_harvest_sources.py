'''
Migrates the DGU user info from the old DGU-customized CKAN to be
suitable for loading into a vanilla CKAN.
'''
import argparse
import os
import uuid

import ckan
import ckanapi

from running_stats import Stats

args = None
stats = Stats()

TYPE_TRANSLATION = {
    'gemini-single': 'single-doc',
    'gemini-csw': 'csw',
    'gemini-waf': 'waf',
    'data_json': 'dcat_json'
}

def ckan_prep():
    """ Loads and prepares CKAN for use, in a script that isn't part of
        CKAN, or an extension.  Ideally we'd do these sort of things as
        paster commands so that the environment is already loaded, but ...
    """
    import paste.deploy
    from paste.registry import Registry
    from pylons import translator
    from ckan.lib.cli import MockTranslator

    config_abs_path = os.path.abspath(os.environ['CKAN_INI'])
    conf = paste.deploy.appconfig('config:' + config_abs_path)

    ckan.config.environment.load_environment(conf.global_conf,
                                             conf.local_conf)

    global registry
    global translator_obj

    registry = Registry()
    registry.prepare()

    translator_obj = MockTranslator()
    registry.register(translator, translator_obj)


def process(ckan_host, production=False):
    print 'Fetching harvest sources from {}'.format(ckan_host)
    remote_ckan = ckanapi.RemoteCKAN(ckan_host)
    local_ckan = ckanapi.LocalCKAN()

    harvest_source_list = remote_ckan.action.harvest_source_list()

    print 'Located {} harvest sources'.format(len(harvest_source_list))
    for harvest_source in harvest_source_list:
        # Ignore inactive harvesters
        if not harvest_source['active']:
            continue

        # Fix malformed harvesters by using the id as a name for now
        # so that the following steps work.
        if not harvest_source['name']:
            harvest_source['name'] = harvest_source['id']

        if not production:
            harvest_source['frequency'] = 'MANUAL'

        if harvest_source['type'] in ['inventory', 'dkan']:
            print "Skipping unsupported format ({}) for now".format(harvest_source['type'])
            continue

        harvest_source['owner_org'] = harvest_source['publisher_name']
        harvest_source['source_type'] = TYPE_TRANSLATION.get(harvest_source['type'], harvest_source['type'])
        del harvest_source['id']

        update_local_harvest_source(local_ckan, harvest_source)



def update_local_harvest_source(local_ckan, harvest_source):
    action = local_ckan.action.harvest_source_create

    try:
        existing_source = local_ckan.action.harvest_source_show(id=harvest_source['name'])
        action = local_ckan.action.harvest_source_update
        print "Updating ... {}".format(harvest_source['name'])
    except ckan.logic.NotFound:
        print "Creating ... {}".format(harvest_source['name'])
        pass
    except ckan.logic.ValidationError as e:
        print "Error validating harvest source on read ... {}".format(harvest_source['name'])
        return

    try:
        action(**harvest_source)
    except ckan.logic.ValidationError as e:
        print "Error validating harvest source on write ... {}".format(harvest_source['name'])
        return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ckan_source_host',
                        default='https://data.gov.uk',
                        help='Specify the legacy CKAN host, '
                             'defaults to http://data.gov.uk')
    parser.add_argument('--production',
                        help='Specify this to import all harvest_sources with '
                             'the same settings, otherwise they are all set '
                             'to MANUAL',
                        action="store_true")

    args = parser.parse_args()

    ckan_prep()
    process(args.ckan_source_host, args.production)
