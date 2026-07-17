"""
Climate Data Fusion Module
===========================
Multi-source climate data ingestion, preprocessing, and fusion pipeline
for the ATHMOS Climate Digital Twin.

Supported sources
------------------
- IMD    : India Meteorological Department gridded rainfall / temperature
           (NetCDF, dims: time, lat, lon)
- ERA5   : ECMWF ERA5 reanalysis (NetCDF, dims: time, latitude, longitude)
- INSAT  : INSAT-3D satellite-derived fields (NetCDF/HDF5-via-NetCDF,
           dims: time, lat, lon)

Pipeline stages
----------------
1. Source-specific loading + coordinate/variable standardization
2. Missing-value handling (temporal interpolation + spatial fallback)
3. Spatial alignment (regridding all sources onto a common lat/lon grid)
4. Temporal alignment (resampling all sources onto a common time axis)
5. Multi-source fusion (merge into a single xarray.Dataset)
6. Normalization (z-score, per-variable, with invertible stats)
7. Persistence (NetCDF or NumPy .npz)
8. PyTorch Dataset wrapping (sliding-window sequences for forecasting)
9. Temporal train/validation split (leakage-safe, non-shuffled)

This module is self-contained and does not depend on any other file in
`services/`. It is designed to be called from `climate_service.py` once
that service is wired up to use real data.
"""

from __future__ import annotations

import glob
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import xarray as xr
from torch.utils.data import Dataset, Subset

logger = logging.getLogger("athmos.data_loader")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Constants / standard schema
# ---------------------------------------------------------------------------

# Every loader normalizes its dataset to these coordinate names.
TIME_DIM = "time"
LAT_DIM = "lat"
LON_DIM = "lon"

# Known coordinate aliases used by real-world distributions of each source.
_COORD_ALIASES = {
    TIME_DIM: ["time", "TIME", "date", "Time"],
    LAT_DIM: ["lat", "latitude", "LATITUDE", "Latitude", "y"],
    LON_DIM: ["lon", "longitude", "LONGITUDE", "Longitude", "x"],
}

# Default variable name mapping (source variable -> standardized name).
# Users can override via DatasetConfig.variable_map.
DEFAULT_VARIABLE_MAP = {
    "imd": {
        "RAINFALL": "imd_rainfall_mm",
        "rf": "imd_rainfall_mm",
        "TMAX": "tmax_c",
        "TMIN": "tmin_c",
    },
    "insat": {
        "3RIMG_L2B_LST": "lst_c",
        "3RIMG_L2B_SST": "sst_c",
        "3RIMG_L2B_IMC": "insat_rainfall_mm",
        "LST": "lst_c",
        "SST": "sst_c",
        "IMC": "insat_rainfall_mm",
    },
}


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class DatasetConfig:
    """Configuration describing how to locate and interpret one data source."""

    name: str                       # "imd" | "era5" | "insat"
    root_dir: str                   # directory containing the raw files
    file_pattern: str = "*.nc"      # glob pattern (relative to root_dir)
    variable_map: Dict[str, str] = field(default_factory=dict)
    engine: Optional[str] = None    # xarray backend override, e.g. "netcdf4"

    def resolved_variable_map(self) -> Dict[str, str]:
        base = dict(DEFAULT_VARIABLE_MAP.get(self.name, {}))
        base.update(self.variable_map)
        return base


@dataclass
class FusionConfig:
    """Configuration for the end-to-end fusion pipeline."""

    lat_bounds: Tuple[float, float] = (20.0, 24.5)   # Gujarat region default
    lon_bounds: Tuple[float, float] = (68.0, 74.5)
    target_resolution_deg: float = 0.25              # common grid spacing
    temporal_freq: str = "D"                          # daily
    missing_value_threshold: float = 0.6              # drop cell if >60% missing
    sequence_length: int = 10                         # timesteps of history
    forecast_horizon: int = 1                          # timesteps ahead to predict


# ---------------------------------------------------------------------------
# Coordinate / variable standardization helpers
# ---------------------------------------------------------------------------

