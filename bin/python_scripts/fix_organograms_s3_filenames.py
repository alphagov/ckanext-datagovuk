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
from pathlib import Path
import psycopg2
import re
import subprocess

import logging

logger = logging.getLogger(__name__)

connection = psycopg2.connect(os.environ.get('POSTGRES_URL'))

SKIP = COPIED = PURGED = True
DONT_SKIP = NOT_COPIED = NOT_PURGED = False


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


def get_path_parts(obj, s3_ls=False, i=0):
    if not obj.key.endswith('.csv'):
        return SKIP, None, None, i

    path = Path(obj.key)
    dataset_name = path.parts[0]
    filename = path.parts[-1]
    directory = Path(*path.parts[:-1])

    if s3_ls:
        if 'legacy/' not in obj.key and 'organogram-' in filename:
            i += 1
            print('{}: {}'.format(i, obj.key))
        return SKIP, None, None, i

    if filename[-7:] in ['-senior.csv', '-junior.csv'] or '-posts-' not in filename:
        return SKIP, None, None, i

    filename_parts = filename.split('-posts-')

    date = filename_parts[-1].rstrip('.csv')
    first_part = filename_parts[0]

    new_filename = '{}-{}.csv'.format(date, first_part)
    new_path = '{}/{}'.format(directory, new_filename)

    if not new_filename.endswith('-senior.csv') and not new_filename.endswith('-junior.csv'):
        logger.info('invalid new filename %s for %s', new_filename, filename)
        return SKIP, dataset_name, new_path, i

    return DONT_SKIP, dataset_name, new_path, i


def show_s3_ls(bucket):
    i = 0
    for obj in bucket.objects.all():
        _, _, _, i = get_path_parts(obj, True, i)


def get_url_mapping(bucket):
    mappings = []
    new_mappings = []
    dataset_names = []

    for obj in bucket.objects.all():
        skip, dataset_name, new_path, _ = get_path_parts(obj)
        if skip:
            continue

        dataset_names.append(dataset_name)
        mappings.append((dataset_name, obj.key, new_path))

    for dataset_name in dataset_names:
        senior_urls = [
            (path, new_path) for _dataset_name, path, new_path in mappings
            if new_path[-10:] == 'senior.csv' and dataset_name == _dataset_name
        ]
        junior_urls = [
            (path, new_path) for _dataset_name, path, new_path in mappings
            if new_path[-10:] == 'junior.csv' and dataset_name == _dataset_name
        ]

        if len(senior_urls) == 1 and len(junior_urls) == 1:
            if [url for _, url, _ in new_mappings if url == junior_urls[0][0]]:
                continue

            datetime_pattern = "[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}-[0-9]{2}-[0-9]{2}Z"

            senior_datetime = re.search(datetime_pattern, senior_urls[0][1]).group()

            new_junior_url = re.sub(datetime_pattern, senior_datetime, junior_urls[0][1])

            new_mappings.append((dataset_name, senior_urls[0][0], senior_urls[0][1]))
            new_mappings.append((dataset_name, junior_urls[0][0], new_junior_url))
        else:
            logger.error(
                'Did not find exactly 1 senior and 1 junior matching file: %s, found %s senior, %s junior',
                dataset_name, len(senior_urls), len(junior_urls)
            )
            break

    return new_mappings


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
            return SKIP, PURGED
        else:
            cursor, _, _ = get_db_cursor(path)
            if cursor.fetchone():
                logger.info('Missing %s', new_path)

        # purge should be run after s3 objs have already been copied and SOLR reindexed
        # so skip other operations
        return SKIP, NOT_PURGED

    cursor, _, _ = get_db_cursor(path)
    if cursor.fetchone():
        if not dry_run:
            if not exists_on_s3(bucket, new_path):
                s3.Object(bucket.name, new_path).copy_from(ACL='public-read',
                    CopySource='{}/{}'.format(bucket.name, path))
                logger.info('S3 - copied in S3 from %s to %s', path, new_path)
            else:
                return DONT_SKIP, NOT_COPIED
        else:
            logger.info('S3 - to be copied in S3 from %s to %s', path, new_path)
        return DONT_SKIP, COPIED
    else:
        return DONT_SKIP, NOT_COPIED


def get_db_cursor(obj_key):
    s3_url_prefix = os.environ.get('S3_URL_PREFIX')
    original_path = obj_key

    original_database_url = '{}{}'.format(s3_url_prefix, original_path)

    cursor = connection.cursor()
    cursor.execute("SELECT url FROM resource WHERE url='{}';".format(original_database_url))

    return cursor, original_database_url, s3_url_prefix


def update_database(bucket, path, new_path, dry_run):
    cursor, original_database_url, s3_url_prefix = get_db_cursor(path)
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
                return (original_database_url, new_database_url)
            else:
                logger.info('DB - FAILED executing %s', sql_statement)
        else:
            logger.info('DB - DRY RUN: %s', sql_statement)
            return (original_database_url, new_database_url)

    elif exists_on_s3(bucket, original_database_url):
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


def create_csv(old_new_urls):
    with open("old_new_urls.csv", "w+") as f:
        for old_url, new_url in old_new_urls:
            f.write("{}, {}\n".format(old_url, new_url))
    logger.info('CSV - Written %s lines to old_new_urls.csv', len(old_new_urls))


def main(command=None):
    while command not in ['live', 'dry-run', 'ls', 'purge', 'db']:
        command = raw_input(
            '(Options: dry-run, live, ls <list s3 organograms>, '
            'purge <remove broken s3 files>): dry-run? ')
        if not command:
            command = 'dry-run'

    dry_run = command == 'dry-run'
    live = command == 'live'
    purge = command == 'purge'
    s3_ls = command == 'ls'

    mappings = []
    solr_reindex_list = []
    old_new_urls = []
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

    if s3_ls:
        show_s3_ls(bucket)
        return

    mappings = get_url_mapping(bucket)

    i = 0
    for dataset_name, path, new_path in mappings:
        skip, file_copied_purged = process_s3(s3, bucket, path, new_path, dry_run, purge)
        if skip:
            if purge and file_copied_purged:
                files_purged = True
            continue

        old_new_url = update_database(bucket, path, new_path, dry_run)

        if (
            file_copied_purged and
            old_new_url and
            dataset_name not in solr_reindex_list
        ):
            solr_reindex_list.append(dataset_name)

        if file_copied_purged:
            if live:
                old_new_urls.append(old_new_url)
            logger.info('===============')

    if live:
        create_csv(old_new_urls)

    if solr_reindex_list:
        for dataset_name in solr_reindex_list:
            reindex_solr(dataset_name, dry_run)
    elif live or dry_run:
        logger.info('No datasets to reindex')
    elif purge and not files_purged:
        logger.info('No files purged')


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
