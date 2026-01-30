"""
Tests for utils.py - Atomic file operations and state validation.
"""

import pytest
import os
import json
import tempfile

from utils import (
    atomic_write_json, safe_load_json,
    validate_engine_weights, validate_brain_state,
    validate_execution_state, validate_broker_state,
    safe_divide, safe_percentage,
    VALID_ENGINES, VALID_REGIMES
)


class TestAtomicWriteJson:
    """Tests for atomic_write_json function."""

    def test_creates_file(self, temp_dir):
        """Test that atomic_write_json creates a new file."""
        filepath = os.path.join(temp_dir, "test.json")
        data = {"key": "value"}

        atomic_write_json(filepath, data)

        assert os.path.exists(filepath)
        with open(filepath) as f:
            loaded = json.load(f)
        assert loaded == data

    def test_overwrites_existing_file(self, temp_dir):
        """Test that atomic_write_json overwrites existing file."""
        filepath = os.path.join(temp_dir, "test.json")

        # Write initial data
        atomic_write_json(filepath, {"initial": True})

        # Overwrite with new data
        new_data = {"updated": True, "value": 123}
        atomic_write_json(filepath, new_data)

        with open(filepath) as f:
            loaded = json.load(f)
        assert loaded == new_data

    def test_creates_parent_directories(self, temp_dir):
        """Test that atomic_write_json creates parent directories."""
        filepath = os.path.join(temp_dir, "subdir", "nested", "test.json")
        data = {"nested": True}

        atomic_write_json(filepath, data)

        assert os.path.exists(filepath)

    def test_no_temp_files_left(self, temp_dir):
        """Test that no temporary files are left after write."""
        filepath = os.path.join(temp_dir, "test.json")
        atomic_write_json(filepath, {"data": True})

        files = os.listdir(temp_dir)
        assert len(files) == 1
        assert files[0] == "test.json"


class TestSafeLoadJson:
    """Tests for safe_load_json function."""

    def test_loads_valid_json(self, temp_dir):
        """Test loading a valid JSON file."""
        filepath = os.path.join(temp_dir, "test.json")
        data = {"key": "value", "number": 42}

        with open(filepath, 'w') as f:
            json.dump(data, f)

        loaded = safe_load_json(filepath)
        assert loaded == data

    def test_returns_default_for_missing_file(self, temp_dir):
        """Test that missing file returns default."""
        filepath = os.path.join(temp_dir, "nonexistent.json")
        default = {"default": True}

        loaded = safe_load_json(filepath, default)
        assert loaded == default

    def test_returns_default_for_corrupted_json(self, temp_dir):
        """Test that corrupted JSON returns default."""
        filepath = os.path.join(temp_dir, "corrupted.json")

        with open(filepath, 'w') as f:
            f.write("{ invalid json }")

        default = {"fallback": True}
        loaded = safe_load_json(filepath, default)
        assert loaded == default

    def test_returns_empty_dict_when_no_default(self, temp_dir):
        """Test that missing file returns empty dict when no default."""
        filepath = os.path.join(temp_dir, "nonexistent.json")
        loaded = safe_load_json(filepath)
        assert loaded == {}


class TestValidateEngineWeights:
    """Tests for validate_engine_weights function."""

    def test_valid_weights(self, sample_engine_weights):
        """Test that valid weights pass validation."""
        result = validate_engine_weights(sample_engine_weights)
        assert sum(result.values()) == pytest.approx(1.0)

    def test_empty_weights_returns_default(self):
        """Test that empty weights return 100% cash default."""
        result = validate_engine_weights({})
        assert result["CASH"] == 1.0
        assert result["EQUITY"] == 0.0

    def test_rejects_unknown_engine(self):
        """Test that unknown engines are rejected."""
        invalid = {
            "CASH": 0.5,
            "EQUITY": 0.5,
            "DEFENSIVE": 0.0,
            "REAL_ASSET": 0.0,
            "UNKNOWN_ENGINE": 0.0,  # Invalid
        }
        with pytest.raises(ValueError, match="Unknown engine"):
            validate_engine_weights(invalid)

    def test_rejects_negative_weight(self):
        """Test that negative weights are rejected."""
        invalid = {
            "CASH": -0.1,  # Invalid
            "EQUITY": 0.6,
            "DEFENSIVE": 0.3,
            "REAL_ASSET": 0.2,
        }
        with pytest.raises(ValueError, match="Negative weight"):
            validate_engine_weights(invalid)

    def test_rejects_weights_not_summing_to_one(self):
        """Test that weights not summing to 1.0 are rejected."""
        invalid = {
            "CASH": 0.5,
            "EQUITY": 0.5,
            "DEFENSIVE": 0.5,  # Sum = 1.5
            "REAL_ASSET": 0.0,
        }
        with pytest.raises(ValueError, match="sum to"):
            validate_engine_weights(invalid)

    def test_normalizes_float_precision_errors(self):
        """Test that small float precision errors are normalized."""
        # Weights that might not sum to exactly 1.0 due to float math
        weights = {
            "CASH": 0.12,
            "EQUITY": 0.50,
            "DEFENSIVE": 0.20,
            "REAL_ASSET": 0.18,
        }
        result = validate_engine_weights(weights)
        assert sum(result.values()) == pytest.approx(1.0, abs=1e-10)

    def test_adds_missing_engines(self):
        """Test that missing engines are added with 0.0 weight."""
        partial = {
            "CASH": 1.0,
            # Missing other engines
        }
        result = validate_engine_weights(partial)
        assert "EQUITY" in result
        assert "DEFENSIVE" in result
        assert "REAL_ASSET" in result


