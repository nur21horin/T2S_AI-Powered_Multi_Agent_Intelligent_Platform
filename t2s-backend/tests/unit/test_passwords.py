from app.security.passwords import (
    hash_password,
    password_hash_needs_rehash,
    verify_password,
)


def test_argon2id_hash_is_salted_and_verifiable():
    password = "a-long-test-password-42"
    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash.startswith("$argon2id$")
    assert first_hash != password
    assert first_hash != second_hash
    assert verify_password(password, first_hash)
    assert not verify_password("wrong-password", first_hash)


def test_malformed_password_hash_fails_closed():
    assert not verify_password("candidate", "not-an-argon2-hash")
    assert password_hash_needs_rehash("not-an-argon2-hash")
