#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Set up environment from ckan.ini
# export POSTGRES_URL=<sqlalchemy.url from ckan.ini>
#
# Execute script like this -
# python solr_reindex_target_date.py yyyy-mm-dd <optional command: show, reindex> <optional state: (default is active)>
#

import os
import sys
import psycopg2
import subprocess

import logging

POSTGRES_URL = os.environ.get('POSTGRES_URL')

logger = logging.getLogger(__name__)
connection = psycopg2.connect(POSTGRES_URL)


def setup_logging(log_to_file=False):
    _format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    logger.setLevel(logging.INFO)
    c_handler = logging.StreamHandler()
    c_handler.setFormatter(_format)
    logger.addHandler(c_handler)

    if log_to_file:
        f_handler = logging.FileHandler('solr_reindex_target_date.log')
        f_handler.setFormatter(_format)
        logger.addHandler(f_handler)

    logger.info('====================================================================')


def is_dev():
    return '@db' in POSTGRES_URL


def get_datasets_with_target_date(target_date, state):
    cursor = connection.cursor()
    sql = """
    SELECT name FROM package WHERE metadata_modified = '%s' and state='%s';
    """ % (target_date, state)

    cursor.execute(sql)

    return cursor


def get_datasets_with_resource_target_date(target_date, state):
    cursor = connection.cursor()
    sql = """
    SELECT name FROM package WHERE id IN (SELECT package_id FROM resource WHERE last_modified = '%s')  and state='%s';
    """ % (target_date, state)

    cursor.execute(sql)

    return cursor


def create_dataset_list(target_date, rows, is_resource):
    resource_suffix = '-resource' if is_resource else ''
    with open("reindex_datasets%s-%s.txt" % (resource_suffix, target_date), "w+") as f:
        for row in rows:
            f.write(row)
    logger.info('TXT - Written %s lines to reindex_datasets%s-%s.txt', len(rows.split('\n')) - 1, resource_suffix, target_date)


def reindex_solr(target_date, is_resource):
    resource_suffix = '-resource' if is_resource else ''
    with open("reindex_datasets%s-%s.txt" % (resource_suffix, target_date), "r+") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            fields = line.split(',')

            ckan_command = 'ckan -c {} search-index rebuild {}'.format(
                '/srv/app/production.ini' if is_dev() else '/var/ckan/ckan.ini', fields[0])

            logger.info('CKAN reindex %d/%d - Running command: %s', i+1, len(lines), ckan_command)

            try:
                subprocess.call(ckan_command, shell=True)
            except Exception as exception:
                logger.error('Subprocess Failed, exception occured: %s', exc_info=exception)


def main(target_date=None, command=None, state='active'):
    while not target_date:
        target_date = raw_input('Dataset target date (yyyy-mm-dd)? ')

    get_datasets = get_datasets_with_target_date

    while command not in ['show', 'reindex', 'show-resource', 'reindex-resource']:
        command = raw_input('(Options: show, reindex, show-resource, reindex-resource) show? ')
        if not command:
            command = 'show'

    is_resource = '-resource' in command
    if is_resource:
        logger.info('Processing resources')
        reindex = command == 'reindex-resource'
        get_datasets = get_datasets_with_resource_target_date
    else:
        reindex = command == 'reindex'

    setup_logging(log_to_file=reindex)

    if reindex:
        logger.info('Executing REINDEX')
    else:
        logger.info('Executing SHOW')

    logger.info('====================================================================')

    txt_rows = ''

    logger.info('Reindex datasets')
    for i, dataset in enumerate(get_datasets(target_date, state)):
        logger.info('%d - %s', i, dataset)
        if reindex:
            txt_rows += ','.join(dataset) + '\n'

    if reindex:
        create_dataset_list(target_date, txt_rows, is_resource)
        reindex_solr(target_date, is_resource)

    logger.info('Processing complete')

if __name__ == "__main__":
    main(
        sys.argv[1] if len(sys.argv) > 1 else None,
        sys.argv[2] if len(sys.argv) > 2 else None,
        sys.argv[3] if len(sys.argv) > 3 else None
    )
