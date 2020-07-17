#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Set up environment from ckan.ini
# export POSTGRES_URL=<sqlalchemy.url from ckan.ini>
#
# Execute script like this -
# python find_invalid_tags.py
#

import csv, io, logging, os, psycopg2, subprocess, sys

from ckan.logic.schema import default_tags_schema
from ckan.lib.navl.dictization_functions import validate, Invalid

POSTGRES_URL = os.environ['POSTGRES_URL']

logger = logging.getLogger(__name__)
connection = psycopg2.connect(POSTGRES_URL)


def setup_logging():
    _format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    logger.setLevel(logging.INFO)
    c_handler = logging.StreamHandler()
    c_handler.setFormatter(_format)
    logger.addHandler(c_handler)

    f_handler = logging.FileHandler('find_invalid_tags.log')
    f_handler.setFormatter(_format)
    logger.addHandler(f_handler)

    logger.info('====================================================================')


# only target packages with tags that are active
def get_all_tags():
    cursor = connection.cursor()
    sql = """
    SELECT tag.name, count(tag.name) FROM tag, package, package_tag
    WHERE tag.id = package_tag.tag_id AND package.id = package_tag.package_id 
    AND package.state = 'active' AND package_tag.state = 'active'
    GROUP BY tag.name ORDER BY count(tag.name) DESC;
    """

    cursor.execute(sql)
    return cursor


def get_tag_data():
    cursor = connection.cursor()
    sql = """
    SELECT tag.name, package_tag.package_id, package_tag.tag_id, tag.vocabulary_id 
    FROM tag, package, package_tag
    WHERE tag.id = package_tag.tag_id AND package.id = package_tag.package_id 
    AND package.state = 'active' AND package_tag.state = 'active'
    ORDER BY tag.name;
    """

    cursor.execute(sql)
    return cursor


def create_tag_list(rows):
    with io.open("invalid_tags.txt", "w+", encoding="utf-8") as f:
        f.writelines(rows)
    logger.info('TXT - Written %s lines to invalid_tags.txt', len(rows) - 1)


def create_invalid_tag_data(invalid_tags):
    counter = 0
    with io.open("invalid_tags_data.csv", "wb") as f:
        fieldnames = ['index', 'tag_name', "package_id", "tag_id", "vocabulary_id"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, tag in enumerate(get_tag_data()):
            tag_name, package_id, tag_id, vocabulary_id = tag
            if tag_name in invalid_tags:
                counter += 1
                writer.writerow(
                    {
                        "index": str(i + 1),
                        "tag_name": tag_name,
                        "package_id": package_id,
                        "tag_id": tag_id,
                        "vocabulary_id": vocabulary_id
                    }
                )

    logger.info('CSV - Written %s lines to invalid_tags_data.csv', counter)


def patch_translator():
    import ckan.logic.validators
    def mock_ugettext(value):
        return unicode(value)
    ckan.logic.validators._ = mock_ugettext


def validate_tag(tag):
    patch_translator()

    logger.info('VALIDATE - %s', tag)

    tag_json = {
        'name': tag
    }

    _, errors = validate(tag_json, default_tags_schema())
    return errors


def main():
    setup_logging()

    logger.info('Find invalid tags')
    logger.info('====================================================================')

    rows = []
    invalid_tags = []
    total_count = 0

    for i, tag in enumerate(get_all_tags()):
        logger.info('%d - %s', i, tag)
        tag_name, count = tag
        tag_name_utf8 = tag_name.decode('utf-8')
        errors = validate_tag(tag_name_utf8)
        if errors:
            total_count += count
            logger.info('Errors: %s', errors)
            invalid_tags.append(tag_name)
            rows.append(
                u">>> {} - {}, {}, {}".format(
                    len(rows) + 1, tag_name_utf8, count, ','.join(errors['name'] if errors else []
                )) + '\n')

    rows.append(u'======\nTotal affected datasets: {}'.format(total_count))
    create_tag_list(rows)

    create_invalid_tag_data(invalid_tags)

    logger.info('Processing complete')

if __name__ == "__main__":
    main()
