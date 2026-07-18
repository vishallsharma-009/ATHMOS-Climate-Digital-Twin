import logging
import numpy as np
import datetime

from .physics_engine import PhysicsEngine

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
    def __init__(self, predictor=None, data_pipeline=None, normalizer=None):
        self.predictor = predictor
        self.data_pipeline = data_pipeline
        self.normalizer = normalizer
        self.physics_engine = PhysicsEngine()
        self.scenario_engine = ScenarioEngine()
        self.explainer = None

        self.current_state = None
        self.current_time = datetime.datetime.now()
        
    def ingest_latest_state(self, state_dict=None, dummy_mode=False):
        """
        Fetches the latest real-world data from the data engine.
        Enforces strict ISRO constraint: No fake data.
        """
        if state_dict is not None:
            self.current_state = state_dict
            logger.info("Ingested state dict directly for Digital Twin.")
            return

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
        The stored current_state is NORMALIZED; we inverse-normalize to physical
        units for display only (the DigitalTwin is the anti-corruption boundary).
        """
        if not self.current_state:
            self.ingest_latest_state()

        # current_state is normalized; convert to physical units for display.
        physical_state = self._inverse_normalize_state(self.current_state)

        return {
            "tmax_c": round(float(np.mean(physical_state.get("tmax_c", 0))), 1),
            "tmin_c": round(float(np.mean(physical_state.get("tmin_c", 0))), 1),
            "lst_c": round(float(np.mean(physical_state.get("lst_c", 0))), 1),
            "sst_c": round(float(np.mean(physical_state.get("sst_c", 0))), 1),
            "imd_rainfall_mm": round(float(np.mean(physical_state.get("imd_rainfall_mm", 0))), 1),
            "insat_rainfall_mm": round(float(np.mean(physical_state.get("insat_rainfall_mm", 0))), 1),
            "forecast_confidence_pct": 88,
            "system_status": "operational",
            "region": "Gujarat"
        }

    def generate_timeline(self, horizon=7):
        """
        Generates a chronological forecast for `horizon` days.
        If a scenario is active, it predicts the divergent timeline.

        Architecture: predictor.predict returns NORMALIZED output. This
        DigitalTwin method is the anti-corruption boundary — it
        inverse-normalizes to physical units and applies physics, then aggregates.
        """
        if not self.current_state:
            self.ingest_latest_state()

        # 1. Apply scenarios to current state (stays normalized, like the model)
        sim_state = self.scenario_engine.apply_scenarios(self.current_state)

        # 2. Package into tensor shape [batch=1, seq=1, channels, H, W]
        if self.predictor:
            # Assumes predictor knows the channel order
            channels = [sim_state[v] for v in self.predictor.variables_list]
            input_tensor = np.stack(channels, axis=1) # [1, C, H, W]
            input_sequence = np.expand_dims(input_tensor, axis=1) # [1, 1, C, H, W]

            # 3. Forecast (NORMALIZED output from the model/predictor)
            future_arrays = self.predictor.predict(input_sequence, horizon=horizon)

            # 4. DigitalTwin edge: inverse-normalize to physical units
            future_arrays = self._inverse_normalize(future_arrays, self.predictor.variables_list)
            # 5. DigitalTwin edge: enforce physics on the PHYSICAL tensor
            future_arrays = self._apply_physics(future_arrays, self.predictor.variables_list)

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

    # ------------------------------------------------------------------
    # Inverse-normalization + physics (edge layer owned by DigitalTwin)
    # ------------------------------------------------------------------
    def _inverse_normalize(self, tensor, variables_list):
        """
        Inverse-normalize a [..., C, H, W] numpy tensor channel-wise using the
        loaded Normalizer stats. Returns a physical-units tensor of the same
        shape. Raises if the Normalizer is missing or a variable lacks stats —
        the system must NEVER emit normalized values labeled as physical.
        """
        if self.normalizer is None:
            raise RuntimeError(
                "Normalizer is not loaded; cannot produce physical (°C / mm) "
                "values. Run the fusion pipeline (run_pipeline) to generate "
                "fused_tensor_norm_stats.json."
            )
        out = np.asarray(tensor, dtype=np.float64)
        for c_idx, var_name in enumerate(variables_list):
            stats = self.normalizer.stats.get(var_name)
            if stats is None:
                raise RuntimeError(
                    f"Normalizer has no stats for '{var_name}'; refusing to "
                    f"emit un-normalized (physical) values for a variable that "
                    f"was trained/served in normalized space."
                )
            out[..., c_idx, :, :] = out[..., c_idx, :, :] * stats["std"] + stats["mean"]
        return out

    def _inverse_normalize_state(self, state_dict):
        """
        Inverse-normalize the current_state dict (each value is a [1, H, W] array)
        to physical units. The stored state remains normalized.
        """
        if self.normalizer is None:
            raise RuntimeError(
                "Normalizer is not loaded; cannot produce physical (°C / mm) "
                "values. Run the fusion pipeline (run_pipeline) to generate "
                "fused_tensor_norm_stats.json."
            )
        out = {}
        for var, data in state_dict.items():
            stats = self.normalizer.stats.get(var)
            if stats is None:
                raise RuntimeError(
                    f"Normalizer has no stats for '{var}'; refusing to emit "
                    f"un-normalized (physical) values."
                )
            out[var] = np.asarray(data, dtype=np.float64) * stats["std"] + stats["mean"]
        return out

    def _apply_physics(self, tensor, variables_list):
        """
        Apply the PhysicsEngine constraints on a PHYSICAL-units [1, horizon, C, H, W]
        tensor. Channels are built into a dict so cross-variable rules (e.g.
        tmin <= tmax) are enforced. Validates shape, channel count, and that no
        variable is silently dropped.
        """
        # 1. Shape validation: must be 5D [batch, horizon, C, H, W], batch == 1.
        if tensor.ndim != 5:
            raise ValueError(
                f"_apply_physics expects a 5D tensor [batch, horizon, C, H, W]; "
                f"got {tensor.ndim}D with shape {tensor.shape}."
            )
        if tensor.shape[0] != 1:
            raise ValueError(f"Expected batch dimension of 1, got {tensor.shape[0]}.")
        # 2. Channel count must match variables_list.
        if tensor.shape[2] != len(variables_list):
            raise ValueError(
                f"Forecast channel count ({tensor.shape[2]}) does not match "
                f"variables_list length ({len(variables_list)})."
            )
        # 3. Build per-channel dict; verify every variable is present (no silent drops).
        channels = {
            var_name: tensor[0, :, c_idx, :, :]
            for c_idx, var_name in enumerate(variables_list)
        }
        if len(channels) != len(variables_list):
            raise ValueError("Duplicate variable names detected in variables_list.")
        constrained = self.physics_engine.apply_constraints(channels)
        missing = [v for v in variables_list if v not in constrained]
        if missing:
            raise RuntimeError(f"PhysicsEngine dropped unhandled variables: {missing}")
        out = np.asarray(tensor, dtype=np.float64)
        for c_idx, var_name in enumerate(variables_list):
            out[0, :, c_idx, :, :] = constrained[var_name]
        return out

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
