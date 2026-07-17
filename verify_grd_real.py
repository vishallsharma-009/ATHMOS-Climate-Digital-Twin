import sys
import os
import numpy as np

# Add backend to path so we can import services
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.data_loader import IMDLoader, DatasetConfig

def verify_dataset(file_path):
    print(f"\n--- Verifying {file_path} ---")
    config = DatasetConfig(name="imd", root_dir="datasets/imd", file_pattern="**/*.*")
    loader = IMDLoader(config)
    
    try:
        ds = loader._read_grd(file_path)
    except Exception as e:
        print(f"Failed to load: {e}")
        return

    var_name = list(ds.data_vars)[0]
    data = ds[var_name]

    print(f"Variable: {var_name}")
    print(f"Shape: {data.shape}")
    
    # 4. Timestep count
    print(f"Timesteps (days): {ds.sizes['time']}")
    
    # 2 & 3. Lats and Lons
    lats = ds['lat'].values
    lons = ds['lon'].values
    print(f"Latitudes: {len(lats)} points, {lats[0]} to {lats[-1]}, step: {lats[1]-lats[0]:.2f}")
    print(f"Longitudes: {len(lons)} points, {lons[0]} to {lons[-1]}, step: {lons[1]-lons[0]:.2f}")
    
    # 5. Missing-value decoding & limits
    vals = data.values
    valid_vals = vals[~np.isnan(vals)]
    print(f"Valid pixels: {len(valid_vals)}")
    print(f"NaN pixels (sentinels): {np.isnan(vals).sum()}")
    
    if len(valid_vals) > 0:
        print(f"Min value: {valid_vals.min():.2f}")
        print(f"Max value: {valid_vals.max():.2f}")
        print(f"Mean value: {valid_vals.mean():.2f}")
    else:
        print("ALL VALUES ARE NAN!")

verify_dataset('datasets/imd/rainfall/Rainfall_ind2015_rfp25.grd')
verify_dataset('datasets/imd/tmax/Maxtemp_MaxT_2015.GRD')
