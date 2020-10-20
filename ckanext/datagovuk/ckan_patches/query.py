import logging

from ckan.lib.search import query

BLOCK_TAGS = ['{!xmlparser', '<!doctype']
logger = logging.getLogger(__name__)


def safe_str(obj):
    try:
        return str(obj)
    except UnicodeEncodeError:
        return obj.encode('ascii', 'ignore').decode('ascii')


def run(self, *args, **kwargs):
    for k in args[0]:
        if all(tag in safe_str(args[0][k]).lower() for tag in BLOCK_TAGS):
            logger.warn('DGU search blocked: %r', args[0][k])
            return {"count": 0, "results": []}

    return query.PackageSearchQuery.original_run(self, *args, **kwargs)

query.PackageSearchQuery.original_run = query.PackageSearchQuery.run
query.PackageSearchQuery.run = run
