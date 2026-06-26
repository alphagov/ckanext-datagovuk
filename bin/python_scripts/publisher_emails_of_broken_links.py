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


def read_org_names(csv_path):
    org_names = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            org_name = row.get('org-name', '').strip()
            if org_name:
                org_names.append(org_name)
    return org_names


def query_active_publisher_emails(connection, group_names):
    cursor = connection.cursor()
    placeholders = ', '.join(['%s'] * len(group_names))

    sql = """
    SELECT DISTINCT u.email, g.name AS organisation
    FROM "user" u
    JOIN member m ON u.id = m.table_id AND m.table_name = 'user' AND m.state = 'active'
    JOIN "group" g ON g.id = m.group_id
    AND g.name IN ({group_names})
    AND u.state = 'active'
    ORDER BY g.name, u.email
    """.format(group_names=placeholders)

    cursor.execute(sql, group_names)
    return cursor.fetchall()

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Get publisher emails associated with broken resource links/urls'
    )
    parser.add_argument("--csv_path", "-c", required=True, help='Path to CSV file containing organisation names')
    parser.add_argument("--output-dir", "-o", required=True, help='Directory to write publisher_emails.csv to')

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    setup_logging()

    args = parse_args(argv)

    logger.info('Reading organisation/group names from %s', args.csv_path)
    org_names = read_org_names(args.csv_path)
    logger.info('Found %d organisation/group names', len(org_names))

    logger.info('Querying database...')
    
    try:
        connection = psycopg2.connect(POSTGRES_URL)
        rows = query_active_publisher_emails(connection, org_names)
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
