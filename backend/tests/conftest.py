import pytest
from api import app
from auth.models import init_db
from watchlist.models import init_watchlist_table
import pandas as pd


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("config.DATABASE_PATH", str(tmp_path / "test.db"))
    init_db()
    init_watchlist_table()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def auth_header(client):
    client.post(
        "/auth/register",
        json={"username": "tester", "email": "t@x.com", "password": "secret123"},
    )
    resp = client.post(
        "/auth/login", json={"username": "tester", "password": "secret123"}
    )
    token = resp.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_raw_df():
    """15 months of synthetic data for 2 countries — enough for lag_12 to compute."""
    dates = pd.date_range("2020-01-01", periods=15, freq="MS")
    rows = []
    for country in ["Nepal", "Australia"]:
        for i, d in enumerate(dates):
            rows.append({"date": d, "country": country, "arrivals": 100 + i * 10})
    return pd.DataFrame(rows)