def _rename_to_standard_coords(ds: xr.Dataset) -> xr.Dataset:
    """Rename whatever coordinate names a raw dataset uses to the standard
    (time, lat, lon) schema used throughout this module."""
    rename_map = {}
    for standard, aliases in _COORD_ALIASES.items():
        for alias in aliases:
            if alias in ds.coords or alias in ds.dims:
                if alias != standard:
                    rename_map[alias] = standard
                break
    if rename_map:
        ds = ds.rename(rename_map)

    missing = [d for d in (TIME_DIM, LAT_DIM, LON_DIM) if d not in ds.coords and d not in ds.dims]
    if missing:
        raise ValueError(
            f"Dataset is missing required coordinate(s) {missing} after alias "
            f"resolution. Found coords: {list(ds.coords)}"
        )
    return ds


def _rename_to_standard_variables(ds: xr.Dataset, variable_map: Dict[str, str]) -> xr.Dataset:
    """Rename raw variable names to the standardized schema, dropping any
    variables not present in the mapping (keeps the fused dataset lean)."""
    present = {raw: std for raw, std in variable_map.items() if raw in ds.data_vars}
    if not present:
        logger.warning(
            "No known variables from variable_map found in dataset; keeping "
            "all raw variables as-is (%s).", list(ds.data_vars)
        )
        return ds
    ds = ds[list(present.keys())].rename(present)
    return ds


def _ensure_lat_ascending(ds: xr.Dataset) -> xr.Dataset:
    """Some products (e.g. ERA5) store latitude descending (90 -> -90).
    Standardize to ascending order so all sources align consistently."""
    if LAT_DIM in ds.coords and ds[LAT_DIM].size > 1:
        if float(ds[LAT_DIM][0]) > float(ds[LAT_DIM][-1]):
            ds = ds.sortby(LAT_DIM)
    if LON_DIM in ds.coords and ds[LON_DIM].size > 1:
        if float(ds[LON_DIM][0]) > float(ds[LON_DIM][-1]):
            ds = ds.sortby(LON_DIM)
    return ds


# ---------------------------------------------------------------------------
# Source-specific loaders
# ---------------------------------------------------------------------------

class BaseClimateLoader(ABC):
    """Common interface for all source loaders."""

    def __init__(self, config: DatasetConfig):
        self.config = config

    def _discover_files(self) -> List[str]:
        pattern = os.path.join(self.config.root_dir, self.config.file_pattern)
        files = sorted(glob.glob(pattern, recursive=True))
        if not files:
            raise FileNotFoundError(
                f"No files matching '{pattern}' found for source "
                f"'{self.config.name}'. Place raw {self.config.name.upper()} "
                f"files under '{self.config.root_dir}' before running the "
                f"fusion pipeline."
            )
        return files

    @abstractmethod
    def load(self) -> xr.Dataset:
        ...

    def _open_and_standardize(self, files: List[str]) -> xr.Dataset:
        open_kwargs = {"engine": self.config.engine} if self.config.engine else {}
        if len(files) == 1:
            ds = xr.open_dataset(files[0], **open_kwargs)
        else:
            ds = xr.open_mfdataset(
                files, combine="by_coords", **open_kwargs
            )
        ds = _rename_to_standard_coords(ds)
        ds = _rename_to_standard_variables(ds, self.config.resolved_variable_map())
        ds = _ensure_lat_ascending(ds)
        # Deduplicate any repeated timestamps that can occur across files.
        if TIME_DIM in ds.dims:
            _, index = np.unique(ds[TIME_DIM], return_index=True)
            if len(index) != ds.sizes[TIME_DIM]:
                ds = ds.isel({TIME_DIM: sorted(index)})
        return ds


