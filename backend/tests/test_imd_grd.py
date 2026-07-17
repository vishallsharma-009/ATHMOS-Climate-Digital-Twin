import os
import numpy as np
import xarray as xr
import pytest
from pathlib import Path

from services.data_loader import IMDLoader, DatasetConfig

@pytest.fixture
def mock_imd_grd_directory(tmp_path):
    """Creates dummy binary GRD files representing 2015 IMD rainfall (0.25 deg) and tmax (1.0 deg)."""
    imd_dir = tmp_path / "imd"
    rain_dir = imd_dir / "rainfall"
    tmax_dir = imd_dir / "tmax"
    rain_dir.mkdir(parents=True)
    tmax_dir.mkdir(parents=True)
    
    # 2015 has 365 days
    days = 365
    
    # 1. Rainfall: 129x135, missing=-999.0
    rain_shape = (days, 129, 135)
    rain_data = np.full(rain_shape, 10.0, dtype='float32')
    # Inject sentinel
    rain_data[0, 0, 0] = -999.0
    rain_file = rain_dir / "Rainfall_ind2015_rfp25.grd"
    rain_data.tofile(rain_file)
    
    # 2. TMax: 31x31, missing=99.9
    tmax_shape = (days, 31, 31)
    tmax_data = np.full(tmax_shape, 35.0, dtype='float32')
    # Inject sentinel
    tmax_data[0, 0, 0] = 99.9
    tmax_file = tmax_dir / "Maxtemp_MaxT_2015.GRD"
    tmax_data.tofile(tmax_file)
    
    return str(imd_dir)

def test_imd_grd_parser_and_alignment(mock_imd_grd_directory):
    config = DatasetConfig(name="imd", root_dir=mock_imd_grd_directory, file_pattern="**/*.*")
    loader = IMDLoader(config)
    
    ds = loader.load()
    
    # Check variables
    assert 'imd_rainfall_mm' in ds.data_vars
    assert 'tmax_c' in ds.data_vars
    
    # Check spatial alignment has occurred (TMax interpolated to Rainfall 129x135 grid)
    assert ds.sizes['lat'] == 129
    assert ds.sizes['lon'] == 135
    assert ds.sizes['time'] == 365
    
    # Verify sentinels converted to NaN
    rain_vals = ds['imd_rainfall_mm'].isel(time=0, lat=0, lon=0).values
    assert np.isnan(rain_vals)
    
    tmax_vals = ds['tmax_c'].isel(time=0, lat=0, lon=0).values
    assert np.isnan(tmax_vals)
    
    # Verify exact grid steps (0.25 deg for master grid)
    lats = ds['lat'].values
    assert np.isclose(lats[1] - lats[0], 0.25)
    assert np.isclose(lats[0], 6.5)
