import pytest
from fastapi.testclient import TestClient
import numpy as np
import pandas as pd
import xarray as xr
from app import app

@pytest.fixture
def client():
    # Provide a standard FastAPI test client
    return TestClient(app, raise_server_exceptions=False)

@pytest.fixture
def mock_isro_vars():
    return ["imd_rainfall_mm", "tmax_c", "tmin_c", "lst_c", "sst_c", "insat_rainfall_mm"]

@pytest.fixture
def mock_climate_state(mock_isro_vars):
    # Generates a dummy climate state mapping similar to ingest_latest_state()
    state = {}
    for var in mock_isro_vars:
        # A simple 10x10 numpy array filled with a baseline value
        state[var] = np.full((10, 10), 25.0)
    return state

@pytest.fixture
def dummy_dataset():
    # Generates a synthetic xarray.Dataset matching the pipeline expectations
    times = pd.date_range("2024-01-01", periods=10, freq="D")
    lats = np.linspace(20, 24.5, 10)
    lons = np.linspace(68, 74.5, 10)
    
    ds = xr.Dataset(
        {
            "imd_rainfall_mm": (["time", "lat", "lon"], np.random.rand(10, 10, 10) * 10),
            "tmax_c": (["time", "lat", "lon"], np.random.rand(10, 10, 10) * 10 + 30),
            "tmin_c": (["time", "lat", "lon"], np.random.rand(10, 10, 10) * 10 + 20),
            "lst_c": (["time", "lat", "lon"], np.random.rand(10, 10, 10) * 15 + 25),
            "sst_c": (["time", "lat", "lon"], np.random.rand(10, 10, 10) * 5 + 28),
            "insat_rainfall_mm": (["time", "lat", "lon"], np.random.rand(10, 10, 10) * 5),
        },
        coords={
            "time": times,
            "lat": lats,
            "lon": lons,
        },
    )
    return ds