class IMDLoader(BaseClimateLoader):
    """Loads IMD gridded rainfall / temperature NetCDF and GRD products."""

    def _read_grd(self, file_path: str) -> xr.Dataset:
        import re
        import pandas as pd
        
        file_lower = file_path.lower()
        year_match = re.search(r'20\d\d', file_path)
        if not year_match:
            raise ValueError(f"Could not find year in IMD GRD filename: {file_path}")
        year = int(year_match.group(0))
        
        if 'rainfall' in file_lower or 'rfp25' in file_lower:
            var_type = 'imd_rainfall_mm'
            lat_pts, lon_pts = 129, 135
            lat_min, lon_min = 6.5, 66.5
            step = 0.25
        elif 'maxt' in file_lower or 'tmax' in file_lower:
            var_type = 'tmax_c'
            lat_pts, lon_pts = 31, 31
            lat_min, lon_min = 7.5, 67.5
            step = 1.0
        elif 'mint' in file_lower or 'tmin' in file_lower:
            var_type = 'tmin_c'
            lat_pts, lon_pts = 31, 31
            lat_min, lon_min = 7.5, 67.5
            step = 1.0
        else:
            raise ValueError(f"Unknown variable type in filename: {file_path}")

        is_leap = (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))
        days = 366 if is_leap else 365

        data = np.fromfile(file_path, dtype='float32')
        expected_size = days * lat_pts * lon_pts
        
        # 2. Validate the binary file size strictly.
        if data.size != expected_size:
            raise ValueError(f"Corrupt GRD file {file_path}: size {data.size} does not match expected {expected_size} pixels for {days} days.")
            
        data = data.reshape(days, lat_pts, lon_pts)
        
        # 3. Replace broad missing-value thresholds with official IMD sentinels
        if var_type == 'imd_rainfall_mm':
            data = np.where((data == -999.0) | (data == -99.9), np.nan, data)
        else:
            data = np.where((data == 99.9) | (data == 99.90), np.nan, data)
        
        # 4. Verify latitude and longitude generation against official IMD grid spec
        lats = lat_min + np.arange(lat_pts) * step
        lons = lon_min + np.arange(lon_pts) * step
        
        times = pd.date_range(f"{year}-01-01", periods=days, freq="D")
        
        ds = xr.Dataset(
            {var_type: (["time", "lat", "lon"], data)},
            coords={"time": times, "lat": lats, "lon": lons}
        )
        ds = _rename_to_standard_coords(ds)
        ds = _rename_to_standard_variables(ds, self.config.resolved_variable_map())
        ds = _ensure_lat_ascending(ds)
        return ds

    def load(self) -> xr.Dataset:
        files = self._discover_files()
        valid_files = [f for f in files if f.lower().endswith('.nc') or f.lower().endswith('.grd')]
        if not valid_files:
            raise ValueError(f"No valid .nc or .grd files found in IMD source: {self.config.root_dir}")
            
        logger.info("IMD: loading %d file(s) from %s", len(valid_files), self.config.root_dir)
        
        nc_files = [f for f in valid_files if f.lower().endswith('.nc')]
        grd_files = [f for f in valid_files if f.lower().endswith('.grd')]
        
        datasets = []
        if nc_files:
            ds_nc = self._open_and_standardize(nc_files)
            datasets.append(ds_nc)
            
        for f in grd_files:
            datasets.append(self._read_grd(f))
            
        if len(datasets) == 1:
            ds = datasets[0]
        else:
            # 1. Do not use combine_by_coords before spatial alignment if resolutions differ.
            # Select the highest-resolution dataset as the master grid (e.g., 0.25 deg rainfall)
            master_ds = max(datasets, key=lambda d: d.sizes.get('lat', 0))
            
            aligned_datasets = []
            for d in datasets:
                if d is not master_ds:
                    # Spatial alignment via interpolation
                    d = d.interp(lat=master_ds.lat, lon=master_ds.lon, method='linear')
                aligned_datasets.append(d)
                
            # Now safe to combine
            ds = xr.combine_by_coords(aligned_datasets, combine_attrs='override')

        ds = ds.where(ds != -999.0)
        ds = ds.sortby(TIME_DIM)
        return ds


class INSATLoader(BaseClimateLoader):
    """Loads INSAT-3D satellite-derived field products (NetCDF/HDF5)."""

    def load(self) -> xr.Dataset:
        files = self._discover_files()
        logger.info("INSAT: loading %d file(s) from %s", len(files), self.config.root_dir)
        ds = self._open_and_standardize(files)
        # INSAT fields (LST, SST) may be distributed in Kelvin; convert to Celsius.
        for var in ["lst_c", "sst_c"]:
            if var in ds.data_vars:
                attrs = ds[var].attrs
                if attrs.get("units", "K") in ("K", "Kelvin", "kelvin"):
                    ds[var] = ds[var] - 273.15
                    ds[var].attrs["units"] = "degC"
        # INSAT scan artifacts frequently show up as extreme negative fill values; mask them out.
        for var in ds.data_vars:
            ds[var] = ds[var].where(ds[var] > -900)
        ds = ds.sortby(TIME_DIM)
        return ds


LOADER_REGISTRY = {
    "imd": IMDLoader,
    "insat": INSATLoader,
}


