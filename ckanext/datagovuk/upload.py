'''
upload.py

Contains functions that upload the resources/zipfiles to S3.

Also contains the MetadataYAMLDumper class to generate the metadata for zipfiles.
'''
import cgi
import os
import StringIO
import zipfile
import mimetypes
import collections
import logging
import datetime
from dateutil import parser

from slugify import slugify
from pylons import config
import boto3
import yaml
import requests

import paste.fileapp
import ckan.plugins.toolkit as toolkit
import ckan.lib.uploader as uploader
from ckan.common import request


def setup_s3_bucket():
    '''
    setup_s3_bucket - Grabs the required info from config file and initializes S3 connection
    '''
    aws_access_key_id = config.get('ckan.datagovuk.s3_aws_access_key_id')
    aws_secret_access_key = config.get('ckan.datagovuk.s3_aws_secret_access_key')
    aws_region_name = config.get('ckan.datagovuk.s3_aws_region_name')
    if aws_region_name:
        s3 = boto3.resource('s3',
                            aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key,
                            region_name=aws_region_name)
    else:
        s3 = boto3.resource('s3',
                            aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key)

    bucket_name = config.get('ckan.datagovuk.s3_bucket_name')
    bucket = s3.Bucket(bucket_name)

    return bucket


def upload_resource_to_s3(context, resource):
    '''
    upload_resource_to_s3

    Uploads resource to S3 and modifies the following resource fields:
    - 'upload'
    - 'url_type'
    - 'url'
    '''

    # Init logger
    logger = logging.getLogger(__name__)
    logger.info("Starting upload_resource_to_s3 for resource %s" % resource.get('name', ''))

    # Init connection to S3
    bucket = setup_s3_bucket()

    # Get content type and extension
    content_type, _ = mimetypes.guess_type(
        resource.get('url', ''))
    extension = mimetypes.guess_extension(content_type)

    # Upload to S3
    timestamp = datetime.datetime.utcnow()
    pkg = toolkit.get_action('package_show')(context, {'id': resource['package_id']})
    s3_filepath = (pkg.get('name')
                   + '/'
                   + 'resources'
                   + '/'
                   + resource.get('timestamp', timestamp.strftime("%Y-%m-%dT%H-%M-%SZ"))
                   + '-'
                   + slugify(resource.get('name'), to_lower=True)
                   + extension)

    # If file is currently being uploaded, the file is in resource['upload']
    if isinstance(resource.get('upload', None), cgi.FieldStorage):
        logger.info("File is being uploaded")
        resource['upload'].file.seek(0)
        body = resource['upload'].file
    # If resource.get('url_type') == 'upload' then the resource is in CKAN file system
    elif resource.get('url_type') == 'upload':
        logger.info("File is on CKAN file store")
        upload = uploader.ResourceUpload(resource)
        filepath = upload.get_path(resource['id'])
        try:
            body = open(filepath, 'r')
        except OSError:
            abort(404, _('Resource data not found'))
    else:
        return ## in datagovuk, we don't want to upload from URL
        logger.info("File is downloadable from URL")
        try:
            # Start session to download files
            session = requests.Session()
            logger.info("Attempting to obtain resource %s from url %s" % (resource.get('name',''), resource.get('url', '')))
            response = session.get(
                resource.get('url', ''), timeout=30)
            # If the response status code is not 200 (i.e. success), raise Exception
            if response.status_code != 200:
                logger.error("Error obtaining resource from the given URL. Response status code is %d" % response.status_code)
                raise Exception("Error obtaining resource from the given URL. Response status code is %d" % response.status_code)
            body = response.content
            logger.info("Successfully obtained resource %s from url %s" % (resource.get('name',''), resource.get('url', '')))

        except requests.exceptions.RequestException:
            toolkit.abort(404, toolkit._(
                'Resource data not found'))

    try:
        logger.info("Uploading resource %s to S3" % resource.get('name', ''))
        bucket.Object(s3_filepath).delete()
        obj = bucket.put_object(Key=s3_filepath,
                                Body=body,
                                ContentType=content_type)
        obj.Acl().put(ACL='public-read')
        logger.info("Successfully uploaded resource %s to S3" % resource.get('name', ''))

    except Exception as exception:
        # Log the error and reraise the exception
        logger.error("Error uploading resource %s from package %s to S3" % (resource['name'], resource['package_id']))
        logger.error(exception)
        if resource.get('url_type') == 'upload':
            body.close()
        raise exception

    if resource.get('url_type') == 'upload':
        body.close()

    # Modify fields in resource
    resource['upload'] = ''
    resource['url_type'] = 's3'
    resource['url'] = config.get('ckan.datagovuk.s3_url_prefix') + s3_filepath
    update_timestamp(resource, timestamp)


def update_timestamp(resource, timestamp):
    '''use the last modified time if it exists, otherwise use the created time.

    destructively modifies resource'''
    if resource.get('last_modified') is None and resource.get('created') is None:
        resource['created'] = timestamp
    else:
        resource['last_modified'] = timestamp


def config_exists():
    '''config_exists - checks for the required s3 config options'''
    access_key = config.get('ckan.datagovuk.s3_aws_access_key_id')
    secret_key = config.get('ckan.datagovuk.s3_aws_secret_access_key')
    bucket_name = config.get('ckan.datagovuk.s3_bucket_name')
    url = config.get('ckan.datagovuk.s3_url_prefix')

    return not (access_key is None or
                secret_key is None or
                bucket_name is None or
                url is None)
