import pytest
import torch
from services.model.predictor import ClimatePredictor

def test_climate_predictor_initialization(mock_isro_vars):
    # Initialize without a physical model path to test base structural setup
    predictor = ClimatePredictor(
        model_path=None, 
        input_dim=len(mock_isro_vars), 
        hidden_dims=[16, 8], 
        variables_list=mock_isro_vars
    )
    
    assert predictor.variables_list == mock_isro_vars
    assert predictor.device.type in ["cpu", "cuda"]
    assert predictor.model is not None

def test_model_forward_pass(mock_isro_vars):
    predictor = ClimatePredictor(
        model_path=None, 
        input_dim=len(mock_isro_vars), 
        hidden_dims=[16, 8], 
        variables_list=mock_isro_vars
    )
    
    # Create a dummy input tensor [Batch=2, Seq=5, Channels=5, H=10, W=10]
    dummy_input = torch.rand(2, 5, len(mock_isro_vars), 10, 10).to(predictor.device)
    
    # Forward pass
    out, hidden = predictor.model(dummy_input)
    
    # Verify dimensions
    assert out.size() == (2, 5, len(mock_isro_vars), 10, 10)

def test_model_autoregressive_predict(mock_isro_vars):
    predictor = ClimatePredictor(
        model_path=None, 
        input_dim=len(mock_isro_vars), 
        hidden_dims=[16, 8], 
        variables_list=mock_isro_vars
    )
    
    dummy_input = torch.rand(2, 5, len(mock_isro_vars), 10, 10).to(predictor.device)
    
    # Predict 3 steps into the future
    horizon = 3
    preds = predictor.model.predict(dummy_input, horizon=horizon)
    
    # Verify forecast dimension: [Batch=2, Horizon=3, Channels=5, H=10, W=10]
    assert preds.size() == (2, horizon, len(mock_isro_vars), 10, 10)
