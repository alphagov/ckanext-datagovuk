#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Requirements: 
# in ./bin/python_scripts directory >
#   sudo /usr/lib/venv/bin/pip install -r requirements.txt
#
# Set up environment from ckan.ini
# export AWS_ACCESS_KEY_ID=
# export AWS_SECRET_ACCESS_KEY=
# export AWS_REGION=
# export AWS_ORG_BUCKET=
# export S3_URL_PREFIX=
# export POSTGRES_URL=<sqlalchemy.url from ckan.ini>
#
# Execute script like this -
# python fix_organograms_s3_filenames_exts.py
#

import boto3
import os
import sys
import psycopg2
import subprocess

import logging

DRY_RUN = PURGED = True
NOT_COPIED = NOT_PURGED = False
POSTGRES_URL = os.environ.get('POSTGRES_URL')

logger = logging.getLogger(__name__)
connection = psycopg2.connect(POSTGRES_URL)


def setup_logging():
    logger.setLevel(logging.INFO)
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler('fix_organogram_s3_filenames_ext.log')
    _format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(_format)
    f_handler.setFormatter(_format)
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    logger.info('====================================================================')


def get_dataset_name_and_bucket_path(path):
    if not path.endswith('.csv'):
        return

    bucket_path = path[len(os.environ.get('S3_URL_PREFIX')):]
    dataset_name = bucket_path.split('/')[0]

    return dataset_name, bucket_path

def exists_on_s3(bucket, path):
    objs = list(bucket.objects.filter(Prefix=path))
    return objs and objs[0].key == path


def delete_s3_file(s3, bucket, path):
    s3.Object(bucket.name, path).delete()
    logger.info('Deleted %s', path)


def get_affected_records():
    cursor = connection.cursor()

    sql = "SELECT url FROM resource WHERE url LIKE '%.csv.csv' AND created > '2020-01-01';"
    cursor.execute(sql)

    return [rec for rec, in list(cursor.fetchall())]


def process_s3(s3, bucket, path, dry_run):
    new_path = path[:-4]

    if not dry_run:
        if not exists_on_s3(bucket, new_path):
            s3.Object(bucket.name, new_path).copy_from(ACL='public-read',
                CopySource='{}/{}'.format(bucket.name, path))
            logger.info('S3 - copied in S3 from %s to %s', path, new_path)

            if exists_on_s3(bucket, new_path):
                delete_s3_file(s3, bucket, path)
                return PURGED
            else:
                logger.info('New file %s, not found', new_path)
                return NOT_PURGED
        else:
            return NOT_COPIED
    else:
        logger.info('S3 - to be copied in S3 from %s to %s', path, new_path)
        return DRY_RUN


def update_database(bucket, path, dataset_name, dry_run):
    new_path = path[:-4]

    sql_statement = "UPDATE resource SET url = '{}' WHERE url='{}';".format(new_path, path)
    # we need to update the metadta_modified to force Publish to pick up the change 
    # by setting the date to a particular date it should be easier to identify affected datasets
    sql_statement += "UPDATE package SET metadata_modified = '2020-02-13' WHERE name='{}';".format(dataset_name)

    if not dry_run:
        cursor = connection.cursor()
        cursor.execute('BEGIN TRANSACTION;')
        cursor.execute(sql_statement)
        cursor.execute('COMMIT;')

        cursor.execute("SELECT url FROM resource WHERE url='{}';".format(new_path))

        if new_path in cursor.fetchone():
            logger.info('DB - SUCCESS executing %s', sql_statement)
            return True
        else:
            logger.info('DB - FAILED executing %s', sql_statement)
            return False
    else:
        logger.info('DB - DRY RUN: %s', sql_statement)
        return True


def reindex_solr(dataset_name, dry_run):
    paster_command = 'paster --plugin=ckan search-index rebuild {} --config {}'.format(
        dataset_name, '/srv/app/production.ini' if '@db' in POSTGRES_URL else '/var/ckan/ckan.ini')

    logger.info('SOLR reindex - %s command: %s', 'Will run' if dry_run else 'Running', paster_command)

    if not dry_run:
        try:
            subprocess.call(paster_command, shell=True)
        except Exception as exception:
            logger.error('Subprocess Failed, exception occured: %s', exc_info=exception)
        else:
            logger.info('Subprocess finished')


def main(command=None):
    while command not in ['live', 'dry-run']:
        command = raw_input(
            '(Options: dry-run, live: dry-run? ')
        if not command:
            command = 'dry-run'

    dry_run = command == 'dry-run'
    live = command == 'live'

    solr_reindex_list = []

    setup_logging()

    s3 = boto3.resource(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_REGION')
    )

    bucket = s3.Bucket(os.environ.get('AWS_ORG_BUCKET'))

    if dry_run:
        logger.info('Executing DRY RUN on %s', bucket)
    else:
        logger.info('Executing S3 updates on %s', bucket)

    logger.info('====================================================================')

    for i, path in enumerate(get_affected_records()):
        logger.info('===== %d =====', i + 1)
        dataset_name, bucket_path = get_dataset_name_and_bucket_path(path)

        file_copied_purged = process_s3(s3, bucket, bucket_path, dry_run)

        db_updated = update_database(bucket, path, dataset_name, dry_run)

        if (
            file_copied_purged and
            db_updated and
            dataset_name not in solr_reindex_list
        ):
            solr_reindex_list.append(dataset_name)

    if solr_reindex_list:
        logger.info('===========')
        for dataset_name in solr_reindex_list:
            reindex_solr(dataset_name, dry_run)
    elif live or dry_run:
        logger.info('No datasets to reindex')


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
