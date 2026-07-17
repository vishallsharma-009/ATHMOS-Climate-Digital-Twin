import pytest

def test_dashboard_endpoint(client):
    # Tests that the dashboard responds or throws the expected 503 if model is uninitialized
    response = client.get("/dashboard")
    assert response.status_code in [200, 503]
    if response.status_code == 200:
        data = response.json()
        assert "imd_rainfall_mm" in data
        assert "tmax_c" in data

def test_forecast_endpoint(client):
    response = client.get("/forecast")
    assert response.status_code in [200, 503]
    if response.status_code == 200:
        data = response.json()
        assert "region" in data
        assert "forecast" in data
        assert isinstance(data["forecast"], list)

def test_regions_endpoint(client):
    response = client.get("/regions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_explain_endpoint(client):
    response = client.get("/explain")
    assert response.status_code in [200, 503]
    if response.status_code == 503:
        assert "Awaiting model training" in response.json()["message"]
