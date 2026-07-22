# tests/unit/test_auth_models.py
from auth.models import _hash_password, _verify_password


def test_correct_password_verifies():
    hashed = _hash_password("mypassword")
    assert _verify_password("mypassword", hashed)


def test_wrong_password_fails():
    hashed = _hash_password("mypassword")
    assert not _verify_password("wrong", hashed)


def test_hash_is_salted_differently_each_time():
    assert _hash_password("same") != _hash_password("same")
