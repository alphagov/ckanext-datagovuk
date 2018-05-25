import ckan.plugins.toolkit as toolkit
import ckanext.datagovuk.plugin as plugin

def test_publisher_path_exists():
    path = toolkit.url_for('publisher_read', action='read', id='cabinet-office')
    assert(path == '/publisher/cabinet-office')

def test_organization_path_redirects():
    path = toolkit.url_for('organization_read', action='read', id='cabinet-office')
    assert(path == '/publisher/cabinet-office')

