#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Set the FILENAME_BASE to the txt file containing the list of package_ids
#
# Execute script like this -
# python solr_reindex_package_ids.py
#

import os
import sys
import subprocess

import logging

logger = logging.getLogger(__name__)

FILENAME_BASE = "<filename for list of package_ids to reindex without the txt extension>"


def setup_logging(log_to_file=False):
    _format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    logger.setLevel(logging.INFO)
    c_handler = logging.StreamHandler()
    c_handler.setFormatter(_format)
    logger.addHandler(c_handler)

    if log_to_file:
        f_handler = logging.FileHandler('%s.log' % FILENAME_BASE)
        f_handler.setFormatter(_format)
        logger.addHandler(f_handler)

    logger.info('====================================================================')


def reindex_solr():
    with open("%s.txt" % FILENAME_BASE, "r+") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            paster_command = 'paster --plugin=ckan search-index rebuild {} --config /var/ckan/ckan.ini'.format(line.strip())

            logger.info('CKAN reindex %d/%d - Running command: %s', i+1, len(lines), paster_command)

            try:
                subprocess.check_call(paster_command, shell=True)
            except Exception as exception:
                logger.error('Subprocess Failed, exception occured: %s', exc_info=exception)


def main(command=None):
    setup_logging()

    logger.info('Executing REINDEX')

    logger.info('====================================================================')

    logger.info('Reindex datasets')
    reindex_solr()

    logger.info('Processing complete')

if __name__ == "__main__":
    main()
