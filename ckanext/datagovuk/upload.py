'''
upload.py

Contains functions that upload the organograms to S3.

'''
import cgi
import os
import zipfile
import mimetypes
import collections
import logging
import datetime
from dateutil import parser

from slugify import slugify
from ckan.plugins.toolkit import config
import boto3
import requests
from botocore.exceptions import ClientError

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

    kwargs = {
      "aws_access_key_id": aws_access_key_id,
      "aws_secret_access_key": aws_secret_access_key,
    }

    if aws_region_name:
        kwargs["region_name"] = aws_region_name

    s3 = boto3.resource('s3', **kwargs)

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

    filename = (
        resource.get("timestamp", timestamp.strftime("%Y-%m-%dT%H-%M-%SZ"))
        + "-"
        + slugify(resource.get("name"), to_lower=True)
        + extension
    )

    s3_filepath = "/".join([pkg.get("name"), "resources", filename])

    # If file is currently being uploaded, the file is in resource['upload']
    if isinstance(resource.get('upload'), cgi.FieldStorage):
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

    try:
        logger.info("Uploading resource %s to S3" % resource.get('name', ''))
        bucket.Object(s3_filepath).delete()
        obj = bucket.put_object(Key=s3_filepath,
                                Body=body.getvalue().encode('utf-8'),
                                ContentType=content_type)
        obj.Acl().put(ACL='public-read')
        logger.info("Successfully uploaded resource %s to S3" % resource.get('name', ''))

    except ClientError as exception:
        # Log the error and reraise the exception
        logger.error("Error uploading resource %s from package %s to S3" % (resource['name'], resource['package_id']))
        logger.error(exception)
        raise exception

    finally:
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

    return all([access_key, secret_key, bucket_name, url])
