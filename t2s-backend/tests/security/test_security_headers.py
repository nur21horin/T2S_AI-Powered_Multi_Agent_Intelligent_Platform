import pytest


_EXPECTED_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "permissions-policy": "camera=(), microphone=(), geolocation=()",
}


@pytest.mark.parametrize("path", ["/api/v1/health", "/api/v1/route-does-not-exist"])
def test_security_headers_are_present_on_success_and_error_responses(client, path):
    response = client.get(path)

    for name, value in _EXPECTED_HEADERS.items():
        assert response.headers[name] == value


def test_security_headers_are_present_on_cors_preflight(client):
    response = client.options(
        "/api/v1/auth/refresh",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "x-csrf-token",
        },
    )

    assert response.status_code == 200
    for name, value in _EXPECTED_HEADERS.items():
        assert response.headers[name] == value


def test_security_headers_are_present_on_unhandled_server_error(app):
    @app.get("/test-unhandled-security-header-error")
    def fail():
        raise RuntimeError("private failure")

    from fastapi.testclient import TestClient

    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/test-unhandled-security-header-error")

    assert response.status_code == 500
    assert "private failure" not in response.text
    for name, value in _EXPECTED_HEADERS.items():
        assert response.headers[name] == value
