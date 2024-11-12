#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Execute script like this -
# python remove_duplicates.py - to show impacted datasets
# python remove_duplicates.py run - to delete duplicate datasets
#

import os
import sys
import psycopg2
import subprocess

import logging

POSTGRES_URL = os.environ.get('CKAN_SQLALCHEMY_URL')

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


MARCH_2019_SQL = """
    WITH duplicates AS 
    (SELECT COUNT(*) AS duplicate_count, owner_org, title, notes, 
    package_extra.value AS metadata_date, package.state AS package_state
    FROM package 
    JOIN package_extra ON package.id = package_extra.package_id
    AND package_extra.key = 'metadata-date'
    AND package.state='active'
    GROUP BY owner_org, title, notes, package_extra.value, package.state
    HAVING COUNT(*) > 1) 
    SELECT DISTINCT 
    package.id AS package_id, 
    package.name AS dataset, 
    package.title AS dataset_title, 
    "group".name AS publisher, 
    COALESCE(to_char(package.metadata_created, 'MM-DD-YYYY HH24:MI:SS'), '') as pkg_created,
    package.state,
    duplicates.metadata_date
    FROM package
    JOIN duplicates ON package.owner_org = duplicates.owner_org 
    JOIN "group" ON package.owner_org = "group".id 
    JOIN package_extra ON package.id = package_extra.package_id
    AND package.title = duplicates.title 
    AND package.notes = duplicates.notes 
    AND package.state = duplicates.package_state 
    AND package.name ~ '.+\D(\d{5,}|\d{1,3})$' 
    AND package_extra.value = duplicates.metadata_date
    AND package_extra.key = 'metadata-date'
    %s
    ORDER BY publisher, package.title, pkg_created
    """ % ("AND package.metadata_created BETWEEN '2019-03-01' AND '2019-04-01'" if not is_local() else '')


NOV_2024_TITLES_SQL = "SELECT title FROM package WHERE state = 'active' GROUP BY title, owner_org " \
                    "HAVING COUNT(*) > 100;"


# retrieve active package_ids which are matching titles from 2 publishers with more than 100 duplicate datasets
NOV_2024_PACKAGE_IDS_SQL = "SELECT package_extra.package_id FROM package_extra, harvest_object WHERE " \
                    "harvest_object.id = value AND key = 'harvest_object_id' AND value IN (" \
                    "SELECT id FROM harvest_object WHERE id IN (" \
                    "SELECT value FROM package_extra WHERE key = 'harvest_object_id' AND package_id IN (" \
                    "SELECT id FROM package WHERE title = '%s' AND state = 'active' AND owner_org IN " \
                    "('c924c995-e063-4f30-bbd3-61418486f0a9', 'b6b50d70-9d5c-4fef-9135-7756cca343c3')))) " \
                    "ORDER BY metadata_modified_date DESC;"


def get_duplicate_datasets(sql, token=None):
    cursor = connection.cursor()
    _sql = globals()[sql]
    _sql = _sql % token if token else _sql

    cursor.execute(_sql)

    return cursor


def delete_dataset(dataset):
    command = 'ckan dataset delete {}'.format(
        dataset[0])

    logger.info('CKAN delete dataset - Running command: %s', command)

    try:
        subprocess.call(command, shell=True)
    except Exception as exception:
        logger.error('Subprocess Failed, exception occured: %s', exc_info=exception)


def reindex_dataset(dataset):
    command = 'ckan search-index rebuild {}'.format(
        dataset[0])

    logger.info('CKAN reindex dataset - Running command: %s', command)

    try:
        subprocess.call(command, shell=True)
    except Exception as exception:
        logger.error('Subprocess Failed, exception occured: %s', exc_info=exception)


def create_csv(rows):
    with open("deleted_datasets.csv", "w+") as f:
        for row in rows:
            f.write(row)
    logger.info('CSV - Written %s lines to deleted_datasets.csv', len(rows.split('\n')) - 1)


def reindex_solr():
    # this is used when restoring datasets from a 'delete' state
    # generate the csv file on the db before running the update to set package.state to 'active'
    #
    # \copy (
    # <your query which should look like the query in get_duplicate_datasets>
    # ) TO '/home/<name>/reindex_datasets.csv' WITH (FORMAT CSV, HEADER)

    with open("reindex_datasets.csv", "r+") as f:
        for line in f.readlines():
            fields = line.split(',')

            command = 'ckan search-index rebuild {}'.format(
                fields[0])

            logger.info('CKAN reindex - Running command: %s', command)

            try:
                subprocess.call(command, shell=True)
            except Exception as exception:
                logger.error('Subprocess Failed, exception occured: %s', exc_info=exception)


def main(command=None, sql="NOV_2024_TITLES_SQL", subset_sql="NOV_2024_PACKAGE_IDS_SQL"):
    while command not in ['show', 'run', 'reindex']:
        command = input('(Options: show, run, reindex) show? ')
        if not command:
            command = 'show'

    run = command == 'run'
    reindex = command == 'reindex'

    setup_logging(log_to_file=run)

    if run:
        logger.info('Executing RUN')
    elif reindex:
        logger.info('Executing REINDEX')
    else:
        logger.info('Executing SHOW')

    logger.info('====================================================================')

    if reindex:
        reindex_solr()
    else:
        csv_rows = ''

        logger.info('Delete duplicate datasets')
        counter = 0
        for dataset in get_duplicate_datasets(sql):
            if subset_sql:
                reindexed_dataset = False
                for subset_dataset in get_duplicate_datasets(subset_sql, token=dataset):
                    # reindex the latest dataset to make it available
                    if not reindexed_dataset:
                        reindex_dataset(subset_dataset)
                        reindexed_dataset = True
                        continue

                    counter += 1

                    logger.info('%d - %r', counter, f"{dataset}-{subset_dataset}")
                    if run:
                        csv_rows += ','.join(subset_dataset) + '\n'
                        delete_dataset(subset_dataset)
            else:
                counter += 1
                logger.info('%d - %r', counter, dataset)
                if run:
                    csv_rows += ','.join(dataset) + '\n'
                    delete_dataset(dataset)

        if run:
            create_csv(csv_rows)

    logger.info('Processing complete')

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