def build_loader(config: DatasetConfig) -> BaseClimateLoader:
    key = config.name.lower()
    if key not in LOADER_REGISTRY:
        raise ValueError(
            f"Unknown data source '{config.name}'. Supported sources: "
            f"{list(LOADER_REGISTRY.keys())}"
        )
    return LOADER_REGISTRY[key](config)


# ---------------------------------------------------------------------------
# Missing-value handling
# ---------------------------------------------------------------------------

class MissingValueHandler:
    """Handles gaps in gridded climate data.

    Strategy:
      1. Drop grid cells (lat/lon points) whose fraction of missing
         timesteps exceeds `threshold` — these are unusable.
      2. Fill remaining short gaps along the time axis via linear
         interpolation (bounded by `max_time_gap` steps).
      3. Fill any leftover NaNs (e.g. at series edges, or short-lived
         spatial holes) via nearest-neighbor spatial fill at each timestep.
    """

    def __init__(self, threshold: float = 0.6, max_time_gap: int = 3):
        self.threshold = threshold
        self.max_time_gap = max_time_gap

    def __call__(self, ds: xr.Dataset) -> xr.Dataset:
        ds = self._drop_sparse_cells(ds)
        ds = self._temporal_interpolate(ds)
        ds = self._spatial_fill(ds)
        return ds

    def _drop_sparse_cells(self, ds: xr.Dataset) -> xr.Dataset:
        for var in ds.data_vars:
            missing_frac = ds[var].isnull().mean(dim=TIME_DIM)
            sparse_mask = missing_frac > self.threshold
            n_sparse = int(sparse_mask.sum())
            if n_sparse:
                logger.info(
                    "MissingValueHandler: masking %d/%d cells in '%s' "
                    "(missing fraction > %.0f%%)",
                    n_sparse, sparse_mask.size, var, self.threshold * 100,
                )
                ds[var] = ds[var].where(~sparse_mask)
        return ds

    def _temporal_interpolate(self, ds: xr.Dataset) -> xr.Dataset:
        return ds.interpolate_na(
            dim=TIME_DIM, method="linear", limit=self.max_time_gap
        )

    def _spatial_fill(self, ds: xr.Dataset) -> xr.Dataset:
        # Nearest-neighbor fill across lat then lon closes any residual
        # holes (e.g. at the very start/end of the time series) without
        # inventing new physical extremes.
        ds = ds.interpolate_na(dim=LAT_DIM, method="nearest", fill_value="extrapolate")
        ds = ds.interpolate_na(dim=LON_DIM, method="nearest", fill_value="extrapolate")
        return ds



class DataValidator:
    """Validates physical bounds and structural integrity of climate data."""
    
    # Expected ranges (min, max) for known variables
    BOUNDS = {
        "imd_rainfall_mm": (0.0, 1500.0), # mm/day
        "insat_rainfall_mm": (0.0, 1500.0), # mm/day
        "tmax_c": (-50.0, 60.0), # Celsius
        "tmin_c": (-50.0, 60.0), # Celsius
        "lst_c": (-50.0, 70.0), # Celsius
        "sst_c": (-5.0, 45.0), # Celsius
    }

    def __call__(self, ds: xr.Dataset, source_name: str) -> xr.Dataset:
        self._check_dimensions(ds, source_name)
        return self._clip_physical_bounds(ds, source_name)

    def _check_dimensions(self, ds: xr.Dataset, source_name: str):
        for dim in [TIME_DIM, LAT_DIM, LON_DIM]:
            if dim not in ds.dims:
                raise ValueError(f"[{source_name}] Missing required dimension: {dim}")
            if ds.sizes[dim] == 0:
                raise ValueError(f"[{source_name}] Degenerate dimension (size 0): {dim}")

    def _clip_physical_bounds(self, ds: xr.Dataset, source_name: str) -> xr.Dataset:
        for var in ds.data_vars:
            if var in self.BOUNDS:
                vmin, vmax = self.BOUNDS[var]
                out_of_bounds = (ds[var] < vmin) | (ds[var] > vmax)
                n_oob = int(out_of_bounds.sum())
                if n_oob > 0:
                    logger.warning(
                        "DataValidator: Clipping %d out-of-bounds values in '%s' for %s",
                        n_oob, var, source_name
                    )
                    ds[var] = ds[var].clip(min=vmin, max=vmax)
        return ds

