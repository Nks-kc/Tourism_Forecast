def test_predict_requires_valid_horizon(client, auth_header):
    resp = client.post("/predict", json={"horizon": 5}, headers=auth_header)
    assert resp.status_code == 400


def test_predict_with_country_field_does_not_500(client, auth_header):
    resp = client.post(
        "/predict", json={"horizon": 3, "country": "Australia"}, headers=auth_header
    )
    assert resp.status_code != 500


def test_predict_country_returns_all_four_models(client, auth_header):
    resp = client.post(
        "/predict/country",
        json={"country": "Australia", "horizon": 3},
        headers=auth_header,
    )
    assert resp.status_code == 200
    data = resp.get_json()["predictions"]
    assert set(data.keys()) <= {"MLP", "Linear Regression", "SARIMA", "Holt-Winters"}
    assert len(data) > 0
    for model_name, result in data.items():
        assert len(result["arrivals"]) == 3
        assert len(result["months"]) == 3
