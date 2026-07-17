import pytest
import numpy as np
import xarray as xr
from services.data_loader import MissingValueHandler, Normalizer, DataValidator

def test_missing_value_handler(dummy_dataset):
    # Introduce NaNs
    ds_with_nans = dummy_dataset.copy()
    ds_with_nans["imd_rainfall_mm"].values[0:2, 0, 0] = np.nan
    
    handler = MissingValueHandler(threshold=0.6, max_time_gap=3)
    cleaned_ds = handler(ds_with_nans)
    
    # Verify temporal interpolation filled the short gap
    assert not np.isnan(cleaned_ds["imd_rainfall_mm"].values[0:2, 0, 0]).any()

def test_data_validator(dummy_dataset):
    validator = DataValidator()
    
    # Introduce an out-of-bounds value
    ds_oob = dummy_dataset.copy()
    ds_oob["imd_rainfall_mm"].values[0, 0, 0] = 2000.0 # Upper bound is 1500
    
    validated = validator(ds_oob, "dummy_source")
    
    # Verify clipping
    assert validated["imd_rainfall_mm"].values[0, 0, 0] <= 1500.0

def test_normalizer(dummy_dataset):
    norm = Normalizer()
    normalized_ds = norm.fit_transform(dummy_dataset)
    
    # Verify mean is roughly 0 and std is roughly 1
    mean_val = float(normalized_ds["imd_rainfall_mm"].mean())
    assert abs(mean_val) < 1e-5
    
    # Verify inverse transform restores original data
    restored_ds = norm.inverse_transform(normalized_ds)
    np.testing.assert_allclose(
        dummy_dataset["imd_rainfall_mm"].values,
        restored_ds["imd_rainfall_mm"].values,
        rtol=1e-5, atol=1e-5
    )
