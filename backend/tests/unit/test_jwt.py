# tests/unit/test_jwt.py — auth/routes.py's hand-rolled JWT
from auth.routes import _create_token, _verify_token
import time


def test_valid_token_round_trips():
    token = _create_token({"user_id": 1, "exp": int(time.time()) + 3600}, "secret")
    assert _verify_token(token, "secret")["user_id"] == 1


def test_expired_token_rejected():
    token = _create_token({"user_id": 1, "exp": int(time.time()) - 10}, "secret")
    assert _verify_token(token, "secret") is None


def test_tampered_signature_rejected():
    token = _create_token({"user_id": 1, "exp": int(time.time()) + 3600}, "secret")
    header, body, sig = token.split(".")
    tampered = f"{header}.{body}.{sig[:-2]}xx"
    assert _verify_token(tampered, "secret") is None
