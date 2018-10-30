import ckan.plugins.toolkit as toolkit
import ckanext.datagovuk.plugin as plugin
import unittest


class TestPaths(unittest.TestCase):
    def test_read_path(self):
        path = toolkit.url_for('organization_read', id='cabinet-office')
        self.assertEqual(path, '/publisher/cabinet-office')

    def test_edit_path(self):
        path = toolkit.url_for('organization_edit', id='cabinet-office')
        self.assertEqual(path, '/publisher/edit/cabinet-office')

    def test_harvest_path(self):
        path = toolkit.url_for('harvest_index')
        self.assertEqual(path, '/harvest')

    def test_healthcheck_path(self):
        path = toolkit.url_for('healthcheck')
        self.assertEqual(path, '/healthcheck')
