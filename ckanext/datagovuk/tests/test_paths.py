from bs4 import BeautifulSoup
import pytest
import unittest

import ckan.plugins.toolkit as toolkit
import ckan.tests.helpers as helpers
import ckanext.datagovuk.plugin as plugin


class TestPaths:
    @pytest.mark.skip("IRoutes after_map not supported")
    def test_read_path(self):
        path = toolkit.url_for('organization_read', id='cabinet-office')
        assert path == '/publisher/cabinet-office'

    @pytest.mark.skip("IRoutes after_map not supported")
    def test_edit_path(self):
        path = toolkit.url_for('organization_edit', id='cabinet-office')
        self.assertEqual(path, '/publisher/edit/cabinet-office')

    def test_harvest_path(self):
        path = toolkit.url_for('harvest.search')
        assert path == '/harvest/'

    def test_healthcheck_path(self):
        app = helpers._get_test_app()
        with app.flask_app.test_request_context():
            path = toolkit.url_for('datagovuk.healthcheck')
            assert path == '/healthcheck'

    def test_home_path_redirects_to_index(self):
        app = helpers._get_test_app()

        resp = app.get('/home', follow_redirects=False)
        home_index = toolkit.url_for('home.index', _external=True)

        assert resp.status_code == 302
        assert resp.headers['location'] == home_index

    @pytest.mark.skip("IRoutes after_map not supported")
    def test_publisher_path(self):
        app = helpers._get_test_app()
        resp = app.get('/publisher')
        assert resp.status_int == 200

        page = BeautifulSoup(resp.get_data().decode('utf-8'), 'html.parser')

        assert page.h1.text.strip() == (
            'Publishers'
        )

        assert page.ol.li.find_next("li").a.text.strip() == (
            'Publishers'
        )

    @pytest.mark.skip("IRoutes after_map not supported")
    def test_publisher_navigation_tab(self):
        app = helpers._get_test_app()
        resp = app.get('/')
        page = BeautifulSoup(resp.get_data().decode('utf-8'), 'html.parser')
        text = page.find_all(href="/publisher")[0].text.strip()

        assert text == (
            'Publishers'
        )
