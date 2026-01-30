"""
Tests for v1_brain_skeleton.py - Brain allocator logic.

Note: These tests focus on allocator logic, not data fetching (which requires yfinance).
"""

import pytest
import os
import json
import datetime

# Import directly to avoid yfinance dependency issues
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v1_brain_skeleton import (
    allocate_capital, load_state, save_state,
    DELTA, ALPHA, COOLDOWN_WEEKS, ENGINES
)
from execution_config import REGIME_ENGINE_TARGETS


class TestAllocateCapital:
    """Tests for allocate_capital function."""

    @pytest.fixture
    def fresh_state(self):
        """Create a fresh state with no prior allocation."""
        return {
            "last_regime": None,
            "last_allocation_date": None,
            "engine_weights": {
                "CASH": 1.0,
                "EQUITY": 0.0,
                "DEFENSIVE": 0.0,
                "REAL_ASSET": 0.0,
            }
        }

    @pytest.fixture
    def state_with_regime(self):
        """Create a state with existing regime (RISK_ON)."""
        return {
            "last_regime": "RISK_ON",
            "last_allocation_date": "2025-01-01",  # Old date, cooldown expired
            "engine_weights": {
                "CASH": 0.12,
                "EQUITY": 0.50,
                "DEFENSIVE": 0.20,
                "REAL_ASSET": 0.18,
            }
        }

    def test_initial_allocation_from_none(self, fresh_state):
        """Test first allocation when last_regime is None."""
        new_state = allocate_capital(fresh_state, "RISK_ON")

        assert new_state["last_regime"] == "RISK_ON"
        assert new_state["last_allocation_date"] is not None
        # Weights should move toward RISK_ON targets
        assert new_state["engine_weights"]["CASH"] < 1.0
        assert new_state["engine_weights"]["EQUITY"] > 0.0

    def test_allocation_respects_alpha(self, fresh_state):
        """Test that allocation uses alpha (ramp fraction)."""
        new_state = allocate_capital(fresh_state, "RISK_ON")

        # Target EQUITY for RISK_ON is 0.50
        # Starting from 0, with ALPHA=0.33, should move 33% toward target
        expected_equity = 0.0 + ALPHA * (0.50 - 0.0)  # ~0.165
        assert new_state["engine_weights"]["EQUITY"] == pytest.approx(expected_equity, rel=0.01)

    def test_allocation_respects_delta(self, fresh_state):
        """Test that allocation caps weight changes at delta."""
        # If alpha would produce a change > delta, it should be capped
        new_state = allocate_capital(fresh_state, "RISK_ON")

        # Maximum change should be DELTA (0.15)
        for engine in ENGINES:
            original = fresh_state["engine_weights"][engine]
            new = new_state["engine_weights"][engine]
            change = abs(new - original)
            assert change <= DELTA + 0.001  # Small tolerance for float math

    def test_cooldown_blocks_allocation(self):
        """Test that cooldown blocks new allocations."""
        today = datetime.date.today()
        recent_date = (today - datetime.timedelta(days=7)).isoformat()  # 1 week ago

        state = {
            "last_regime": "RISK_ON",
            "last_allocation_date": recent_date,
            "engine_weights": {
                "CASH": 0.12,
                "EQUITY": 0.50,
                "DEFENSIVE": 0.20,
                "REAL_ASSET": 0.18,
            }
        }

        # Try to change to RISK_OFF - should be blocked by cooldown
        new_state = allocate_capital(state, "RISK_OFF")

        # State should be unchanged
        assert new_state["last_regime"] == "RISK_ON"
        assert new_state["engine_weights"]["EQUITY"] == 0.50

    def test_cooldown_bypass_when_last_regime_none(self):
        """Test that cooldown is bypassed when last_regime is None."""
        today = datetime.date.today()
        recent_date = (today - datetime.timedelta(days=1)).isoformat()  # Yesterday

        state = {
            "last_regime": None,  # No regime set
            "last_allocation_date": recent_date,  # But has recent date
            "engine_weights": {
                "CASH": 1.0,
                "EQUITY": 0.0,
                "DEFENSIVE": 0.0,
                "REAL_ASSET": 0.0,
            }
        }

        # Should be allowed even though date is recent
        new_state = allocate_capital(state, "RISK_OFF")

        assert new_state["last_regime"] == "RISK_OFF"

    def test_no_change_when_same_regime(self, state_with_regime):
        """Test that same regime doesn't trigger reallocation."""
        new_state = allocate_capital(state_with_regime, "RISK_ON")

        # State should be unchanged
        assert new_state == state_with_regime

    def test_regime_change_after_cooldown(self):
        """Test regime change after cooldown expires."""
        old_date = (datetime.date.today() - datetime.timedelta(weeks=4)).isoformat()

        state = {
            "last_regime": "RISK_ON",
            "last_allocation_date": old_date,  # 4 weeks ago, cooldown expired
            "engine_weights": {
                "CASH": 0.12,
                "EQUITY": 0.50,
                "DEFENSIVE": 0.20,
                "REAL_ASSET": 0.18,
            }
        }

        new_state = allocate_capital(state, "RISK_OFF")

        # Should be allowed - cooldown expired
        assert new_state["last_regime"] == "RISK_OFF"
        # Weights should move toward RISK_OFF (100% cash)
        assert new_state["engine_weights"]["CASH"] > 0.12

    def test_allocation_updates_date(self, fresh_state):
        """Test that allocation updates the date."""
        new_state = allocate_capital(fresh_state, "RISK_ON")

        assert new_state["last_allocation_date"] == datetime.date.today().isoformat()

    def test_all_regimes_have_targets(self):
        """Test that all valid regimes have target weights defined."""
        for regime in ["RISK_ON", "RISK_NEUTRAL", "RISK_OFF"]:
            assert regime in REGIME_ENGINE_TARGETS
            targets = REGIME_ENGINE_TARGETS[regime]
            assert sum(targets.values()) == pytest.approx(1.0)


