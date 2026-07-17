import os
import numpy as np
import pandas as pd
import xarray as xr

def create_synthetic_datasets():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    imd_dir = os.path.join(base_dir, "datasets", "imd")
    insat_dir = os.path.join(base_dir, "datasets", "insat")
    
    os.makedirs(imd_dir, exist_ok=True)
    os.makedirs(insat_dir, exist_ok=True)

    times = pd.date_range("2024-01-01", periods=20, freq="D")
    lats = np.linspace(20, 24.5, 20)
    lons = np.linspace(68, 74.5, 20)

    # 1. Create IMD Dataset
    imd_ds = xr.Dataset(
        {
            "RAINFALL": (["time", "lat", "lon"], np.random.rand(20, 20, 20) * 10),
            "TMAX": (["time", "lat", "lon"], np.random.rand(20, 20, 20) * 10 + 30),
            "TMIN": (["time", "lat", "lon"], np.random.rand(20, 20, 20) * 10 + 20),
        },
        coords={"time": times, "lat": lats, "lon": lons}
    )
    imd_ds.to_netcdf(os.path.join(imd_dir, "imd_synthetic_2024.nc"))
    
    # 2. Create INSAT Dataset
    insat_ds = xr.Dataset(
        {
            "3RIMG_L2B_LST": (["time", "lat", "lon"], np.random.rand(20, 20, 20) * 15 + 25 + 273.15), # Kelvin
            "3RIMG_L2B_SST": (["time", "lat", "lon"], np.random.rand(20, 20, 20) * 5 + 28 + 273.15), # Kelvin
            "3RIMG_L2B_IMC": (["time", "lat", "lon"], np.random.rand(20, 20, 20) * 5),
        },
        coords={"time": times, "lat": lats, "lon": lons}
    )
    insat_ds.to_netcdf(os.path.join(insat_dir, "insat_synthetic_2024.nc"))

if __name__ == "__main__":
    create_synthetic_datasets()
    print("Synthetic datasets generated.")
