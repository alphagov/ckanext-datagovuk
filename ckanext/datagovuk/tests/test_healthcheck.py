import unittest
from ckanext.datagovuk.controllers.healthcheck import HealthcheckController

class TestHealthcheck(unittest.TestCase):
    def test_healthcheck_controller(self):
        healthcheck = HealthcheckController()
        self.assertEqual(healthcheck.healthcheck(), 'OK')
