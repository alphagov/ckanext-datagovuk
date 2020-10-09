"""
Provides a superclass which does setup and teardown for tests which
use the database.
"""
import unittest
from ckan.tests import helpers
from ckanext.harvest.model import setup as db_setup


class DBTest(unittest.TestCase):
    def setUp(_self):
        helpers.reset_db()
        db_setup()

    def tearDown(_self):
        helpers.reset_db()
