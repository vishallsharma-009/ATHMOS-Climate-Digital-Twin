"""
Geospatial Service
Provides spatial data endpoints, specifically GeoJSON representations
of the analysis region and grid cells.
"""
import os
import json
import glob
from config import settings

def _get_geojson_dir():
    # settings.DATASETS_DIR is usually relative to the root or backend. 
    # Let's ensure it maps to the correct absolute path.
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # If DATASETS_DIR is "../datasets", this will resolve correctly from backend
    return os.path.abspath(os.path.join(base_dir, settings.DATASETS_DIR, "geojson"))

def list_regions():
    """
    Scans the geojson directory for .geojson files and returns their basenames as a list of available regions.
    """
    geojson_dir = _get_geojson_dir()
    if not os.path.exists(geojson_dir):
        return []
    
    files = glob.glob(os.path.join(geojson_dir, "*.geojson"))
    regions = [os.path.splitext(os.path.basename(f))[0] for f in files]
    return sorted(regions)

def get_region_geojson(region: str):
    """
    Returns a GeoJSON FeatureCollection for the requested region by reading the corresponding file.
    """
    if not isinstance(region, str) or not region:
        return {"error": f"Region '{region}' not found"}

    # Only allow exact, known region names (basenames of existing .geojson files).
    # This prevents directory traversal via crafted 'region' values such as
    # "../../etc/passwd".
    allowed_regions = list_regions()
    if region not in allowed_regions:
        return {"error": f"Region '{region}' not found"}

    # Defensive second layer: ensure the resolved path stays inside the
    # geojson directory even if region somehow passed the check above.
    geojson_dir = _get_geojson_dir()
    filepath = os.path.join(geojson_dir, f"{os.path.basename(region)}.geojson")
    base_dir = os.path.realpath(geojson_dir)
    resolved = os.path.realpath(filepath)
    if resolved != os.path.join(base_dir, f"{os.path.basename(region)}.geojson") \
            and not resolved.startswith(base_dir + os.sep):
        return {"error": f"Region '{region}' not found"}

    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"Failed to parse GeoJSON for region '{region}': {str(e)}"}

    return {"error": f"Region '{region}' not found"}
