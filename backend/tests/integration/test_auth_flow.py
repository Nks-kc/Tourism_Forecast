# tests/integration/test_auth_flow.py
import pytest
from api import app
from auth.models import init_db


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("config.DATABASE_PATH", str(tmp_path / "test.db"))
    init_db()
    app.config["TESTING"] = True
    return app.test_client()


def test_register_then_login_then_access_protected_route(client):
    client.post(
        "/auth/register",
        json={"username": "alice", "email": "a@x.com", "password": "secret123"},
    )
    resp = client.post(
        "/auth/login", json={"username": "alice", "password": "secret123"}
    )
    token = resp.get_json()["token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.get_json()["username"] == "alice"


def test_protected_route_without_token_returns_401(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_duplicate_username_returns_409(client):
    client.post(
        "/auth/register",
        json={"username": "bob", "email": "b@x.com", "password": "secret123"},
    )
    resp = client.post(
        "/auth/register",
        json={"username": "bob", "email": "b2@x.com", "password": "secret123"},
    )
    assert resp.status_code == 409

def test_duplicate_email_returns_409(client):
    client.post(
        "/auth/register",
        json={"username": "erin1", "email": "erin@x.com", "password": "secret123"},
    )
    resp = client.post(
        "/auth/register",
        json={"username": "erin2", "email": "erin@x.com", "password": "secret123"},
    )
    assert resp.status_code == 409


def test_registration_still_works_after_a_failed_attempt(client):
    """Regression test for the connection-leak bug: a failed create_user() call
    used to leave its SQLite connection open, locking out the next attempt."""
    client.post(
        "/auth/register",
        json={"username": "frank", "email": "frank@x.com", "password": "secret123"},
    )
    client.post(
        "/auth/register",
        json={"username": "frank", "email": "frank2@x.com", "password": "secret123"},
    )
    resp = client.post(
        "/auth/register",
        json={"username": "george", "email": "george@x.com", "password": "secret123"},
    )
    assert resp.status_code == 201