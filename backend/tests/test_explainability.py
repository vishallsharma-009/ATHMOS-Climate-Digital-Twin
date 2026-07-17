import pytest
import torch
import numpy as np
from services.explainability import ShapExplainer
from services.model.predictor import ClimatePredictor

def test_shap_explainer(mock_isro_vars):
    # Initialize a dummy model
    predictor = ClimatePredictor(
        model_path=None, 
        input_dim=len(mock_isro_vars), 
        hidden_dims=[16, 8], 
        variables_list=mock_isro_vars
    )
    
    # SHAP requires a background tensor for GradientExplainer
    # [Batch=1, Seq=1, Channels=5, H=10, W=10]
    background_tensor = torch.zeros((1, 1, len(mock_isro_vars), 10, 10)).float().to(predictor.device)
    
    explainer = ShapExplainer(predictor.model, background_tensor, device=predictor.device)
    
    # Create a dummy input tensor to explain
    input_tensor = torch.rand((1, 1, len(mock_isro_vars), 10, 10)).float().to(predictor.device)
    
    # Test global importance
    global_importance = explainer.get_feature_importance(input_tensor, mock_isro_vars)
    assert isinstance(global_importance, dict)
    for var in mock_isro_vars:
        assert var in global_importance
        
    # Test local explanation
    local_contributions = explainer.explain_local(input_tensor, lat_idx=5, lon_idx=5)
    assert len(local_contributions) == len(mock_isro_vars)
    assert isinstance(local_contributions, list)
