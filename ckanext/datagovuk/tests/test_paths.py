import ckan.plugins.toolkit as toolkit
import ckanext.datagovuk.plugin as plugin

def test_read_path():
    path = toolkit.url_for('organization_read', id='cabinet-office')
    assert(path == '/publisher/cabinet-office')

def test_edit_path():
    path = toolkit.url_for('organization_edit', id='cabinet-office')
    assert(path == '/publisher/edit/cabinet-office')

def test_harvest_path():
    path = toolkit.url_for('harvest_index')
    assert(path == '/harvest')

def test_healthcheck_path():
    path = toolkit.url_for('healthcheck')
    assert(path == '/healthcheck')
