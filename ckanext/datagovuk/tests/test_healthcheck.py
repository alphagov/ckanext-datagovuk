from ckanext.datagovuk.controllers.healthcheck import HealthcheckController

class TestHealthcheck:

    def setup(self):
        return

    def test_healthcheck_controller(self):
        healthcheck = HealthcheckController()
        assert healthcheck.healthcheck() == 'OK'
