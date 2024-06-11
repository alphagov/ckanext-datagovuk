from ckan import model
from pytest_factoryboy import register

from ckan.tests.factories import CKANFactory
from ckanext.activity.model import Activity


pytest_plugins = [
    u'ckanext.datagovuk.tests.pytest_ckan.ckan_setup',
    u'ckanext.datagovuk.tests.pytest_ckan.fixtures',
]


# to prevent all tables from being deleted
model.repo.tables_created_and_initialised = True

@register
class ActivityFactory(CKANFactory):
    """A factory class for creating CKAN activity objects."""

    class Meta:
        model = Activity
        action = "activity_create"
