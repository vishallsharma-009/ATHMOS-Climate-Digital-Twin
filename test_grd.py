import numpy as np
import xarray as xr
import pandas as pd
import re

def read_imd_grd(file_path):
    # Extract year and type from filename, e.g. "Rainfall_ind2015_rfp25.grd" or "Maxtemp_MaxT_2015.GRD"
    year_match = re.search(r'20\d\d', file_path)
    if not year_match:
        raise ValueError(f"Could not find year in {file_path}")
    year = int(year_match.group(0))
    
    file_lower = file_path.lower()
    if 'rainfall' in file_lower or 'rfp25' in file_lower:
        var_type = 'imd_rainfall_mm'
        lat_pts, lon_pts = 129, 135
        lat_min, lat_max = 6.5, 38.5
        lon_min, lon_max = 66.5, 100.0
    elif 'maxt' in file_lower or 'tmax' in file_lower:
        var_type = 'tmax_c'
        lat_pts, lon_pts = 31, 31
        lat_min, lat_max = 7.5, 37.5
        lon_min, lon_max = 67.5, 97.5
    elif 'mint' in file_lower or 'tmin' in file_lower:
        var_type = 'tmin_c'
        lat_pts, lon_pts = 31, 31
        lat_min, lat_max = 7.5, 37.5
        lon_min, lon_max = 67.5, 97.5
    else:
        raise ValueError(f"Unknown variable type in filename: {file_path}")

    is_leap = (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))
    days = 366 if is_leap else 365

    data = np.fromfile(file_path, dtype='float32')
    
    # Handle files that might have a few extra bytes/missing days by dynamically sizing if needed
    expected_size = days * lat_pts * lon_pts
    if data.size != expected_size:
        print(f"Warning: {file_path} size {data.size} does not match expected {expected_size}. Attempting dynamic resolution.")
        days = data.size // (lat_pts * lon_pts)

    data = data[:days * lat_pts * lon_pts].reshape(days, lat_pts, lon_pts)
    
    # Missing values in IMD are typically -99.9 or -999.0
    data = np.where(data < -90.0, np.nan, data)
    
    lats = np.linspace(lat_min, lat_max, lat_pts)
    lons = np.linspace(lon_min, lon_max, lon_pts)
    times = pd.date_range(f"{year}-01-01", periods=days, freq="D")
    
    ds = xr.Dataset(
        {var_type: (["time", "lat", "lon"], data)},
        coords={"time": times, "lat": lats, "lon": lons}
    )
    return ds

print("Reading Rainfall...")
ds_rain = read_imd_grd('datasets/imd/rainfall/Rainfall_ind2015_rfp25.grd')
print(ds_rain)

print("\nReading Max Temp...")
ds_tmax = read_imd_grd('datasets/imd/tmax/Maxtemp_MaxT_2015.GRD')
print(ds_tmax)
