def test_history_filters_by_year_range(client):
    resp = client.get("/history?start_year=2022&end_year=2023")
    body = resp.get_json()
    assert all(2022 <= r["year"] <= 2023 for r in body["records"])


def test_history_rejects_start_after_end(client):
    resp = client.get("/history?start_year=2024&end_year=2020")
    assert resp.status_code == 400
