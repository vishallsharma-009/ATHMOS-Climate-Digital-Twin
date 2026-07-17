import numpy as np
import logging

logger = logging.getLogger("athmos.physics_engine")

class PhysicsEngine:
    """
    Applies strict physical constraints to raw neural network climate predictions
    to ensure meteorological validity for the Digital Twin.
    """
    
    def __init__(self):
        # We assume the predictions are provided as a dictionary mapping 
        # variable names to numpy arrays, or as an xarray Dataset.
        pass
        
    def apply_constraints(self, predictions: dict) -> dict:
        """
        Takes a dictionary of {variable_name: np.ndarray} and applies physics constraints.
        Returns the modified dictionary.
        """
        constrained = {}
        # Apply standard range bounds
        for var, data in predictions.items():
            if var in ["imd_rainfall_mm", "insat_rainfall_mm"]:
                constrained[var] = self.apply_rainfall_constraints(data)
            elif var in ["tmax_c", "tmin_c", "lst_c", "sst_c"]:
                constrained[var] = self.apply_temperature_constraints(data)
            else:
                constrained[var] = data
                
        # Thermodynamic constraint: tmax must be >= tmin
        if "tmax_c" in constrained and "tmin_c" in constrained:
            # If tmin > tmax, set tmin = tmax
            constrained["tmin_c"] = np.minimum(constrained["tmin_c"], constrained["tmax_c"])
                
        return constrained

    def apply_rainfall_constraints(self, data: np.ndarray) -> np.ndarray:
        """
        Rainfall cannot be negative.
        Cap extreme anomalies (e.g., max 1500 mm/day for cyclones).
        """
        # Ensure non-negative
        data = np.maximum(data, 0.0)
        # Cap at realistic upper bound
        data = np.minimum(data, 1500.0)
        return data

    def apply_temperature_constraints(self, data: np.ndarray) -> np.ndarray:
        """
        Temperatures (in Celsius) must remain within valid Earth bounds.
        Assuming target region: -50 C to +70 C.
        """
        data = np.maximum(data, -50.0)
        data = np.minimum(data, 70.0)
        return data
