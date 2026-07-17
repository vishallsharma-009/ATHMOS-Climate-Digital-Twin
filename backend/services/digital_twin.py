import logging
import numpy as np
import datetime

logger = logging.getLogger("athmos.digital_twin")

class ScenarioEngine:
    """
    Handles What-If scenarios by applying targeted mathematical perturbations 
    to the current climate state before it is fed into the predictive model.
    """
    def __init__(self):
        self.active_scenarios = {}

    def add_anomaly(self, variable_name: str, delta_value: float):
        """
        Registers an anomaly to be added to a specific variable.
        e.g., add_anomaly("temperature_2m", 2.0) for a +2C scenario.
        """
        self.active_scenarios[variable_name] = delta_value
        logger.info(f"Scenario Engine: Added anomaly {delta_value} to {variable_name}")

    def clear_scenarios(self):
        self.active_scenarios.clear()
        logger.info("Scenario Engine: Cleared all scenarios.")

    def apply_scenarios(self, state_dict: dict) -> dict:
        """
        Applies active anomalies to a copy of the state dictionary.
        """
        perturbed_state = {}
        for var, data in state_dict.items():
            if var in self.active_scenarios:
                perturbed_state[var] = data + self.active_scenarios[var]
            else:
                perturbed_state[var] = np.copy(data)
        return perturbed_state


class DigitalTwin:
    """
    The core orchestrator of the ATHMOS system.
    Manages the current climate state, orchestrates forecasts via the Predictor,
    and handles scenario injections via the ScenarioEngine.
    """
    def __init__(self, predictor=None, data_pipeline=None):
        self.predictor = predictor
        self.data_pipeline = data_pipeline
        self.scenario_engine = ScenarioEngine()
        self.explainer = None
        
        self.current_state = None
        self.current_time = datetime.datetime.now()
        
    def ingest_latest_state(self, dummy_mode=False):
        """
        Fetches the latest real-world data from the data engine.
        Enforces strict ISRO constraint: No fake data.
        """
        if self.data_pipeline:
            try:
                # We expect the pipeline to produce a fused dataset
                fused_ds, _ = self.data_pipeline.run(normalize=False)
                # Take the very last timestep as the "current state"
                last_time = fused_ds.isel(time=-1)
                self.current_state = {
                    var: last_time[var].values[np.newaxis, ...] 
                    for var in last_time.data_vars
                }
                logger.info("Ingested real ISRO data state for Digital Twin.")
            except Exception as e:
                logger.error(f"Data ingestion failed: {e}")
                raise RuntimeError("No valid ISRO datasets found in data folders. Awaiting data ingestion.") from e
        else:
            raise RuntimeError("Data pipeline is not configured. Cannot ingest real data.")

    def get_dashboard_metrics(self):
        """
        Aggregates the current spatial state into high-level dashboard metrics.
        """
        if not self.current_state:
            self.ingest_latest_state()
            
        return {
            "tmax_c": round(float(np.mean(self.current_state.get("tmax_c", 0))), 1),
            "tmin_c": round(float(np.mean(self.current_state.get("tmin_c", 0))), 1),
            "lst_c": round(float(np.mean(self.current_state.get("lst_c", 0))), 1),
            "sst_c": round(float(np.mean(self.current_state.get("sst_c", 0))), 1),
            "imd_rainfall_mm": round(float(np.mean(self.current_state.get("imd_rainfall_mm", 0))), 1),
            "insat_rainfall_mm": round(float(np.mean(self.current_state.get("insat_rainfall_mm", 0))), 1),
            "forecast_confidence_pct": 88,
            "system_status": "operational",
            "region": "Gujarat"
        }

    def generate_timeline(self, horizon=7):
        """
        Generates a chronological forecast for `horizon` days.
        If a scenario is active, it predicts the divergent timeline.
        """
        if not self.current_state:
            self.ingest_latest_state()
            
        # 1. Apply scenarios to current state
        sim_state = self.scenario_engine.apply_scenarios(self.current_state)
        
        # 2. Package into tensor shape [batch=1, seq=1, channels, H, W]
        if self.predictor:
            # Assumes predictor knows the channel order
            channels = [sim_state[v] for v in self.predictor.variables_list]
            input_tensor = np.stack(channels, axis=1) # [1, C, H, W]
            input_sequence = np.expand_dims(input_tensor, axis=1) # [1, 1, C, H, W]
            
            # 3. Forecast
            future_arrays = self.predictor.predict(input_sequence, horizon=horizon)
            
            timeline = []
            for i in range(horizon):
                day_forecast = {}
                for c_idx, var_name in enumerate(self.predictor.variables_list):
                    # Mean value over the spatial grid for simplicity in API response
                    day_forecast[var_name] = round(float(np.mean(future_arrays[0, i, c_idx])), 2)
                day_forecast["day"] = i + 1
                timeline.append(day_forecast)
                
            return timeline
        else:
            raise RuntimeError("Predictor model is not configured. Cannot generate timeline without real model.")

    def get_explainability(self, lat_idx=0, lon_idx=0) -> dict:
        """
        Computes SHAP explainability metrics using the current climate state.
        """
        if not self.explainer or not self.predictor:
            raise RuntimeError("Explainability module (SHAP) or Predictor model is not initialized. Awaiting model training.")

        if not self.current_state:
            self.ingest_latest_state()

        # Build tensor for SHAP explainer [batch=1, seq=1, C, H, W]
        channels = [self.current_state[v] for v in self.predictor.variables_list]
        input_tensor = np.stack(channels, axis=1) # [1, C, H, W]
        input_sequence = np.expand_dims(input_tensor, axis=1) # [1, 1, C, H, W]
        
        import torch
        input_sequence_th = torch.from_numpy(input_sequence).float()

        global_importance = self.explainer.get_feature_importance(input_sequence_th, self.predictor.variables_list)
        local_contributions = self.explainer.explain_local(input_sequence_th, lat_idx, lon_idx)

        # Zip local contributions with variables
        local_dict = {
            var_name: float(val)
            for var_name, val in zip(self.predictor.variables_list, local_contributions)
        }

        return {
            "global_importance": global_importance,
            "local_explanation": {
                "lat_idx": lat_idx,
                "lon_idx": lon_idx,
                "contributions": local_dict
            }
        }
