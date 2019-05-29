#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Requirements, sudo /usr/lib/venv/bin/pip install -
# boto3
# pytest
# pytest-mock
# psycopg2
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
# python fix-organograms-s3-filenames.py dry-run
#

import boto3
import os
import sys
import psycopg2

import logging

import pdb

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('app.log')

connection = psycopg2.connect(os.environ.get('POSTGRES_URL'))


def setupLogging():
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    logger.info('====================================================================')


def main(dry_run=False):
    setupLogging()

    s3 = boto3.resource(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_REGION')
    )

    bucket = s3.Bucket(os.environ.get('AWS_ORG_BUCKET'))
    logger.info(bucket)

    if dry_run:
        print('Executing DRY RUN on {}'.format(bucket))
        logger.info('Executing DRY RUN on {}'.format(bucket))
        logger.info('====================================================================')
    else:
        print('Executing permanent changes on {}'.format(bucket))
        logger.info('Executing permanent changes on {}'.format(bucket))
        logger.info('====================================================================')


    for obj in bucket.objects.all():
        if not obj.key.endswith('.csv'):
            continue

        path_parts = obj.key.split('/')
        filename = path_parts[-1]
        directory = '/'.join(path_parts[:-1])

        if filename[-7:] in ['-senior.csv', '-junior.csv'] or '-posts-' not in filename:
            continue

        filename_parts = filename.split('-posts-')

        date = filename_parts[-1].rstrip('.csv')
        first_part = filename_parts[0]

        new_filename = '{}-{}.csv'.format(date, first_part)
        new_path = '{}/{}'.format(directory, new_filename)

        if not new_filename.endswith('-senior.csv') and not new_filename.endswith('-junior.csv'):
            print('invalid new filename {} for {}'.format(new_filename, filename))
            logger.info('invalid new filename {} for {}'.format(new_filename, filename))
            continue

        print('{}renamed in S3 from {} to {}'.format(
            'TO BE ' if dry_run else '', obj.key, new_path))
        logger.info('{}renamed in S3 from {} to {}'.format(
            'TO BE ' if dry_run else '', obj.key, new_path))

        if not dry_run:
            s3.Object(bucket.name, new_path).copy_from(ACL='public-read',
                CopySource='{}/{}'.format(bucket.name, obj.key))

            objs = list(bucket.objects.filter(Prefix=new_path))
            if objs and objs[0].key == new_path:
                print('Found', len(objs))
                logger.info('Found', len(objs))
                s3.Object(bucket.name, obj.key).delete()
            else:
                print('Not found')
                logger.info('Not found')

        print('Update database record to match url renamed in S3...')
        logger.info('Update database record to match url renamed in S3...')

        s3_url_prefix = os.environ.get('S3_URL_PREFIX')
        original_path = obj.key

        original_database_url = '{}{}'.format(s3_url_prefix, original_path)
        new_database_url = '{}{}'.format(s3_url_prefix, new_path)

        cursor = connection.cursor()
        cursor.execute("SELECT url FROM resource WHERE url='{}';".format(original_database_url))

        if cursor.fetchone():
            print('Original url found - {}'.format(original_database_url))
            logger.info('Original url found - {}'.format(original_database_url))

            sql_statement = "UPDATE resource SET url = REPLACE(url, url, '{}') WHERE URL = '{}';".format(new_database_url,original_database_url)

            if not dry_run:
                print('Not a dry run - executing statement...')
                logger.info('Not a dry run - executing statement...')

                cursor.execute('BEGIN TRANSACTION;')
                cursor.execute(sql_statement)
                cursor.execute('COMMIT TRANSACTION;')

                cursor.execute("SELECT url FROM resource WHERE url='{}';".format(new_database_url))

                if new_database_url in cursor.fetchone():
                    print('SUCCESS')
                    logger.info('SUCCESS')
                else:
                    print('FAILED')
                    logger.info('FAILED')
            else:
                print('DRY RUN of SQL statement: {}'.format(sql_statement))
                logger.info('DRY RUN of SQL statement: {}'.format(sql_statement))
        else:
            print('Original url not found in table - {}'.format(original_database_url))
            logger.info('Original url not found in table -{}'.format(original_database_url))

        print('===============')
        logger.info('===============')
        # pdb.set_trace()


if __name__ == "__main__":
    main(sys.argv[1] if (len(sys.argv) > 1 and sys.argv[1] == 'dry-run') else None)
