import unittest

import ckan.tests.helpers as helpers


class TestHealthcheck(unittest.TestCase):
    def test_healthcheck(self):
        app = helpers._get_test_app()
        with app.flask_app.test_client() as client:
            resp = client.get("/healthcheck")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.get_data(as_text=True), "OK")
