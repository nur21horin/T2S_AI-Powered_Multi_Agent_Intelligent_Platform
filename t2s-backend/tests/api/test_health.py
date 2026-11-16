def test_health_ok(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_request_id_generated_and_returned(client):
    r = client.get("/api/v1/health")
    assert len(r.headers["x-request-id"]) >= 8


def test_valid_incoming_request_id_is_kept(client):
    r = client.get("/api/v1/health", headers={"X-Request-ID": "abc12345-def"})
    assert r.headers["x-request-id"] == "abc12345-def"


def test_unsafe_request_id_is_replaced(client):
    r = client.get("/api/v1/health", headers={"X-Request-ID": "bad id\tinjected"})
    assert r.headers["x-request-id"] != "bad id\tinjected"


def test_cors_allows_configured_origin(client):
    r = client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert r.headers["access-control-allow-credentials"] == "true"


def test_cors_blocks_unknown_origin(client):
    r = client.get("/api/v1/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in r.headers


def test_untrusted_host_rejected(client):
    r = client.get("/api/v1/health", headers={"Host": "evil.example"})
    assert r.status_code == 400
