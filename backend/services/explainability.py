import torch
import numpy as np
import logging

logger = logging.getLogger("athmos.explainability")

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError as e:
    SHAP_AVAILABLE = False
    logger.warning(f"SHAP could not be imported: {e}. Explainer will run in Dummy mode.")

class ShapExplainer:
    """
    Provides explainable AI metrics for the ConvLSTM model using SHAP.
    Calculates both global feature importance and local spatial explanations.
    """
    def __init__(self, model, background_data, device=None):
        """
        model: PyTorch model (ConvLSTM)
        background_data: A representative sample of training data to use as the background
                         for SHAP (Tensor of shape [batch, seq_len, channels, height, width]).
        """
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = model.to(self.device)
        self.model.eval()
        
        if not SHAP_AVAILABLE:
            logger.info("Initializing Dummy Explainer due to missing SHAP dependency.")
            return

        background_tensor = background_data.to(self.device)
        
        # We need a wrapper because our model returns a tuple (output, hidden_state)
        # GradientExplainer expects a model that just returns the output tensor
        class ModelWrapper(torch.nn.Module):
            def __init__(self, core_model):
                super().__init__()
                self.core_model = core_model
                
            def forward(self, x):
                out, _ = self.core_model(x)
                # We usually want to explain the final prediction step
                return out[:, -1, :, :, :]
                
        self.wrapped_model = ModelWrapper(self.model)
        
        try:
            self.explainer = shap.GradientExplainer(self.wrapped_model, background_tensor)
            logger.info("Successfully initialized SHAP GradientExplainer.")
        except Exception as e:
            logger.error(f"Failed to initialize SHAP explainer: {e}")
            raise

    def get_feature_importance(self, input_data: torch.Tensor, variable_names: list) -> dict:
        """
        Computes the global feature importance for the given input batch.
        input_data: Tensor [batch, seq_len, channels, height, width]
        Returns: Dict mapping variable name to its mean absolute SHAP value (importance).
        """
        if not SHAP_AVAILABLE:
            # Dummy fallback
            val = 1.0 / len(variable_names)
            return {var_name: val for var_name in variable_names}

        input_data = input_data.to(self.device)
        
        # shap_values is a list of tensors (one per output channel), 
        # or a single tensor if output has 1 channel.
        # Shape per output channel: [batch, seq_len, channels, height, width]
        shap_values = self.explainer.shap_values(input_data)
        
        # If multiple output channels, take the mean magnitude across all of them
        if isinstance(shap_values, list):
            shap_mag = np.mean([np.abs(sv) for sv in shap_values], axis=0)
        else:
            shap_mag = np.abs(shap_values)
            
        # Aggregate across batch, seq_len, height, width to get 1 value per input channel
        channel_importance = np.mean(shap_mag, axis=(0, 1, 3, 4))
        
        importance_dict = {
            var_name: float(val) 
            for var_name, val in zip(variable_names, channel_importance)
        }
        
        # Sort by importance descending
        return dict(sorted(importance_dict.items(), key=lambda item: item[1], reverse=True))

    def explain_local(self, input_data: torch.Tensor, lat_idx: int, lon_idx: int) -> dict:
        """
        Computes local SHAP values for a specific spatial coordinate.
        This explains *why* the model predicted a specific value at (lat, lon).
        """
        if not SHAP_AVAILABLE:
            # Dummy fallback
            return [1.0] * input_data.size(2)

        input_data = input_data.to(self.device)
        shap_values = self.explainer.shap_values(input_data)
        
        if isinstance(shap_values, list):
            # Sum up magnitude across all output channels for the local pixel
            shap_mag = np.sum([np.abs(sv[:, :, :, lat_idx, lon_idx]) for sv in shap_values], axis=0)
        else:
            shap_mag = np.abs(shap_values[:, :, :, lat_idx, lon_idx])
            
        # Average across the batch and time dimensions to get contribution per channel
        channel_contributions = np.mean(shap_mag, axis=(0, 1))
        
        return channel_contributions.tolist()
