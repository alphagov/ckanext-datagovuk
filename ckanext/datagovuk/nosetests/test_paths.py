from bs4 import BeautifulSoup
import unittest

import ckan.plugins.toolkit as toolkit
import ckan.tests.helpers as helpers
import ckanext.datagovuk.plugin as plugin


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
        app = helpers._get_test_app()
        with app.flask_app.test_request_context():
            path = toolkit.url_for('datagovuk.healthcheck')
            self.assertEqual(path, '/healthcheck')

    def test_home_path_redirects_to_index(self):
        app = helpers._get_test_app()

        resp = app.get('/home')

        assert resp.status_int == 302
        assert resp.location == 'http://localhost/'


    def test_publisher_path(self):
        app = helpers._get_test_app()
        resp = app.get('/publisher')
        assert resp.status_int == 200

        page = BeautifulSoup(resp.html.decode('utf-8'), 'html.parser')

        assert page.h1.text.strip() == (
            'Publishers'
        )

        assert page.ol.li.find_next("li").a.text.strip() == (
            'Publishers'
        )

    def test_publisher_navigation_tab(self):
        app = helpers._get_test_app()
        resp = app.get('/')
        page = BeautifulSoup(resp.html.decode('utf-8'), 'html.parser')

        text = page.find_all(href="/publisher")[0].text.strip()


        assert text == (
            'Publishers'
        )
