"""
Pytest configuration and shared fixtures.
"""

import pytest
import tempfile
import os
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_json_file(temp_dir):
    """Create a temporary JSON file path."""
    return os.path.join(temp_dir, "test_state.json")


@pytest.fixture
def sample_engine_weights():
    """Sample valid engine weights."""
    return {
        "CASH": 0.12,
        "EQUITY": 0.50,
        "DEFENSIVE": 0.20,
        "REAL_ASSET": 0.18,
    }


@pytest.fixture
def sample_engine_weights_risk_off():
    """Sample RISK_OFF engine weights (100% cash)."""
    return {
        "CASH": 1.0,
        "EQUITY": 0.0,
        "DEFENSIVE": 0.0,
        "REAL_ASSET": 0.0,
    }


@pytest.fixture
def sample_brain_state():
    """Sample valid brain state."""
    return {
        "last_regime": "RISK_ON",
        "last_allocation_date": "2026-01-15",
        "engine_weights": {
            "CASH": 0.12,
            "EQUITY": 0.50,
            "DEFENSIVE": 0.20,
            "REAL_ASSET": 0.18,
        }
    }


@pytest.fixture
def sample_brain_output(sample_engine_weights):
    """Sample brain output dict."""
    return {"engine_weights": sample_engine_weights}


@pytest.fixture
def sample_positions():
    """Sample broker positions."""
    return {
        "SPY": 500000.0,
        "TLT": 200000.0,
        "GLD": 180000.0,
    }


@pytest.fixture
def paper_broker(temp_dir):
    """Create a PaperBroker with temporary state file."""
    from execution import PaperBroker
    state_file = os.path.join(temp_dir, "paper_broker_state.json")
    broker = PaperBroker(initial_cash=1_000_000.0, state_file=state_file)
    broker.reset()
    return broker
