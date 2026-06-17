#!/usr/bin/env python

import argparse
import csv
import os
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

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Get publisher emails associated with broken resource links/urls'
    )
    parser.add_argument("--csv_path", "-c", required=True, help='Path to CSV file containing resource IDs')
    parser.add_argument("--output-dir", "-o", required=True, help='Directory to write publisher_emails.csv to')

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    setup_logging()

    args = parse_args(argv)

    logger.info('Reading resource IDs from %s', args.csv_path)
    resource_ids = read_resource_ids(args.csv_path)
    logger.info('Found %d resource IDs', len(resource_ids))

    logger.info('Querying database...')
    
    try:
        connection = psycopg2.connect(POSTGRES_URL)
        rows = query_active_publisher_emails(connection, resource_ids)
    finally:
        connection.close()

    logger.info('Found %d results', len(rows))

    if not rows:
        logger.info('No results found.')
        return

    output_path = os.path.join(args.output_dir, 'publisher_emails.csv')
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['email', 'organisation'])
        writer.writerows(rows)

    logger.info('Report written to %s', output_path)


if __name__ == '__main__':
    main()