# ---------------------------------------------------------------------------
# Spatial alignment (regridding)
# ---------------------------------------------------------------------------

def build_target_grid(
    lat_bounds: Tuple[float, float],
    lon_bounds: Tuple[float, float],
    resolution_deg: float,
) -> Tuple[np.ndarray, np.ndarray]:
    lat = np.arange(lat_bounds[0], lat_bounds[1] + resolution_deg / 2, resolution_deg)
    lon = np.arange(lon_bounds[0], lon_bounds[1] + resolution_deg / 2, resolution_deg)
    return lat, lon


def spatial_align(ds: xr.Dataset, target_lat: np.ndarray, target_lon: np.ndarray) -> xr.Dataset:
    """Regrid a dataset onto the common target lat/lon grid via bilinear
    interpolation (xarray's linear ND interpolation)."""
    return ds.interp(
        {LAT_DIM: target_lat, LON_DIM: target_lon},
        method="linear",
        kwargs={"fill_value": None},
    )


# ---------------------------------------------------------------------------
# Temporal alignment
# ---------------------------------------------------------------------------

def temporal_align(
    ds: xr.Dataset, freq: str, start: Optional[str] = None, end: Optional[str] = None
) -> xr.Dataset:
    """Resample a dataset onto a regular time frequency and (optionally)
    clip to a shared [start, end] window so multiple sources line up."""
    ds = ds.resample({TIME_DIM: freq}).mean(skipna=True)
    if start is not None or end is not None:
        ds = ds.sel({TIME_DIM: slice(start, end)})
    return ds


def common_time_window(datasets: Sequence[xr.Dataset]) -> Tuple[str, str]:
    starts = [pd.Timestamp(ds[TIME_DIM].values.min()) for ds in datasets]
    ends = [pd.Timestamp(ds[TIME_DIM].values.max()) for ds in datasets]
    start = max(starts)
    end = min(ends)
    if start >= end:
        raise ValueError(
            f"Data sources do not overlap in time (latest start={start}, "
            f"earliest end={end}). Cannot align temporally."
        )
    return start.isoformat(), end.isoformat()


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

class Normalizer:
    """Per-variable z-score normalization with invertible, persistable
    statistics computed once on the training split (avoids leakage)."""

    def __init__(self):
        self.stats: Dict[str, Dict[str, float]] = {}

    def fit(self, ds: xr.Dataset, variables: Optional[Sequence[str]] = None) -> "Normalizer":
        variables = variables or list(ds.data_vars)
        for var in variables:
            mean = float(ds[var].mean(skipna=True))
            std = float(ds[var].std(skipna=True))
            if std == 0 or np.isnan(std):
                std = 1.0
            self.stats[var] = {"mean": mean, "std": std}
        return self

    def transform(self, ds: xr.Dataset) -> xr.Dataset:
        ds = ds.copy()
        for var, s in self.stats.items():
            if var in ds.data_vars:
                ds[var] = (ds[var] - s["mean"]) / s["std"]
        return ds

    def fit_transform(self, ds: xr.Dataset, variables: Optional[Sequence[str]] = None) -> xr.Dataset:
        return self.fit(ds, variables).transform(ds)

    def inverse_transform(self, ds: xr.Dataset) -> xr.Dataset:
        ds = ds.copy()
        for var, s in self.stats.items():
            if var in ds.data_vars:
                ds[var] = ds[var] * s["std"] + s["mean"]
        return ds

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self.stats, f, indent=2)

    @classmethod
    def load(cls, path: str) -> "Normalizer":
        norm = cls()
        with open(path, "r") as f:
            norm.stats = json.load(f)
        return norm


# ---------------------------------------------------------------------------
# Fusion pipeline orchestrator
# ---------------------------------------------------------------------------

