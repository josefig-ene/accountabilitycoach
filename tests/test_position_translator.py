"""
Tests for execution/position_translator.py
"""

import pytest
from execution import PositionTranslator, translate_brain_output, TargetPositions


class TestPositionTranslator:
    """Tests for PositionTranslator class."""

    def test_translate_risk_on_allocation(self, sample_engine_weights):
        """Test translating RISK_ON allocation."""
        translator = PositionTranslator()
        account_equity = 1_000_000.0

        result = translator.translate(sample_engine_weights, account_equity)

        assert isinstance(result, TargetPositions)
        assert result.account_equity == account_equity
        assert result.dollar_positions["SPY"] == pytest.approx(500_000.0, rel=0.01)
        assert result.dollar_positions["TLT"] == pytest.approx(200_000.0, rel=0.01)
        assert result.dollar_positions["GLD"] == pytest.approx(180_000.0, rel=0.01)
        assert result.cash_position == pytest.approx(120_000.0, rel=0.01)

    def test_translate_risk_off_allocation(self, sample_engine_weights_risk_off):
        """Test translating RISK_OFF allocation (100% cash)."""
        translator = PositionTranslator()
        account_equity = 1_000_000.0

        result = translator.translate(sample_engine_weights_risk_off, account_equity)

        assert result.cash_position == pytest.approx(1_000_000.0)
        assert len(result.dollar_positions) == 0 or all(
            v == 0 for v in result.dollar_positions.values()
        )

    def test_rejects_unknown_engine(self):
        """Test that unknown engines are rejected."""
        translator = PositionTranslator()
        invalid_weights = {
            "CASH": 0.5,
            "EQUITY": 0.5,
            "DEFENSIVE": 0.0,
            "REAL_ASSET": 0.0,
            "CRYPTO": 0.0,  # Unknown engine
        }

        with pytest.raises(ValueError, match="Unknown engines"):
            translator.translate(invalid_weights, 1_000_000.0)

    def test_rejects_missing_engine(self):
        """Test that missing engines are rejected."""
        translator = PositionTranslator()
        incomplete_weights = {
            "CASH": 0.5,
            "EQUITY": 0.5,
            # Missing DEFENSIVE and REAL_ASSET
        }

        with pytest.raises(ValueError, match="Missing engines"):
            translator.translate(incomplete_weights, 1_000_000.0)

    def test_rejects_negative_weight(self):
        """Test that negative weights are rejected."""
        translator = PositionTranslator()
        invalid_weights = {
            "CASH": -0.1,
            "EQUITY": 0.6,
            "DEFENSIVE": 0.3,
            "REAL_ASSET": 0.2,
        }

        with pytest.raises(ValueError, match="Negative weight"):
            translator.translate(invalid_weights, 1_000_000.0)

    def test_rejects_weights_not_summing_to_one(self):
        """Test that weights not summing to 1.0 are rejected."""
        translator = PositionTranslator()
        invalid_weights = {
            "CASH": 0.5,
            "EQUITY": 0.5,
            "DEFENSIVE": 0.5,  # Sum > 1
            "REAL_ASSET": 0.0,
        }

        with pytest.raises(ValueError, match="sum to"):
            translator.translate(invalid_weights, 1_000_000.0)

    def test_rejects_zero_equity(self):
        """Test that zero equity is rejected."""
        translator = PositionTranslator()
        weights = {
            "CASH": 1.0,
            "EQUITY": 0.0,
            "DEFENSIVE": 0.0,
            "REAL_ASSET": 0.0,
        }

        with pytest.raises(ValueError, match="positive"):
            translator.translate(weights, 0)

    def test_rejects_negative_equity(self):
        """Test that negative equity is rejected."""
        translator = PositionTranslator()
        weights = {
            "CASH": 1.0,
            "EQUITY": 0.0,
            "DEFENSIVE": 0.0,
            "REAL_ASSET": 0.0,
        }

        with pytest.raises(ValueError, match="positive"):
            translator.translate(weights, -1000)

    def test_rejects_tiny_equity(self):
        """Test that very small equity is rejected (sanity check)."""
        translator = PositionTranslator()
        weights = {
            "CASH": 1.0,
            "EQUITY": 0.0,
            "DEFENSIVE": 0.0,
            "REAL_ASSET": 0.0,
        }

        with pytest.raises(ValueError, match="too small"):
            translator.translate(weights, 50)  # $50 is too small

    def test_normalizes_float_precision(self, sample_engine_weights):
        """Test that float precision errors are normalized."""
        translator = PositionTranslator()
        account_equity = 1_000_000.0

        result = translator.translate(sample_engine_weights, account_equity)

        # Total should sum to account equity
        total = sum(result.dollar_positions.values()) + result.cash_position
        assert total == pytest.approx(account_equity, rel=0.001)

    def test_to_dict(self, sample_engine_weights):
        """Test that TargetPositions.to_dict() works."""
        translator = PositionTranslator()
        result = translator.translate(sample_engine_weights, 1_000_000.0)

        result_dict = result.to_dict()

        assert "timestamp" in result_dict
        assert "account_equity" in result_dict
        assert "engine_weights" in result_dict
        assert "dollar_positions" in result_dict
        assert "cash_position" in result_dict


class TestTranslateBrainOutput:
    """Tests for translate_brain_output convenience function."""

    def test_translates_brain_output(self, sample_brain_output):
        """Test the convenience function."""
        result = translate_brain_output(sample_brain_output, 500_000.0)

        assert isinstance(result, TargetPositions)
        assert result.account_equity == 500_000.0
        assert result.dollar_positions["SPY"] == pytest.approx(250_000.0, rel=0.01)

    def test_handles_different_equity_sizes(self, sample_brain_output):
        """Test with different equity sizes."""
        for equity in [100_000, 500_000, 1_000_000, 10_000_000]:
            result = translate_brain_output(sample_brain_output, float(equity))
            total = sum(result.dollar_positions.values()) + result.cash_position
            assert total == pytest.approx(equity, rel=0.001)
