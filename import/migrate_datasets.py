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

    # Tags on old DGU had looser validation than default ckan
    tags_to_delete = []
    for tag_dict in dataset['tags'][:]:
        tag = tag_dict['name']
        # get rid of tags of 1 character e.g. B (chemical name for Boron)
        if len(tag) < 2:
            tags_to_delete.append(tag_dict)
            continue
        # munge to get rid of disallowed symbols
        munged_tag = munge_tag(tag)
        if munged_tag != tag:
            tag_dict['name'] = munged_tag
    for tag in tags_to_delete:
        dataset['tags'].remove(tag)

    # Shunt custom fields into extras (while we work out what to do with them)
    for key in ['schema', 'codelist',
                'archival', 'qa']:
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
