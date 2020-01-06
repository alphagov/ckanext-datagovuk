'''
Includes S3ResourcesPackageController

Handles package and resource downloads.
'''
import logging
import os

import mimetypes
from pylons import config
from slugify import slugify

import paste.fileapp
import ckan.plugins.toolkit as toolkit
import ckan.lib.uploader as uploader
import ckan.model as model
from ckan.controllers.package import PackageController
# from ckan.common import response, request
from ckan.common import _, request, response
# from ckan.lib.base import redirect
from ckan.lib.helpers import redirect_to as redirect


class S3ResourcesPackageController(PackageController):
    '''
    S3ResourcesPackageController

    Extends CKAN PackageController.
    Handles package and resource downloads.
    '''
    def __init__(self):
        self.s3_url_prefix = config.get('ckan.datagovuk.s3_url_prefix')

    # override the default resource_download to download the file instead
    def resource_download(self, id, resource_id):
        '''Handles resource downloads for CKAN going through S3'''
        context = {
            'model': model,
            'session': model.Session,
            'user': toolkit.c.user or toolkit.c.author,
            'auth_user_obj': toolkit.c.userobj
        }

        try:
            rsc = toolkit.get_action('resource_show')(context, {'id': resource_id})
        except toolkit.ObjectNotFound:
            toolkit.abort(404, _('Resource not found'))
        except toolkit.NotAuthorized:
            toolkit.abort(401, _('Unauthorized to read resource %s') % resource_id)

        # Check where the resource is located
        # If rsc.get('url_type') == 'upload' then the resource is in CKAN file system
        if rsc.get('url_type') == 'upload':
            upload = uploader.ResourceUpload(rsc)
            filepath = upload.get_path(rsc['id'])
            fileapp = paste.fileapp.FileApp(filepath)
            try:
                status, headers, app_iter = request.call_application(fileapp)
            except OSError:
                toolkit.abort(404, _('Resource data not found'))
            response.headers.update(dict(headers))
            content_type, _ = mimetypes.guess_type(rsc.get('url', ''))
            if content_type:
                response.headers['Content-Type'] = content_type
            response.status = status
            return app_iter
        # If resource is not in CKAN file system, it should have a URL directly to the resource
        elif not 'url' in rsc:
            toolkit.abort(404, _('No download is available'))

        # Track download
        try:
            toolkit.get_action('track_resource_download')(context, rsc)
        except Exception as exception:
            # Log the error
            logger = logging.getLogger(__name__)
            logger.error("Error tracking resource download - %s" % exception)

        # Redirect the request to the URL for the resource zip
        pkg = toolkit.get_action('package_show')(context, {'id': id})
        redirect(self.s3_url_prefix
                 + pkg['name']
                 + '/'
                 + 'resources'
                 + '/'
                 + slugify(rsc.get('name'), to_lower=True)
                 + '.zip')
