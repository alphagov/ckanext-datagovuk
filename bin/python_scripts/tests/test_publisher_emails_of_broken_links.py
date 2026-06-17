
import pytest
import publisher_emails_of_broken_links
from unittest.mock import patch, Mock

from python_scripts.publisher_emails_of_broken_links import (
    query_active_publisher_emails,
    read_resource_ids,
    main
)

class TestPublisherEmailsOfBrokenLinks:
    @patch('python_scripts.publisher_emails_of_broken_links.psycopg2.connect')
    def test_query_active_publisher_emails(self, mock_connect):
        mock_cursor = mock_connect.cursor.return_value
        mock_cursor.fetchall.return_value = [
            ('publisher1@example.com', 'Organisation A'),
            ('publisher2@example.com', 'Organisation B')
        ]
        mock_cursor.execute.return_value = 123
        mock_cursor.rowcount = 4

        result = query_active_publisher_emails(mock_connect, ['resource-1', 'resource-2'])

        assert result == [
            ('publisher1@example.com', 'Organisation A'),
            ('publisher2@example.com', 'Organisation B')
        ]

        mock_cursor.execute.assert_called_once_with("""
    SELECT DISTINCT u.email, g.name AS organisation
    FROM "user" u
    JOIN member m ON u.id = m.table_id AND m.table_name = 'user' AND m.state = 'active'
    JOIN "group" g ON g.id = m.group_id
    JOIN package p ON p.owner_org = g.id
    JOIN resource r ON r.package_id = p.id AND r.state = 'active'
    WHERE r.id IN (%s, %s)
      AND u.state = 'active'
    ORDER BY g.name, u.email
    """, ['resource-1', 'resource-2'])

    @patch('python_scripts.publisher_emails_of_broken_links.psycopg2.connect')
    def test_read_resource_ids(self, mock_connect, tmp_path):
        mock_cursor = mock_connect.cursor.return_value
        mock_cursor.fetchall.return_value = [
            ('publisher1@example.com', 'Organisation A'),
            ('publisher2@example.com', 'Organisation B')
        ]
        mock_cursor.execute.return_value = 123
        mock_cursor.rowcount = 4
        csv = tmp_path / "test_data.csv"

        csv.write_text("resource-id,organisation\nresource-1,Organisation A\nresource-2,Organisation B\n")

        result = read_resource_ids(csv)

        assert result == ['resource-1', 'resource-2']
    
    @patch('python_scripts.publisher_emails_of_broken_links.psycopg2.connect')
    def test_query_results_outputted_to_csv(self, mock_connect, tmp_path):
        mock_cursor = mock_connect.return_value.cursor.return_value
        mock_cursor.fetchall.return_value = [
            ('publisher1@example.com', 'Organisation A')
        ]
        mock_cursor.execute.return_value = 123
        mock_cursor.rowcount = 4

        csv = tmp_path / "test_data.csv"
        csv.write_text("resource-id,organisation\nresource-1,Organisation A\nresource-2,Organisation B\n")

        main(argv=['--csv_path', str(csv), '--output-dir', str(tmp_path)])

        output_csv = tmp_path / "publisher_emails.csv"
        assert output_csv.exists()
        assert output_csv.read_text() == "email,organisation\npublisher1@example.com,Organisation A\n"
        