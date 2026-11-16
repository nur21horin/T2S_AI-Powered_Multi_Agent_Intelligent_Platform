from uuid import uuid4


WEB_ORIGIN = "http://localhost:3000"


def _register_and_verify(client, email: str) -> None:
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Rate Limit Student",
            "password": "correct-horse-battery-42",
        },
    )
    assert registered.status_code == 201, registered.text
    token = client.app.state.email_sender.verification_tokens[email]
    verified = client.post("/api/v1/auth/email/verify", json={"token": token})
    assert verified.status_code == 200, verified.text


def test_login_account_bucket_counts_failures_but_allows_valid_credentials(db_client):
    email = f"rate-limit-{uuid4().hex}@example.com"
    _register_and_verify(db_client, email)

    responses = [
        db_client.post(
            "/api/v1/auth/login",
            json={"email": email.upper(), "password": "incorrect-password"},
            headers={"Origin": WEB_ORIGIN},
        )
        for _ in range(6)
    ]

    assert [response.status_code for response in responses[:5]] == [401] * 5
    assert responses[5].status_code == 429
    assert int(responses[5].headers["retry-after"]) >= 1

    valid = db_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "correct-horse-battery-42"},
        headers={"Origin": WEB_ORIGIN},
    )
    assert valid.status_code == 200, valid.text


def test_login_failure_limit_does_not_reveal_account_existence(db_client):
    known_email = f"known-{uuid4().hex}@example.com"
    _register_and_verify(db_client, known_email)
    email = f"nonexistent-{uuid4().hex}@example.com"
    known_failure = db_client.post(
        "/api/v1/auth/login",
        json={"email": known_email, "password": "incorrect-password"},
        headers={"Origin": WEB_ORIGIN},
    )
    unknown_failure = db_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "incorrect-password"},
        headers={"Origin": WEB_ORIGIN},
    )
    known_error = known_failure.json()["error"]
    unknown_error = unknown_failure.json()["error"]
    assert known_failure.status_code == unknown_failure.status_code == 401
    assert (known_error["code"], known_error["message"], known_error["details"]) == (
        unknown_error["code"], unknown_error["message"], unknown_error["details"]
    )

    responses = [
        db_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "incorrect-password"},
            headers={"Origin": WEB_ORIGIN},
        )
        for _ in range(5)
    ]
    assert all(response.status_code == 401 for response in responses[:4])
    assert responses[4].status_code == 429


def test_registration_ip_limit_is_enforced(db_client):
    responses = [
        db_client.post(
            "/api/v1/auth/register",
            json={
                "email": f"register-{uuid4().hex}@example.com",
                "full_name": "Rate Limit Student",
                "password": "correct-horse-battery-42",
            },
        )
        for _ in range(6)
    ]

    assert [response.status_code for response in responses] == [201] * 5 + [429]


def test_email_verification_ip_limit_is_enforced(db_client):
    responses = [
        db_client.post(
            "/api/v1/auth/email/verify", json={"token": "x" * 32}
        )
        for _ in range(11)
    ]

    assert [response.status_code for response in responses[:10]] == [401] * 10
    assert responses[10].status_code == 429


def test_password_reset_ip_limit_is_enforced(db_client):
    responses = [
        db_client.post(
            "/api/v1/auth/password/reset",
            json={"token": "x" * 32, "new_password": "new-valid-password-123"},
        )
        for _ in range(6)
    ]

    assert [response.status_code for response in responses[:5]] == [401] * 5
    assert responses[5].status_code == 429


def test_password_forgot_enforces_email_and_ip_buckets_and_ignores_forwarded_ip(db_client):
    email = f"same-person-{uuid4().hex}@example.com"
    first_responses = [
        db_client.post(
            "/api/v1/auth/password/forgot",
            json={"email": email.upper()},
            headers={"X-Forwarded-For": f"198.51.100.{index}"},
        )
        for index in range(1, 5)
    ]
    assert [response.status_code for response in first_responses] == [200, 200, 200, 429]

    # The email dimension is independent; varying emails and forged forwarding
    # headers cannot bypass the direct ASGI client IP bucket.
    other_responses = [
        db_client.post(
            "/api/v1/auth/password/forgot",
            json={"email": f"other-{index}-{uuid4().hex}@example.com"},
            headers={"X-Forwarded-For": f"203.0.113.{index}"},
        )
        for index in range(1, 8)
    ]
    assert [response.status_code for response in other_responses] == [
        200, 200, 200, 200, 200, 200, 429
    ]


def test_verification_resend_enforces_email_wide_limit(db_client):
    email = f"resend-{uuid4().hex}@example.com"
    responses = [
        db_client.post(
            "/api/v1/auth/email/verification/request", json={"email": email}
        )
        for _ in range(4)
    ]

    assert [response.status_code for response in responses] == [200, 200, 200, 429]


def test_refresh_limit_runs_after_csrf_and_origin_validation(db_client):
    email = f"refresh-limit-{uuid4().hex}@example.com"
    _register_and_verify(db_client, email)
    login = db_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "correct-horse-battery-42"},
        headers={"Origin": WEB_ORIGIN},
    )
    csrf = login.json()["csrf_token"]
    headers = {"Origin": WEB_ORIGIN, "X-CSRF-Token": csrf}
    responses = [
        db_client.post(
            "/api/v1/auth/refresh",
            headers={**headers, "Cookie": f"t2s_refresh=invalid; t2s_csrf={csrf}"},
        )
        for _ in range(31)
    ]

    assert [response.status_code for response in responses[:30]] == [401] * 30
    assert responses[30].status_code == 429


def test_password_change_limit_is_scoped_to_authenticated_user(db_client):
    email = f"change-limit-{uuid4().hex}@example.com"
    _register_and_verify(db_client, email)
    login = db_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "correct-horse-battery-42"},
        headers={"Origin": WEB_ORIGIN},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    responses = [
        db_client.post(
            "/api/v1/auth/password/change",
            json={
                "current_password": "wrong-password",
                "new_password": "new-valid-password-123",
            },
            headers=headers,
        )
        for _ in range(6)
    ]

    assert [response.status_code for response in responses[:5]] == [401] * 5
    assert responses[5].status_code == 429


def test_retry_after_is_cors_exposed(client):
    response = client.get("/api/v1/health", headers={"Origin": WEB_ORIGIN})

    assert response.status_code == 200
    assert "retry-after" in response.headers["access-control-expose-headers"].lower()
