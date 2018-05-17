"""
Functions to retrieve the boundaries for spatial coverage when provided
with a local authority url on statistics.data.gov.uk

e.g.
    http://statistics.data.gov.uk/doc/statistical-geography/E06000031
"""
import logging
import json

import requests
from shapely.geometry import Polygon


log = logging.getLogger(__name__)

def get_boundary(url):
    """
    Gets the geographic boundary from the specified URL which is described for
    a given authority (who each have their own URL). This data *will* change,
    but should be stored against the publisher when we harvest a specific
    inventory.

    We've some inconsistency about whether the supplied URL will be the
    publisher URI or the GSS URI, so we'll support both.

    It returns the Polygon. On error, it will log the error and return None.
    """
    if not 'statistical-geography' in url:
        # e.g.: http://opendatacommunities.org/doc/london-borough-council/redbridge
        publisher_url = url + '.json'
        log.debug('Looking up publisher: %s', publisher_url)
        try:
            req = requests.get(publisher_url)
            req.raise_for_status()
        except requests.exceptions.RequestException as e:
            log.error('Failed to retrieve publisher: %s %s', e, publisher_url)
            return None

        try:
            blob = json.loads(req.content)
        except ValueError:
            log.error('Not JSON response: %s', publisher_url)
            return None
        try:
            gss_url = blob[0]['http://opendatacommunities.org/def/local-government/governsGSS'][0]['@id'] + '.json'
        except KeyError:
            log.error('Key not found : %s', publisher_url)
            return None
    else:
        gss_url = url + '.json'

    log.debug('Getting Geo boundary for authority: %s', gss_url)

    try:
        req = requests.get(gss_url)
        req.raise_for_status()
    except requests.exceptions.RequestException as e:
        log.error('Failed to retrieve publisher boundary: %s %s', e, gss_url)
        return None

    try:
        blob = json.loads(req.content)
    except ValueError:
        log.error('Not json response (gss): %s', gss_url)
        return None
    try:
        boundary = blob['result']['primaryTopic']['hasExteriorLatLongPolygon']
    except KeyError:
        log.error('Key not found (gss): %s', gss_url)
        return None

    def chunk(l):
        for i in xrange(0, len(l), 2):
            lat = l[i:i+1][0]
            lng = l[i+1:i+2][0]
            yield (float(lat), float(lng))

    poly = Polygon([c for c in chunk(boundary.strip().split(' '))])
    return poly
