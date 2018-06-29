"""
Migrates the DGU dataset metadata from the old DGU-customized CKAN to be
suitable for loading into a vanilla CKAN. Some of the fields prevented
datasets to be loaded.

Run this script by passing the "-s datasets.jsonl.gz" parameter and it will
generate a new jsonl.gz in the same folder as the source file.
"""
import argparse
import json
import os
import sys
import gzip
import re

from running_stats import Stats

args = None
stats = Stats()

def process(source, output):
    with gzip.open(source, 'rb') as input_f, \
            gzip.open(output, 'wb') as output_f:
        lines = input_f.readlines()
        for line in lines:
            new_entry = clean_and_write(line)
            output_f.write(new_entry + "\n")

    print stats
    print 'Written %s' % output

def clean_and_write(dataset_json):
    dataset = json.loads(dataset_json)

    # These split-up resources are repeats of the 'resources' key and
    # cause problems on load - just get rid of them
    keys_to_delete = ['individual_resources', 'additional_resources',
                      'timeseries_resources']

    # Remove the tags
    dataset.pop('tags')
    dataset.pop('num_tags')

    # Update the theme-primary mapping
    themes_dict = {
        "Business & Economy": "business-and-economy",
        "Environment": "environment",
        "Mapping": "mapping",
        "Crime & Justice": "crime-and-justice",
        "Government": "government",
        "Society": "society",
        "Defence": "defence",
        "Government Spending": "government-spending",
        "Towns & Cities": "towns-and-cities",
        "Education": "education",
        "Health": "health",
        "Transport": "transport",
    }
    if 'theme-primary' in dataset:
        if dataset['theme-primary'] in themes_dict:
            dataset['theme-primary'] = themes_dict[dataset['theme-primary']]
        else:
            dataset['theme-primary'] = 'None'
            stats.add('Primary theme mapping not possible', dataset['name'])
    else:
        dataset['theme-primary'] = 'None'

    # Set 'codelist' to a list of codelist ids
    if 'codelist' in dataset:
        list_of_ids = []
        for code in dataset['codelist']:
            list_of_ids.append(code['id'])
        dataset['codelist'] = list_of_ids

    # Rename schema to schema-vocabulary and set to a list of schema ids
    if 'schema' in dataset:
        list_of_ids = []
        for schema in dataset['schema']:
            list_of_ids.append(schema['id'])
        dataset['schema-vocabulary'] = list_of_ids
        dataset.pop('schema')
    # Shunt custom fields into extras (while we work out what to do with them)
    for key in ['archival', 'qa', 'theme-secondary', 'geographic_coverage']:
        if key not in dataset:
            continue
        # delete an extra in that name if it exists
        for extra in dataset['extras'][:]:
            if extra['key'] == key:
                dataset['extras'].remove(extra)
        dataset['extras'].append(
            dict(
                key=key,
                value=json.dumps(dataset[key])
                ))
        keys_to_delete.append(key)

    # Some extras are defined in the schema, so need removing from extras
    for key in ['codelist', 'schema', 'theme-primary', 'contact-name', 'contact-email', 'contact-phone', 'foi-name', 'foi-email', 'foi-web', 'foi-phone', 'date_update_future']:
        for extra in dataset['extras'][:]:
            if extra['key'] == key:
                dataset['extras'].remove(extra)

    # Email address cleansing
    for key in ['author_email', 'contact_email', 'maintainer_email', 'contact-email', 'foi-email']:
        if key in dataset and dataset[key] is not None:
            dataset[key] = re.sub(r'$\s+', '', dataset[key])
            dataset[key] = re.sub(r'\s+^', '', dataset[key])
            dataset[key] = re.sub(r'$mailto:', '', dataset[key])
            dataset[key] = dataset[key].encode("ascii", errors="ignore").decode() # Removes the non-ASCII characters

    # Resource qa & archiver
    # Need to be converted from a dict (which ends up as a single extra
    # like: "qa": "{u'updated': u'2016-11-20T23:31:02.535445', ...
    # to actual JSON like:
    #       "qa": "{\"updated\": \"2016-11-20T23:31:02.535445\", ...
    for res in dataset['resources']:
        for key in ['qa', 'archiver']:
            if key in res:
                res[key] = json.dumps(res[key])

    # Delete keys
    for key in keys_to_delete:
        if key in dataset:
            del dataset[key]

    stats.add('Migrated dataset', dataset['name'])

    return json.dumps(dataset)


MAX_TAG_LENGTH = 100
MIN_TAG_LENGTH = 2

def munge_tag(tag):
    tag = re.sub(r'[^a-zA-Z0-9\- ]', '', tag).replace(' ', '-')
    tag = _munge_to_length(tag, MIN_TAG_LENGTH, MAX_TAG_LENGTH)
    return tag

def _munge_to_length(string, min_length, max_length):
    '''Pad/truncates a string'''
    if len(string) < min_length:
        string += '_' * (min_length - len(string))
    if len(string) > max_length:
        string = string[:max_length]
    return string


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Cleanup the DGU export')
    parser.add_argument('--source', '-s', dest='source',
                        help='Specify the location of the source file')
    parser.add_argument('--output', '-o', dest='output',
                        help='Specify the location of the output file')

    args = parser.parse_args()
    if not args.source or not args.output:
        print "Both source and output files are required\n"
        print parser.print_help()
        sys.exit(1)

    if not os.path.exists(args.source):
        print "Source file {0} could not be found\n".format(args.source)
        print parser.print_help()
        sys.exit(1)

    process(args.source, args.output)