class TestValidateBrainState:
    """Tests for validate_brain_state function."""

    def test_valid_state(self, sample_brain_state):
        """Test that valid state passes validation."""
        result = validate_brain_state(sample_brain_state)
        assert result["last_regime"] == "RISK_ON"
        assert result["last_allocation_date"] == "2026-01-15"

    def test_invalid_regime_becomes_none(self):
        """Test that invalid regime is set to None."""
        invalid = {
            "last_regime": "INVALID_REGIME",
            "last_allocation_date": None,
            "engine_weights": {"CASH": 1.0},
        }
        result = validate_brain_state(invalid)
        assert result["last_regime"] is None

    def test_old_regime_names_rejected(self):
        """Test that old regime names (TREND, RANGE, SHOCK) are rejected."""
        for old_name in ["TREND", "RANGE", "SHOCK"]:
            state = {"last_regime": old_name, "engine_weights": {"CASH": 1.0}}
            result = validate_brain_state(state)
            assert result["last_regime"] is None

    def test_invalid_date_becomes_none(self):
        """Test that invalid date format is set to None."""
        invalid = {
            "last_regime": "RISK_ON",
            "last_allocation_date": "not-a-date",
            "engine_weights": {"CASH": 1.0},
        }
        result = validate_brain_state(invalid)
        assert result["last_allocation_date"] is None

    def test_corrupted_weights_default_to_cash(self):
        """Test that corrupted weights default to 100% cash."""
        invalid = {
            "last_regime": "RISK_ON",
            "engine_weights": {"CASH": -1.0, "EQUITY": 2.0},  # Invalid
        }
        result = validate_brain_state(invalid)
        assert result["engine_weights"]["CASH"] == 1.0
        assert result["engine_weights"]["EQUITY"] == 0.0


class TestValidateExecutionState:
    """Tests for validate_execution_state function."""

    def test_valid_state(self):
        """Test that valid state passes validation."""
        state = {
            "last_execution": None,
            "execution_history": [],
            "last_regime": "RISK_ON",
            "account_equity": 500_000.0,
        }
        result = validate_execution_state(state)
        assert result["account_equity"] == 500_000.0
        assert result["last_regime"] == "RISK_ON"

    def test_invalid_equity_uses_default(self):
        """Test that invalid equity uses default."""
        state = {"account_equity": -1000}  # Invalid
        result = validate_execution_state(state)
        assert result["account_equity"] == 1_000_000.0  # Default

    def test_history_bounded(self):
        """Test that history is bounded to max size."""
        state = {
            "execution_history": [{"i": i} for i in range(200)]
        }
        result = validate_execution_state(state)
        assert len(result["execution_history"]) <= 100


class TestValidateBrokerState:
    """Tests for validate_broker_state function."""

    def test_valid_state(self, sample_positions):
        """Test that valid state passes validation."""
        state = {
            "positions": sample_positions,
            "cash": 120_000.0,
            "trade_history": [],
        }
        result = validate_broker_state(state)
        assert result["cash"] == 120_000.0
        assert result["positions"]["SPY"] == 500_000.0

    def test_negative_cash_uses_default(self):
        """Test that negative cash uses default."""
        state = {"cash": -1000, "positions": {}}
        result = validate_broker_state(state)
        assert result["cash"] == 1_000_000.0

    def test_negative_positions_filtered(self):
        """Test that negative positions are filtered out."""
        state = {
            "positions": {"SPY": 100000, "TLT": -50000},  # TLT invalid
            "cash": 100000,
        }
        result = validate_broker_state(state)
        assert "SPY" in result["positions"]
        assert "TLT" not in result["positions"]


class TestSafeDivide:
    """Tests for safe_divide function."""

    def test_normal_division(self):
        """Test normal division."""
        assert safe_divide(10, 2) == 5.0
        assert safe_divide(100, 4) == 25.0

    def test_division_by_zero_returns_default(self):
        """Test that division by zero returns default."""
        assert safe_divide(10, 0) == 0.0
        assert safe_divide(10, 0, default=999) == 999

    def test_zero_numerator(self):
        """Test zero numerator."""
        assert safe_divide(0, 10) == 0.0


class TestSafePercentage:
    """Tests for safe_percentage function."""

    def test_normal_percentage(self):
        """Test normal percentage calculation."""
        assert safe_percentage(25, 100) == 25.0
        assert safe_percentage(50, 200) == 25.0

    def test_zero_whole_returns_default(self):
        """Test that zero whole returns default."""
        assert safe_percentage(10, 0) == 0.0
        assert safe_percentage(10, 0, default=100) == 100
