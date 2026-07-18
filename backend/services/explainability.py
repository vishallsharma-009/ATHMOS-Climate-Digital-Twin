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

        self.background_tensor = background_data.to(self.device)
        
        # We need a wrapper because our model returns a tuple (output, hidden_state)
        # GradientExplainer expects a model that just returns the output tensor
        class GlobalModelWrapper(torch.nn.Module):
            def __init__(self, core_model):
                super().__init__()
                self.core_model = core_model
                
            def forward(self, x):
                out, _ = self.core_model(x)
                # We usually want to explain the final prediction step
                # Mean over spatial dimensions to get [batch, channels]
                return out[:, -1, :, :, :].mean(dim=(2, 3))
                
        self.wrapped_model = GlobalModelWrapper(self.model)
        
        try:
            self.explainer = shap.GradientExplainer(self.wrapped_model, self.background_tensor)
            logger.info("Successfully initialized SHAP GradientExplainer.")
        except Exception as e:
            logger.error(f"Failed to initialize SHAP explainer: {e}")
            raise

    def _ensure_background_shape(self, spatial_shape: tuple):
        if not SHAP_AVAILABLE:
            return
        if self.background_tensor.shape[3:] != spatial_shape:
            logger.info(f"Reinitializing SHAP explainer background tensor to match spatial shape: {spatial_shape}")
            b, s, c = self.background_tensor.shape[:3]
            h, w = spatial_shape
            self.background_tensor = torch.zeros((b, s, c, h, w), dtype=self.background_tensor.dtype, device=self.device)
            try:
                self.explainer = shap.GradientExplainer(self.wrapped_model, self.background_tensor)
            except Exception as e:
                logger.error(f"Failed to reinitialize SHAP explainer: {e}")

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
        self._ensure_background_shape(input_data.shape[3:])
        
        # shap_values is a list of tensors (one per output channel), 
        # or a single tensor if output has 1 channel.
        # Shape per output channel: [batch, seq_len, channels, height, width]
        shap_values = self.explainer.shap_values(input_data)
        
        # If multiple output channels, take the mean magnitude across all of them
        if isinstance(shap_values, list):
            shap_mag = np.mean([np.abs(sv) for sv in shap_values], axis=0)
        elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 6:
            # shap_values shape: [batch, seq, in_channels, H, W, out_channels]
            # Average across out_channels first (axis 5)
            shap_mag = np.mean(np.abs(shap_values), axis=5)
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
        self._ensure_background_shape(input_data.shape[3:])
        
        class LocalModelWrapper(torch.nn.Module):
            def __init__(self, core_model, lat, lon):
                super().__init__()
                self.core_model = core_model
                self.lat = lat
                self.lon = lon
                
            def forward(self, x):
                out, _ = self.core_model(x)
                return out[:, -1, :, self.lat, self.lon]
                
        local_wrapper = LocalModelWrapper(self.model, lat_idx, lon_idx)
        local_explainer = shap.GradientExplainer(local_wrapper, self.background_tensor)
        shap_values = local_explainer.shap_values(input_data)
        
        if isinstance(shap_values, list):
            # Sum up magnitude across all output channels for the local pixel
            shap_mag = np.sum([np.abs(sv[:, :, :, lat_idx, lon_idx]) for sv in shap_values], axis=0)
        elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 6:
            # shap_values shape: [batch, seq, in_channels, H, W, out_channels]
            shap_mag = np.sum(np.abs(shap_values[:, :, :, lat_idx, lon_idx, :]), axis=3)
        else:
            shap_mag = np.abs(shap_values[:, :, :, lat_idx, lon_idx])
            
        # Average across the batch and time dimensions to get contribution per channel
        channel_contributions = np.mean(shap_mag, axis=(0, 1))
        
        return channel_contributions.tolist()
