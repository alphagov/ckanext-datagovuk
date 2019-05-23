#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Requirements - 
# boto3
# pytest
# moto
#
# Set up environment from ckan.ini
# export AWS_ACCESS_KEY_ID=
# export AWS_SECRET_ACCESS_KEY=
# export AWS_REGION=
# export AWS_ORG_BUCKET=
#
# Execute script like this - 
# python fix-organograms-s3-filenames.py dry-run
#

import boto3
import os
import sys

import logging

logger = logging.getLogger(__name__)

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('app.log')


def setupLogging():
    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.INFO)
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)


def main(dry_run=False):
    setupLogging()

    s3 = boto3.resource(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_REGION')
    )

    bucket = s3.Bucket(os.environ.get('AWS_ORG_BUCKET'))

    for obj in bucket.objects.all():
        if not obj.key.endswith('.csv'):
            continue

        path_parts = obj.key.split('/')
        filename = path_parts[-1]
        directory = '/'.join(path_parts[:-1])

        if filename[-7:] in ['-senior.csv', '-junior.csv'] or '-posts-' not in filename:
            continue

        # print(directory)
        # print(filename)

        filename_parts = filename.split('-posts-')

        date = filename_parts[-1].rstrip('.csv')
        first_part = filename_parts[0]

        new_filename = '{}-{}.csv'.format(date, first_part)
        new_path = '{}/{}'.format(directory, new_filename)

        if not new_filename.endswith('-senior.csv') and not new_filename.endswith('-junior.csv'):
            print('invalid new filename {} for {}'.format(new_filename, filename))
            logger.info('invalid new filename {} for {}'.format(new_filename, filename))
            continue

        print('{}renamed from {} to {}'.format(
            'TO BE ' if dry_run else '', obj.key, new_path))

        if not dry_run:
            s3.Object(bucket.name, new_path).copy_from(
                CopySource='{}/{}'.format(bucket.name, obj.key))

            objs = list(bucket.objects.filter(Prefix=new_path))
            if objs and objs[0].key == new_path:
                print('found', len(objs))
                s3.Object(bucket.name, obj.key).delete()
            else:
                print('not found')
        # break


if __name__ == "__main__":
    main(sys.argv[1] if (len(sys.argv) > 1 and sys.argv[1] == 'dry-run') else None)
