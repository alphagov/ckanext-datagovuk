#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Requirements, sudo /usr/lib/venv/bin/pip install -
# boto3
# pytest
# pytest-mock
# psycopg2
# popen
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
# after being run the SOLR search index needs to be refreshed:
# paster --plugin=ckan search-index rebuild -r --config=/etc/ckan/ckan.ini

import boto3
import os
import sys
import psycopg2
import subprocess

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('app.log')

connection = psycopg2.connect(os.environ.get('POSTGRES_URL'))


def setupLogging():
    _format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(_format)
    f_handler.setFormatter(_format)
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

    if dry_run:
        logger.info('Executing DRY RUN on {}'.format(bucket))
        logger.info('====================================================================')
    else:
        logger.info('Executing permanent changes on {}'.format(bucket))
        logger.info('====================================================================')

    for obj in bucket.objects.all():
        if not obj.key.endswith('.csv'):
            continue

        path_parts = obj.key.split('/')
        dataset_name = path_parts[0]
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
            logger.info('invalid new filename {} for {}'.format(new_filename, filename))
            continue

        logger.info('{}renamed in S3 from {} to {}'.format(
            'TO BE ' if dry_run else '', obj.key, new_path))

        if not dry_run:
            s3.Object(bucket.name, new_path).copy_from(ACL='public-read',
                CopySource='{}/{}'.format(bucket.name, obj.key))

            objs = list(bucket.objects.filter(Prefix=new_path))
            if objs and objs[0].key == new_path:
                logger.info('Found', len(objs))
                s3.Object(bucket.name, obj.key).delete()
            else:
                logger.info('Not found')

        logger.info('Update database record to match url renamed in S3...')

        s3_url_prefix = os.environ.get('S3_URL_PREFIX')
        original_path = obj.key

        original_database_url = '{}{}'.format(s3_url_prefix, original_path)
        new_database_url = '{}{}'.format(s3_url_prefix, new_path)

        cursor = connection.cursor()
        cursor.execute("SELECT url FROM resource WHERE url='{}';".format(original_database_url))

        if cursor.fetchone():
            logger.info('Original url found - {}'.format(original_database_url))

            sql_statement = "UPDATE resource SET url = REPLACE(url, url, '{}') WHERE URL = '{}';".format(new_database_url,original_database_url)

            if not dry_run:
                logger.info('Not a dry run - executing statement...')

                cursor.execute('BEGIN TRANSACTION;')
                cursor.execute(sql_statement)
                cursor.execute('COMMIT TRANSACTION;')

                cursor.execute("SELECT url FROM resource WHERE url='{}';".format(new_database_url))

                if new_database_url in cursor.fetchone():
                    logger.info('SUCCESS')
                else:
                    logger.info('FAILED')
            else:
                logger.info('DRY RUN of SQL statement: {}'.format(sql_statement))

        else:
            logger.info('Original url not found in table -{}'.format(original_database_url))

        pastor_command = 'paster --plugin=ckan search-index rebuild {} -c /etc/ckan/ckan.ini'.format(dataset_name)

        if not dry_run:
            logger.info('Update dataset {} in SOLR...'.format(dataset_name))
            logger.info('Running pastor command:  {}'.format(pastor_command))

            try:
                subprocess.call(pastor_command, shell=True)
            except:
                exception = sys.exc_info()[1]
                logging.error('Exception occured: ' + str(exception))
                logging.error('Subprocess failed')
            else:
                logging.info('Subprocess finished')
        else:
            logger.info('Update dataset {} in SOLR...'.format(dataset_name))
            logger.info('To run pastor command: {}'.format(pastor_command))

        logger.info('===============')
        # import pdb; pdb.set_trace()


if __name__ == "__main__":
    main(sys.argv[1] if (len(sys.argv) > 1 and sys.argv[1] == 'dry-run') else None)
