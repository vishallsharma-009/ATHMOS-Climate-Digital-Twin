from pydantic import BaseModel
from typing import List, Dict, Any

class DashboardResponse(BaseModel):
    region: str
    imd_rainfall_mm: float
    insat_rainfall_mm: float
    tmax_c: float
    tmin_c: float
    lst_c: float
    sst_c: float
    forecast_confidence_pct: float
    system_status: str

class ForecastDay(BaseModel):
    day: int
    imd_rainfall_mm: float
    insat_rainfall_mm: float
    tmax_c: float
    tmin_c: float
    lst_c: float
    sst_c: float

class ForecastResponse(BaseModel):
    region: str
    horizon_days: int
    forecast: List[ForecastDay]
    note: str

class ScenarioResponse(BaseModel):
    region: str
    applied_anomalies: Dict[str, float]
    forecast: List[ForecastDay]
    note: str

class ExplainResponse(BaseModel):
    region: str
    global_importance: Dict[str, float]
    local_explanation: Dict[str, Any]
    note: str
