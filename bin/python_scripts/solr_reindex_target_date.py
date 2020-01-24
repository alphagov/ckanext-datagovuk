#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Set up environment from ckan.ini
# export POSTGRES_URL=<sqlalchemy.url from ckan.ini>
#
# Execute script like this -
# python solr_reindex_target_date.py yyyy-mm-dd <optional command: show, reindex>
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


def get_datasets_with_target_date(target_date):
    cursor = connection.cursor()
    sql = """
    SELECT name FROM package WHERE metadata_modified = '%s';
    """ % (target_date)

    cursor.execute(sql)

    return cursor


def create_dataset_list(target_date, rows):
    with open("reindex_datasets-%s.txt" % target_date, "w+") as f:
        for row in rows:
            f.write(row)
    logger.info('TXT - Written %s lines to reindex_datasets-%s.txt', len(rows.split('\n')) - 1, target_date)


def reindex_solr(target_date):
    with open("reindex_datasets-%s.txt" % target_date, "r+") as f:
        for line in f.readlines():
            fields = line.split(',')

            paster_command = 'paster --plugin=ckan search-index rebuild {} -c {}'.format(
                fields[0], '/srv/app/production.ini' if is_dev() else '/var/ckan/ckan.ini')

            logger.info('CKAN reindex - Running command: %s', paster_command)

            try:
                subprocess.call(paster_command, shell=True)
            except Exception as exception:
                logger.error('Subprocess Failed, exception occured: %s', exc_info=exception)


def main(target_date=None, command=None):
    while not target_date:
        target_date = raw_input('Dataset target date (yyyy-mm-dd)? ')

    while command not in ['show', 'reindex']:
        command = raw_input('(Options: show, reindex) show? ')
        if not command:
            command = 'show'

    reindex = command == 'reindex'

    setup_logging(log_to_file=reindex)

    if reindex:
        logger.info('Executing REINDEX')
    else:
        logger.info('Executing SHOW')

    logger.info('====================================================================')

    txt_rows = ''

    logger.info('Reindex datasets')
    for i, dataset in enumerate(get_datasets_with_target_date(target_date)):
        logger.info('%d - %s', i, dataset)
        if reindex:
            txt_rows += ','.join(dataset) + '\n'

    if reindex:
        create_dataset_list(target_date, txt_rows)
        reindex_solr(target_date)

    logger.info('Processing complete')

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None, sys.argv[2] if len(sys.argv) > 2 else None)
