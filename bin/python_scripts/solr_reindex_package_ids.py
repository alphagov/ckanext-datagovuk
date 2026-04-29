#!/usr/bin/env python
#
# Set the FILENAME_BASE to the txt file containing the list of package_ids
#
# Execute script like this -
# python solr_reindex_package_ids.py
#

import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)

FILENAME_BASE = (
    "<filename for list of package_ids to reindex without the txt extension>"
)


def setup_logging(log_to_file=False):
    _format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    logger.setLevel(logging.INFO)
    c_handler = logging.StreamHandler()
    c_handler.setFormatter(_format)
    logger.addHandler(c_handler)

    if log_to_file:
        f_handler = logging.FileHandler("%s.log" % FILENAME_BASE)
        f_handler.setFormatter(_format)
        logger.addHandler(f_handler)

    logger.info("====================================================================")


def reindex_solr():

    ckan_ini = os.environ.get("CKAN_INI")
    if ckan_ini is None:
        logger.info("CKAN_INI env variable not set")
        sys.exit(1)

    with open(f"{FILENAME_BASE}.txt", "r") as f:
        lines = f.readlines()
        datasets = [l.strip() for l in lines if l.strip()]
        for i, line in enumerate(datasets):
            try:
                command = ["ckan", "-c", ckan_ini, "search-index", "rebuild", line]
                logger.info(
                    "CKAN reindex %d/%d - Running command: %s",
                    i + 1,
                    len(datasets),
                    command,
                )
                subprocess.check_call(command)
            except Exception:
                logger.exception("Subprocess Failed")


def main(command=None):
    setup_logging()

    logger.info("Executing REINDEX")

    logger.info("====================================================================")

    logger.info("Reindex datasets")
    reindex_solr()

    logger.info("Processing complete")


if __name__ == "__main__":
    main()
