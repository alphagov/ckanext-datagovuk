#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Set up environment from ckan.ini
# export POSTGRES_URL=<sqlalchemy.url from ckan.ini>
#
# Execute script like this -
# python remove_march2019_duplicates.py
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
        f_handler = logging.FileHandler('remove_march2019_duplicates.log')
        f_handler.setFormatter(_format)
        logger.addHandler(f_handler)

    logger.info('====================================================================')


def is_local():
    return '@localhost' in POSTGRES_URL


def get_duplicate_datasets():
    cursor = connection.cursor()
    sql = """
    WITH duplicates AS 
    (SELECT COUNT(*) AS duplicate_count, owner_org, title, notes
    FROM package 
    WHERE state='active'
    GROUP BY owner_org, title, notes
    HAVING COUNT(*) > 1) 
    SELECT DISTINCT 
    package.id AS package_id, 
    package.name AS dataset, 
    package.title AS dataset_title, 
    "group".name AS publisher, 
    COALESCE(to_char(package.metadata_created, 'MM-DD-YYYY HH24:MI:SS'), '') as pkg_created
    FROM package
    JOIN duplicates ON package.owner_org = duplicates.owner_org 
    JOIN "group" ON package.owner_org = "group".id 
    AND package.notes = duplicates.notes 
    AND package.title = duplicates.title 
    AND package.name ~ '.+\D(\d{5,}|\d{1,3})$' 
    %s 
    ORDER BY publisher, package.title, pkg_created
    """ % ("AND package.metadata_created BETWEEN '2019-03-01' AND '2019-04-01'" if not is_local() else '')

    cursor.execute(sql)

    return cursor


def delete_dataset(dataset):
    paster_command = 'paster --plugin=ckan dataset delete {} -c /{}/ckan/ckan.ini'.format(
        dataset[0], 'etc' if is_local() else 'var')

    logger.info('CKAN delete dataset - Running command: %s', paster_command)

    try:
        subprocess.call(paster_command, shell=True)
    except Exception as exception:
        logger.error('Subprocess Failed, exception occured: %s', exc_info=exception)


def create_csv(rows):
    with open("deleted_datasets.csv", "w+") as f:
        for row in rows:
            f.write(row)
    logger.info('CSV - Written %s lines to deleted_datasets.csv', len(rows.split('\n')) - 1)


def main(command=None):
    while command not in ['show', 'run']:
        command = raw_input('(Options: show, run) show? ')
        if not command:
            command = 'show'

    run = command == 'run'

    setup_logging(log_to_file=run)

    if run:
        logger.info('Executing RUN')
    else:
        logger.info('Executing SHOW')

    logger.info('====================================================================')

    logger.info('Delete duplicate datasets')

    csv_rows = ''
    for dataset in get_duplicate_datasets():
        logger.info(dataset)
        if run:
            csv_rows += ','.join(dataset) + '\n'
            delete_dataset(dataset)

    if run:
        create_csv(csv_rows)

    logger.info('Processing complete')

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
