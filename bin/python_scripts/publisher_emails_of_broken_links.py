#!/usr/bin/env python

import csv
import os
import sys
import logging

import psycopg2

POSTGRES_URL = os.environ.get('POSTGRES_URL')

logger = logging.getLogger(__name__)


def setup_logging():
    _format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    logger.setLevel(logging.INFO)
    c_handler = logging.StreamHandler()
    c_handler.setFormatter(_format)
    logger.addHandler(c_handler)


def read_resource_ids(csv_path):
    ids = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            resource_id = row.get('resource-id', '').strip()
            if resource_id:
                ids.append(resource_id)
    return ids


def query_active_publisher_emails(connection, resource_ids):
    cursor = connection.cursor()
    placeholders = ', '.join(['%s'] * len(resource_ids))

    sql = """
    SELECT DISTINCT u.email, g.name AS organisation
    FROM "user" u
    JOIN member m ON u.id = m.table_id AND m.table_name = 'user' AND m.state = 'active'
    JOIN "group" g ON g.id = m.group_id
    JOIN package p ON p.owner_org = g.id
    JOIN resource r ON r.package_id = p.id AND r.state = 'active'
    WHERE r.id IN ({ids})
      AND u.state = 'active'
    ORDER BY g.name, u.email
    """.format(ids=placeholders)

    cursor.execute(sql, resource_ids)
    return cursor.fetchall()


def main():
    setup_logging()

    if len(sys.argv) < 2:
        print('Usage: python emails_of_broken_links.py <resource_ids.csv>')
        sys.exit(1)

    csv_path = sys.argv[1]

    connection = psycopg2.connect(POSTGRES_URL)

    logger.info('Reading resource IDs from %s', csv_path)
    resource_ids = read_resource_ids(csv_path)
    logger.info('Found %d resource IDs', len(resource_ids))

    logger.info('Querying database...')
    rows = query_active_publisher_emails(connection, resource_ids)
    logger.info('Found %d results', len(rows))

    if not rows:
        logger.info('No results found.')
        return

    output_path = '/check_links/publisher_emails.csv'
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['email', 'organisation'])
        writer.writerows(rows)

    logger.info('Report written to %s', output_path)


if __name__ == '__main__':
    main()