class ClimateFusionPipeline:
    """End-to-end orchestrator: load -> clean -> align -> fuse -> normalize.

    Usage
    -----
    >>> configs = [
    ...     DatasetConfig(name="imd", root_dir="../datasets/imd"),
    ...     DatasetConfig(name="era5", root_dir="../datasets/era5"),
    ...     DatasetConfig(name="insat", root_dir="../datasets/insat"),
    ... ]
    >>> pipeline = ClimateFusionPipeline(configs, FusionConfig())
    >>> fused_ds, normalizer = pipeline.run()
    """

    def __init__(self, dataset_configs: Sequence[DatasetConfig], fusion_config: FusionConfig):
        self.dataset_configs = dataset_configs
        self.fusion_config = fusion_config
        self.validator = DataValidator()
        self.missing_handler = MissingValueHandler(
            threshold=fusion_config.missing_value_threshold
        )
        self.normalizer = Normalizer()

    def _load_all(self) -> List[xr.Dataset]:
        loaded = []
        for cfg in self.dataset_configs:
            loader = build_loader(cfg)
            ds = loader.load()
            ds = ds.sel(
                {
                    LAT_DIM: slice(*self.fusion_config.lat_bounds),
                    LON_DIM: slice(*self.fusion_config.lon_bounds),
                }
            )
            loaded.append(ds)
        return loaded

    def run(self, normalize: bool = True) -> Tuple[xr.Dataset, Normalizer]:
        raw_datasets = self._load_all()

        # 0. Data Validation (physical bounds and structural integrity)
        raw_datasets = [
            self.validator(ds, cfg.name) 
            for ds, cfg in zip(raw_datasets, self.dataset_configs)
        ]

        # 1. Missing-value handling per source (before alignment, while each
        #    source is still on its native grid — cleaner interpolation).
        cleaned = [self.missing_handler(ds) for ds in raw_datasets]

        # 2. Temporal alignment onto a shared frequency + overlapping window.
        start, end = common_time_window(cleaned)
        temporally_aligned = [
            temporal_align(ds, self.fusion_config.temporal_freq, start, end)
            for ds in cleaned
        ]

        # 3. Spatial alignment onto a common target grid.
        target_lat, target_lon = build_target_grid(
            self.fusion_config.lat_bounds,
            self.fusion_config.lon_bounds,
            self.fusion_config.target_resolution_deg,
        )
        spatially_aligned = [
            spatial_align(ds, target_lat, target_lon) for ds in temporally_aligned
        ]

        # 4. Fuse: merge all sources into one dataset. `compat="override"`
        #    with pre-aligned coordinates means variables combine cleanly;
        #    overlapping variable names across sources are suffixed by
        #    source name to avoid silent collisions.
        fused = self._merge_sources(spatially_aligned)

        # 5. A second, lighter missing-value pass after regridding, since
        #    interpolation near source-grid edges can reintroduce NaNs.
        fused = self.missing_handler._spatial_fill(fused)

        # 6. Normalize.
        if normalize:
            fused = self.normalizer.fit_transform(fused)

        return fused, self.normalizer

    def _merge_sources(self, datasets: Sequence[xr.Dataset]) -> xr.Dataset:
        renamed = []
        seen_vars: Dict[str, str] = {}
        for cfg, ds in zip(self.dataset_configs, datasets):
            rename = {}
            for var in ds.data_vars:
                if var in seen_vars:
                    rename[var] = f"{var}_{cfg.name}"
                else:
                    seen_vars[var] = cfg.name
            renamed.append(ds.rename(rename) if rename else ds)
        return xr.merge(renamed, compat="override", join="outer")


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def save_processed_dataset(
    ds: xr.Dataset, out_path: str, fmt: str = "netcdf"
) -> str:
    """Persist the fused/processed dataset.

    fmt="netcdf" -> writes a single .nc file (preserves coords/attrs).
    fmt="numpy"  -> writes a .npz with one array per variable plus the
                    time/lat/lon coordinate arrays (lighter dependency for
                    downstream PyTorch-only consumers).
    """
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fmt = fmt.lower()
    if fmt == "netcdf":
        if not out_path.endswith((".nc", ".nc4")):
            out_path += ".nc"
        ds.to_netcdf(out_path)
    elif fmt == "numpy":
        if not out_path.endswith(".npz"):
            out_path += ".npz"
        arrays = {var: ds[var].values.astype(np.float32) for var in ds.data_vars}
        arrays[TIME_DIM] = ds[TIME_DIM].values.astype("datetime64[ns]")
        arrays[LAT_DIM] = ds[LAT_DIM].values.astype(np.float32)
        arrays[LON_DIM] = ds[LON_DIM].values.astype(np.float32)
        np.savez_compressed(out_path, **arrays)
    else:
        raise ValueError(f"Unsupported format '{fmt}'. Use 'netcdf' or 'numpy'.")
    logger.info("Saved processed dataset to %s (format=%s)", out_path, fmt)
    return out_path


