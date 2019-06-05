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
# python fix_organograms_s3_filenames.py
#
# after being run the SOLR search index needs to be refreshed:
# paster --plugin=ckan search-index rebuild -r --config=/etc/ckan/ckan.ini

import boto3
import os
import sys
import psycopg2
import subprocess

import logging

logger = logging.getLogger(__name__)

connection = psycopg2.connect(os.environ.get('POSTGRES_URL'))


def setup_logging():
    logger.setLevel(logging.INFO)
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler('app.log')
    _format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(_format)
    f_handler.setFormatter(_format)
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    logger.info('====================================================================')


def get_path_parts(obj, s3_ls, i):
    path_parts = obj.key.split('/')
    dataset_name = path_parts[0]
    filename = path_parts[-1]
    directory = '/'.join(path_parts[:-1])

    if s3_ls:
        if 'legacy/' not in obj.key and 'organogram-' in filename:
            i += 1
            print('{}: {}'.format(i, obj.key))
        return True, None, None, i

    if filename[-7:] in ['-senior.csv', '-junior.csv'] or '-posts-' not in filename:
        return True, None, None, i

    filename_parts = filename.split('-posts-')

    date = filename_parts[-1].rstrip('.csv')
    first_part = filename_parts[0]

    new_filename = '{}-{}.csv'.format(date, first_part)
    new_path = '{}/{}'.format(directory, new_filename)

    if not new_filename.endswith('-senior.csv') and not new_filename.endswith('-junior.csv'):
        logger.info('invalid new filename %s for %s', new_filename, filename)
        return True, dataset_name, new_path, i

    return False, dataset_name, new_path, i


def exists_on_s3(bucket, path):
    objs = list(bucket.objects.filter(Prefix=path))
    return objs and objs[0].key == path


def delete_s3_file(s3, bucket, path):
    s3.Object(bucket.name, path).delete()
    logger.info('Deleted %s', path)


def process_s3(s3, bucket, path, new_path, dry_run, purge):
    if purge:
        cursor, _, _ = get_db_cursor(new_path)
        if exists_on_s3(bucket, new_path) and cursor.fetchone():
            delete_s3_file(s3, bucket, path)
            return True, True
        else:
            cursor, _, _ = get_db_cursor(path)
            if cursor.fetchone():
                logger.info('Missing %s', new_path)

        # deletion is run after s3 objs have already been copied and SOLR reindexed
        # so skip other operations
        return True, False

    if not dry_run:
        if not exists_on_s3(bucket, new_path):
            s3.Object(bucket.name, new_path).copy_from(ACL='public-read',
                CopySource='{}/{}'.format(bucket.name, path))
            logger.info('S3 - copied in S3 from %s to %s', path, new_path)
        else:
            return False, False
    else:
        logger.info('S3 - to be copied in S3 from %s to %s', path, new_path)
    return False, True


def find_in_db(obj_key):
    s3_url_prefix = os.environ.get('S3_URL_PREFIX')
    original_path = obj_key

    original_database_url = '{}{}'.format(s3_url_prefix, original_path)

    cursor = connection.cursor()
    cursor.execute("SELECT url FROM resource WHERE url='{}';".format(original_database_url))

    return cursor, original_database_url, s3_url_prefix


def update_database(obj, new_path, dry_run):
    cursor, original_database_url, s3_url_prefix = find_in_db(obj.key)
    new_database_url = '{}{}'.format(s3_url_prefix, new_path)

    if cursor.fetchone():
        sql_statement = "UPDATE resource SET url = '{}' WHERE url = '{}';".format(new_database_url,original_database_url)

        if not dry_run:
            cursor.execute('BEGIN TRANSACTION;')
            cursor.execute(sql_statement)
            cursor.execute('COMMIT TRANSACTION;')

            cursor.execute("SELECT url FROM resource WHERE url='{}';".format(new_database_url))

            if new_database_url in cursor.fetchone():
                logger.info('DB - SUCCESS executing %s', sql_statement)
                return True
            else:
                logger.info('DB - FAILED executing %s', sql_statement)
        else:
            logger.info('DB - DRY RUN: %s', sql_statement)
            return True

    elif exists_on_s3(obj.Bucket(), original_database_url):
        logger.info('DB - ERROR Original url not found in table - %s', original_database_url)


def reindex_solr(dataset_name, dry_run):
    paster_command = 'paster --plugin=ckan search-index rebuild {} -c /etc/ckan/ckan.ini'.format(dataset_name)

    logger.info('SOLR reindex - %s command: %s', 'Will run' if dry_run else 'Running', paster_command)

    if not dry_run:
        try:
            subprocess.call(paster_command, shell=True)
        except:
            exception = sys.exc_info()[1]
            logger.error('Subprocess Failed, exception occured: %s', str(exception))
        else:
            logger.info('Subprocess finished')


def main(command=None):
    while command not in ['live', 'dry-run', 'ls', 'purge', 'db']:
        command = raw_input(
            'Live run (Other options: dry-run, ls <list s3 organograms>), '
            'purge <remove broken s3 files>: Y? ')
        if not command:
            command = 'live'

    dry_run = command == 'dry-run'
    live = command == 'live'
    purge = command == 'purge'
    s3_ls = command == 'ls'

    solr_reindex_list = []
    files_purged = False

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
    elif s3_ls:
        logger.info('Executing S3 ls on %s', bucket)
    elif purge:
        logger.info('Purging S3 files on %s', bucket)
    else:
        logger.info('Executing S3 updates on %s', bucket)

    logger.info('====================================================================')

    i = 0
    for obj in bucket.objects.all():
        if not obj.key.endswith('.csv'):
            continue

        skip, dataset_name, new_path, i = get_path_parts(obj, s3_ls, i)
        if skip:
            continue

        skip, file_copied_purged = process_s3(s3, bucket, obj.key, new_path, dry_run, purge)
        if skip:
            if purge and file_copied_purged:
                files_purged = True
            continue

        if (
            file_copied_purged and
            update_database(obj, new_path, dry_run) and
            dataset_name not in solr_reindex_list
        ):
            solr_reindex_list.append(dataset_name)

        if file_copied_purged:
            logger.info('===============')
        # import pdb; pdb.set_trace()

    if solr_reindex_list:
        for dataset_name in solr_reindex_list:
            reindex_solr(dataset_name, dry_run)
    elif live or dry_run:
        logger.info('No datasets to reindex')
    elif purge and not files_purged:
        logger.info('No files purged')


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