class TestLoadSaveState:
    """Tests for state persistence functions."""

    def test_load_state_returns_default_when_no_file(self, temp_dir, monkeypatch):
        """Test that load_state returns default when file doesn't exist."""
        # Monkeypatch STATE_FILE to use temp directory
        import v1_brain_skeleton
        original_state_file = v1_brain_skeleton.STATE_FILE
        v1_brain_skeleton.STATE_FILE = os.path.join(temp_dir, "nonexistent.json")

        try:
            state = load_state()

            assert state["last_regime"] is None
            assert state["last_allocation_date"] is None
            assert state["engine_weights"]["CASH"] == 1.0
        finally:
            v1_brain_skeleton.STATE_FILE = original_state_file

    def test_save_and_load_state(self, temp_dir, monkeypatch):
        """Test saving and loading state."""
        import v1_brain_skeleton
        original_state_file = v1_brain_skeleton.STATE_FILE
        v1_brain_skeleton.STATE_FILE = os.path.join(temp_dir, "test_state.json")

        try:
            state = {
                "last_regime": "RISK_ON",
                "last_allocation_date": "2026-01-15",
                "engine_weights": {
                    "CASH": 0.12,
                    "EQUITY": 0.50,
                    "DEFENSIVE": 0.20,
                    "REAL_ASSET": 0.18,
                }
            }

            save_state(state)
            loaded = load_state()

            assert loaded["last_regime"] == "RISK_ON"
            assert loaded["engine_weights"]["EQUITY"] == pytest.approx(0.50, rel=0.01)
        finally:
            v1_brain_skeleton.STATE_FILE = original_state_file

    def test_load_state_validates_data(self, temp_dir, monkeypatch):
        """Test that load_state validates and sanitizes data."""
        import v1_brain_skeleton
        original_state_file = v1_brain_skeleton.STATE_FILE
        state_file = os.path.join(temp_dir, "invalid_state.json")
        v1_brain_skeleton.STATE_FILE = state_file

        try:
            # Write invalid state directly
            with open(state_file, 'w') as f:
                json.dump({
                    "last_regime": "INVALID_REGIME",
                    "engine_weights": {"CASH": -1.0}  # Invalid
                }, f)

            loaded = load_state()

            # Should be sanitized
            assert loaded["last_regime"] is None
            assert loaded["engine_weights"]["CASH"] == 1.0  # Default
        finally:
            v1_brain_skeleton.STATE_FILE = original_state_file


class TestFrozenParameters:
    """Tests for frozen V1 parameters."""

    def test_delta_value(self):
        """Test that DELTA has expected value."""
        assert DELTA == 0.15

    def test_alpha_value(self):
        """Test that ALPHA has expected value."""
        assert ALPHA == 0.33

    def test_cooldown_weeks_value(self):
        """Test that COOLDOWN_WEEKS has expected value."""
        assert COOLDOWN_WEEKS == 3

    def test_engines_list(self):
        """Test that ENGINES contains expected values."""
        assert set(ENGINES) == {"CASH", "EQUITY", "DEFENSIVE", "REAL_ASSET"}
