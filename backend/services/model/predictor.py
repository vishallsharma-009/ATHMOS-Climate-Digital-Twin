import torch
import logging
from .convlstm import ConvLSTM
import numpy as np
from ..physics_engine import PhysicsEngine

logger = logging.getLogger("athmos.model.predictor")

class ClimatePredictor:
    """
    Handles inference for the trained ConvLSTM model.
    """
    def __init__(self, model_path, input_dim, hidden_dims, variables_list, device=None):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.variables_list = variables_list
        self.physics_engine = PhysicsEngine()
        self.model = ConvLSTM(input_dim=input_dim, hidden_dims=hidden_dims).to(self.device)
        
        if model_path is not None:
            try:
                checkpoint = torch.load(model_path, map_location=self.device)
                self.model.load_state_dict(checkpoint['model_state_dict'])
                logger.info(f"Successfully loaded model weights from {model_path}")
            except Exception as e:
                logger.error(f"Failed to load model weights: {e}")
                raise
            
        self.model.eval()

    def predict(self, input_sequence, horizon=1):
        """
        Generate a forecast for `horizon` timesteps.
        input_sequence: numpy array or tensor of shape [1, seq_len, channels, height, width]
        Returns: constrained numpy array of shape [1, horizon, channels, height, width]
        """
        if isinstance(input_sequence, np.ndarray):
            input_tensor = torch.from_numpy(input_sequence).float()
        else:
            input_tensor = input_sequence.float()
            
        input_tensor = input_tensor.to(self.device)
        
        with torch.no_grad():
            predictions = self.model.predict(input_tensor, horizon=horizon)
            
        pred_np = predictions.cpu().numpy()
        
        # Apply physics constraints channel by channel
        # pred_np shape: [batch, horizon, channels, height, width]
        b, h, c, y, x = pred_np.shape
        constrained_preds = np.zeros_like(pred_np)
        
        for i, var_name in enumerate(self.variables_list):
            # Extract single channel across all batches and horizons
            channel_data = pred_np[:, :, i, :, :]
            constrained_dict = self.physics_engine.apply_constraints({var_name: channel_data})
            constrained_preds[:, :, i, :, :] = constrained_dict[var_name]
            
        return constrained_preds
