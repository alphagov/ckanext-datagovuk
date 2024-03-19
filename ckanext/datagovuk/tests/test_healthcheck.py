def test_healthcheck(app):
    with app.flask_app.test_client() as client:
        resp = client.get("/healthcheck")
        assert resp.status_code == 200
        assert resp.get_data(as_text=True) == "OK"
