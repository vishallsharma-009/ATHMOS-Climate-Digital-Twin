"""
ATHMOS Climate Digital Twin - FastAPI Backend Entry Point
Returns dummy JSON responses. No ML logic implemented yet.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from config import settings
from schemas.climate import DashboardResponse, ForecastResponse, ScenarioResponse, ExplainResponse
from services.digital_twin import DigitalTwin

logger = logging.getLogger("athmos.api")
app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = str(exc)
    if isinstance(exc, RuntimeError) and any(kw in error_msg for kw in ["ISRO datasets", "Awaiting model training", "not configured", "not initialized", "Normalizer"]):
        logger.warning(f"Service unavailable: {exc}")
        return JSONResponse(
            status_code=503,
            content={"message": str(exc)},
        )
    logger.error(f"Unhandled API exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error. Please contact the administrator."},
    )

# Initialize singleton Digital Twin
dt = DigitalTwin()

@app.get("/")
def root():
    return {"message": "ATHMOS Climate Digital Twin API", "status": "running"}

@app.get("/dashboard", response_model=DashboardResponse)
def dashboard():
    return dt.get_dashboard_metrics()

@app.get("/regions")
def get_regions():
    from services.geo_service import list_regions
    return list_regions()

@app.get("/geojson")
def geojson(region: str = "gujarat"):
    from services.geo_service import get_region_geojson
    return get_region_geojson(region)

@app.get("/forecast", response_model=ForecastResponse)
def forecast():
    timeline = dt.generate_timeline(horizon=7)
    return {
        "region": "Gujarat",
        "horizon_days": 7,
        "forecast": timeline,
        "note": "Digital Twin forecast timeline",
    }

@app.get("/scenario", response_model=ScenarioResponse)
def scenario(temp_anomaly: float = 0.0, rain_anomaly: float = 0.0):
    dt.scenario_engine.clear_scenarios()
    
    if temp_anomaly != 0.0:
        dt.scenario_engine.add_anomaly("tmax_c", temp_anomaly)
    if rain_anomaly != 0.0:
        dt.scenario_engine.add_anomaly("imd_rainfall_mm", rain_anomaly)
        dt.scenario_engine.add_anomaly("insat_rainfall_mm", rain_anomaly)
        
    divergent_timeline = dt.generate_timeline(horizon=7)
    
    return {
        "region": "Gujarat",
        "applied_anomalies": {
            "temperature_change_c": temp_anomaly,
            "rainfall_change_mm": rain_anomaly
        },
        "forecast": divergent_timeline,
        "note": "Divergent timeline simulated via Scenario Engine",
    }

@app.get("/explain", response_model=ExplainResponse)
def explain():
    # Calling get_explainability dynamically triggers SHAP and returns the struct
    # If the model is not initialized, it will raise RuntimeError (caught by 503 handler)
    res = dt.get_explainability(lat_idx=0, lon_idx=0)
    
    return {
        "region": "Gujarat",
        "global_importance": res["global_importance"],
        "local_explanation": res["local_explanation"],
        "note": "SHAP feature importance calculated live from ConvLSTM"
    }

# Initialization of Models
try:
    import os
    import torch
    from services.model.predictor import ClimatePredictor
    
    model_path = os.path.join(os.path.dirname(__file__), "services", "model", "checkpoints", "model.pt")
    
    # Official ISRO variables in order
    isro_vars = ["imd_rainfall_mm", "tmax_c", "tmin_c", "lst_c", "sst_c", "insat_rainfall_mm"]
    
    if not os.path.exists(model_path):
        logger.warning(f"Model file not found at {model_path}.")
        datasets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datasets")
        if os.path.exists(datasets_dir) and (os.path.exists(os.path.join(datasets_dir, "imd")) or os.path.exists(os.path.join(datasets_dir, "insat"))):
            logger.info(f"Official datasets detected in {datasets_dir}. Starting Data Fusion Pipeline...")
            from services.data_loader import run_pipeline, load_processed_dataset, ClimateFusionDataset
            from services.model.trainer import ClimateModelTrainer
            
            output_tensor_path = os.path.join(os.path.dirname(__file__), "services", "fused_tensor.npz")
            run_pipeline(datasets_dir, output_tensor_path, output_format="numpy")
            
            logger.info("Starting ConvLSTM Training Pipeline...")
            fused_ds = load_processed_dataset(output_tensor_path)
            dataset = ClimateFusionDataset(fused_ds, sequence_length=10, forecast_horizon=7, variables=isro_vars)
            
            # Since we only have one dataset for pilot, split it to train/val
            from services.data_loader import train_val_split
            train_ds, val_ds = train_val_split(dataset, val_ratio=0.2)
            
            # Instantiate the actual model
            from services.model.convlstm import ConvLSTM
            model = ConvLSTM(input_dim=len(isro_vars), hidden_dims=[32, 16])
            
            trainer = ClimateModelTrainer(model, checkpoint_dir=os.path.dirname(model_path))
            trainer.fit(train_ds, val_ds, epochs=1, batch_size=2)
            
            # Save the final model as model.pt (in addition to the best_model.pt saved by trainer)
            torch.save({'model_state_dict': model.state_dict()}, model_path)
            
            # Load the latest sequence from real data into the Digital Twin
            last_seq, _ = dataset[len(dataset) - 1]
            # Convert to dictionary of arrays (shape: [1, H, W]) for the latest timestep
            state_dict = {}
            for i, var_name in enumerate(isro_vars):
                state_dict[var_name] = last_seq[-1, i].numpy()[np.newaxis, ...] # Extract the last step of the sequence
            dt.ingest_latest_state(state_dict)
            logger.info("Digital Twin ingested real recent climate state.")
        else:
            logger.warning("No datasets found in ../datasets. Predictor and Explainer remain offline.")

    if os.path.exists(model_path):
        # 1. Initialize Predictor
        # We need to know spatial dimension (H, W). Using 10x10 as default for pilot.
        dt.predictor = ClimatePredictor(
            model_path=model_path, 
            input_dim=len(isro_vars), 
            hidden_dims=[32, 16], 
            variables_list=isro_vars
        )
        
        # 2. Initialize SHAP Explainer
        try:
            from services.explainability import ShapExplainer
            background_tensor = torch.zeros((1, 1, len(isro_vars), 10, 10)).float()
            dt.explainer = ShapExplainer(dt.predictor.model, background_tensor, device=dt.predictor.device)
            logger.info("Successfully bound Predictor and ShapExplainer to Digital Twin.")
        except Exception as explainer_e:
            logger.warning(f"Failed to initialize ShapExplainer (Explainability offline): {explainer_e}")
            
        # 3. Load latest state from fused_tensor.npz
        try:
            import numpy as np
            from services.data_loader import load_processed_dataset, ClimateFusionDataset
            output_tensor_path = os.path.join(os.path.dirname(__file__), "services", "fused_tensor.npz")
            if os.path.exists(output_tensor_path):
                fused_ds = load_processed_dataset(output_tensor_path)
                dataset = ClimateFusionDataset(fused_ds, sequence_length=10, forecast_horizon=7, variables=isro_vars)
                last_seq, _ = dataset[len(dataset) - 1]
                state_dict = {}
                for i, var_name in enumerate(isro_vars):
                    state_dict[var_name] = last_seq[-1, i].numpy()[np.newaxis, ...]
                dt.ingest_latest_state(state_dict)
                logger.info("Successfully loaded current state from fused_tensor.npz for Digital Twin.")
        except Exception as state_e:
            logger.warning(f"Failed to load current state from fused_tensor.npz: {state_e}")
        
except Exception as e:
    logger.error(f"Failed during model initialization: {e}")

# Load the Normalizer once at startup. Architecture: the DigitalTwin is the
# single owner of inverse normalization at the API edge. The stats are produced
# by the fusion pipeline (run_pipeline -> *_norm_stats.json).
# NOTE: if the stats are missing we do NOT fall back — the /dashboard and
# /forecast endpoints will fail with a clear RuntimeError (mapped to 503)
# rather than serving normalized values as if they were physical °C / mm.
try:
    import os
    from services.data_loader import Normalizer
    _norm_stats_path = os.path.join(os.path.dirname(__file__), "services", "fused_tensor_norm_stats.json")
    if os.path.exists(_norm_stats_path):
        dt.normalizer = Normalizer.load(_norm_stats_path)
        logger.info("Normalizer loaded from %s.", _norm_stats_path)
    else:
        logger.error(
            "Normalizer stats NOT found at %s. The /dashboard and /forecast "
            "endpoints will fail until the fusion pipeline has run (run_pipeline).",
            _norm_stats_path,
        )
except Exception as _norm_e:
    logger.error("Failed to load Normalizer: %s", _norm_e)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
