import pytest
from services.digital_twin import DigitalTwin, ScenarioEngine

def test_scenario_engine_add_anomaly():
    engine = ScenarioEngine()
    engine.add_anomaly("tmax_c", 2.0)
    assert "tmax_c" in engine.active_scenarios
    assert engine.active_scenarios["tmax_c"] == 2.0

def test_scenario_engine_apply(mock_climate_state):
    engine = ScenarioEngine()
    engine.add_anomaly("tmax_c", 2.0)
    
    modified_state = engine.apply_scenarios(mock_climate_state)
    
    # Original is 25.0, anomaly adds 2.0
    assert modified_state["tmax_c"][0, 0] == 27.0
    # Rainfall should be untouched
    assert modified_state["imd_rainfall_mm"][0, 0] == 25.0

def test_digital_twin_initialization():
    dt = DigitalTwin()
    assert dt.predictor is None
    assert dt.current_state is None
    assert dt.explainer is None