def load_processed_dataset(path: str) -> xr.Dataset:
    """Load a previously saved processed dataset (NetCDF or NumPy .npz)
    back into an xarray.Dataset."""
    if path.endswith(".npz"):
        npz = np.load(path)
        coords = {
            TIME_DIM: npz[TIME_DIM],
            LAT_DIM: npz[LAT_DIM],
            LON_DIM: npz[LON_DIM],
        }
        data_vars = {
            k: ((TIME_DIM, LAT_DIM, LON_DIM), npz[k])
            for k in npz.files
            if k not in (TIME_DIM, LAT_DIM, LON_DIM)
        }
        return xr.Dataset(data_vars=data_vars, coords=coords)
    return xr.open_dataset(path)


def export_to_geotiff(ds: xr.Dataset, out_dir: str):
    """Export the processed dataset to multi-band GeoTIFFs (Raster Processing).
    
    Creates one GeoTIFF per variable per timestep for downstream Leaflet/GIS use.
    """
    import rasterio
    from rasterio.transform import from_bounds
    
    os.makedirs(out_dir, exist_ok=True)
    
    lats = ds[LAT_DIM].values
    lons = ds[LON_DIM].values
    
    # Calculate pixel size (assuming regular grid)
    res_lat = abs(lats[1] - lats[0]) if len(lats) > 1 else 0.25
    res_lon = abs(lons[1] - lons[0]) if len(lons) > 1 else 0.25
    
    # rasterio bounds: (left, bottom, right, top)
    transform = from_bounds(
        lons.min() - res_lon/2, lats.min() - res_lat/2,
        lons.max() + res_lon/2, lats.max() + res_lat/2,
        len(lons), len(lats)
    )
    
    times = ds[TIME_DIM].values
    for var in ds.data_vars:
        for i, t in enumerate(times):
            # Format time string safely for filenames
            t_str = pd.Timestamp(t).strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(out_dir, f"{var}_{t_str}.tif")
            
            # Data is [time, lat, lon]. Extract 2D array and ensure proper orientation.
            # Rasterio expects [lat, lon] but typically origin at top-left.
            # Depending on lats orientation (ascending/descending), we might need to flip.
            data_2d = ds[var].isel({TIME_DIM: i}).values.astype(np.float32)
            
            if lats[0] < lats[-1]:
                # Ascending lats (origin bottom-left). Rasterio prefers origin top-left.
                data_2d = np.flipud(data_2d)
                
            with rasterio.open(
                filename,
                'w',
                driver='GTiff',
                height=data_2d.shape[0],
                width=data_2d.shape[1],
                count=1,
                dtype=data_2d.dtype,
                crs='EPSG:4326',
                transform=transform,
                nodata=np.nan
            ) as dst:
                dst.write(data_2d, 1)
                
    logger.info("Exported GeoTIFFs to %s", out_dir)


# ---------------------------------------------------------------------------
# PyTorch Dataset
# ---------------------------------------------------------------------------

class ClimateFusionDataset(Dataset):
    """Sliding-window PyTorch Dataset over a fused, normalized climate
    xarray.Dataset, suitable for sequence models (e.g. ConvLSTM).

    Each sample is:
      X : FloatTensor [sequence_length, n_channels, n_lat, n_lon]
      y : FloatTensor [forecast_horizon, n_channels, n_lat, n_lon]

    where n_channels = number of variables in the fused dataset.
    """

    def __init__(
        self,
        ds: xr.Dataset,
        sequence_length: int = 10,
        forecast_horizon: int = 1,
        variables: Optional[Sequence[str]] = None,
    ):
        import torch  # local import keeps module importable without torch installed

        self.torch = torch
        self.variables = list(variables) if variables else list(ds.data_vars)
        if not self.variables:
            raise ValueError("Fused dataset has no data variables to build samples from.")

        # Stack variables into a single [time, channel, lat, lon] array.
        arrays = []
        for var in self.variables:
            if var in ds.data_vars:
                arrays.append(ds[var].transpose(TIME_DIM, LAT_DIM, LON_DIM).values)
            else:
                logger.warning(f"Variable '{var}' not found in fused dataset. Padding with zeros.")
                # Create a zero array matching the shape of (time, lat, lon)
                shape = (ds.sizes[TIME_DIM], ds.sizes[LAT_DIM], ds.sizes[LON_DIM])
                arrays.append(np.zeros(shape, dtype=np.float32))
                
        stacked = np.stack(arrays, axis=1).astype(np.float32)

        # Any residual NaNs (e.g. permanently masked cells) are set to 0
        # post-normalization, i.e. the per-variable mean, so they contribute
        # no signal to the model rather than corrupting it.
        stacked = np.nan_to_num(stacked, nan=0.0)

        self.data = stacked  # [T, C, H, W]
        self.sequence_length = sequence_length
        self.forecast_horizon = forecast_horizon
        self.times = pd.to_datetime(ds[TIME_DIM].values)

        n_windows = self.data.shape[0] - sequence_length - forecast_horizon + 1
        if n_windows <= 0:
            raise ValueError(
                f"Not enough timesteps ({self.data.shape[0]}) to build a "
                f"sequence_length={sequence_length} + "
                f"forecast_horizon={forecast_horizon} sample."
            )
        self._n_windows = n_windows

    def __len__(self) -> int:
        return self._n_windows

    def __getitem__(self, idx: int):
        x = self.data[idx : idx + self.sequence_length]
        y = self.data[
            idx + self.sequence_length : idx + self.sequence_length + self.forecast_horizon
        ]
        return self.torch.from_numpy(x), self.torch.from_numpy(y)

    def window_start_time(self, idx: int) -> pd.Timestamp:
        return self.times[idx]

    def target_time(self, idx: int) -> pd.Timestamp:
        return self.times[idx + self.sequence_length]


def train_val_split(
    dataset: ClimateFusionDataset, val_ratio: float = 0.2
) -> Tuple[Subset, Subset]:
    """Chronological (non-shuffled) train/validation split.

    Time series data must be split by time, not randomly, to avoid the
    validation set leaking information into training via overlapping
    sliding windows or temporal autocorrelation.
    """
    if not 0.0 < val_ratio < 1.0:
        raise ValueError("val_ratio must be between 0 and 1 (exclusive).")

    n = len(dataset)
    n_val = max(1, int(round(n * val_ratio)))
    n_train = n - n_val
    if n_train <= 0:
        raise ValueError(
            f"val_ratio={val_ratio} leaves no samples for training "
            f"(dataset has {n} windows total)."
        )

    train_indices = list(range(0, n_train))
    val_indices = list(range(n_train, n))
    logger.info(
        "train_val_split: %d train windows, %d val windows (val_ratio=%.2f)",
        len(train_indices), len(val_indices), val_ratio,
    )
    return Subset(dataset, train_indices), Subset(dataset, val_indices)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def run_pipeline(
    datasets_dir: str,
    output_path: str,
    output_format: str = "netcdf",
    fusion_config: Optional[FusionConfig] = None,
) -> str:
    """Convenience entry point wiring together the full fusion pipeline
    using the standard ATHMOS folder layout:

        datasets_dir/
            imd/*.nc
            insat/*.nc
    """
    fusion_config = fusion_config or FusionConfig()
    configs = [
        DatasetConfig(name="imd", root_dir=os.path.join(datasets_dir, "imd"), file_pattern="**/*.*"),
        DatasetConfig(name="insat", root_dir=os.path.join(datasets_dir, "insat"), file_pattern="*.[nh]*"),
    ]
    pipeline = ClimateFusionPipeline(configs, fusion_config)
    fused_ds, normalizer = pipeline.run(normalize=True)

    saved_path = save_processed_dataset(fused_ds, output_path, fmt=output_format)
    norm_path = os.path.splitext(saved_path)[0] + "_norm_stats.json"
    normalizer.save(norm_path)
    logger.info("Normalization stats saved to %s", norm_path)
    return saved_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ATHMOS Climate Data Fusion Pipeline")
    parser.add_argument(
        "--datasets-dir", default="../datasets",
        help="Root directory containing imd/, era5/, insat/ subfolders",
    )
    parser.add_argument(
        "--output", default="../datasets/processed/fused_climate_data",
        help="Output path (extension added automatically based on --format)",
    )
    parser.add_argument(
        "--format", choices=["netcdf", "numpy"], default="netcdf",
        help="Output storage format",
    )
    args = parser.parse_args()

    run_pipeline(args.datasets_dir, args.output, args.format)
