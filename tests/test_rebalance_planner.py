"""
Tests for execution/rebalance_planner.py
"""

import pytest
import datetime

from execution import (
    RebalancePlanner, RebalancePlan, CurrentPositions,
    Trade, TradeAction, HaltReason,
    create_current_positions, translate_brain_output
)


class TestRebalancePlanner:
    """Tests for RebalancePlanner class."""

    @pytest.fixture
    def planner(self):
        """Create a RebalancePlanner instance."""
        return RebalancePlanner()

    @pytest.fixture
    def current_all_cash(self):
        """Current positions: 100% cash."""
        return create_current_positions({}, 1_000_000.0)

    @pytest.fixture
    def target_risk_on(self, sample_brain_output):
        """Target positions for RISK_ON."""
        return translate_brain_output(sample_brain_output, 1_000_000.0)

    def test_plan_from_cash_to_invested(self, planner, current_all_cash, target_risk_on):
        """Test planning from 100% cash to invested positions."""
        plan = planner.plan(target_risk_on, current_all_cash, regime_changed=True)

        assert isinstance(plan, RebalancePlan)
        assert plan.should_execute is True
        assert plan.halt_reason is None
        assert len(plan.trades) == 3  # BUY SPY, TLT, GLD

        # All trades should be BUY
        for trade in plan.trades:
            assert trade.action == TradeAction.BUY

        # Check total buy amount
        assert plan.total_buy_amount == pytest.approx(880_000.0, rel=0.01)  # 88%
        assert plan.total_sell_amount == 0

    def test_plan_within_tolerance_no_trades(self, planner, sample_brain_output):
        """Test that positions within tolerance don't generate trades."""
        # Create current positions very close to target
        current = create_current_positions(
            {"SPY": 500_000.0, "TLT": 200_000.0, "GLD": 180_000.0},
            120_000.0
        )
        target = translate_brain_output(sample_brain_output, 1_000_000.0)

        plan = planner.plan(target, current, regime_changed=False)

        assert plan.should_execute is False
        assert len(plan.trades) == 0

    def test_plan_sell_to_cash(self, planner, sample_brain_output):
        """Test planning to sell positions for RISK_OFF."""
        # Current: invested
        current = create_current_positions(
            {"SPY": 500_000.0, "TLT": 200_000.0, "GLD": 180_000.0},
            120_000.0
        )
        # Target: 100% cash
        target_cash = translate_brain_output(
            {"engine_weights": {"CASH": 1.0, "EQUITY": 0.0, "DEFENSIVE": 0.0, "REAL_ASSET": 0.0}},
            1_000_000.0
        )

        plan = planner.plan(target_cash, current, regime_changed=True)

        assert plan.should_execute is True
        assert len(plan.trades) == 3  # SELL SPY, TLT, GLD

        # All trades should be SELL
        for trade in plan.trades:
            assert trade.action == TradeAction.SELL

        assert plan.total_sell_amount == pytest.approx(880_000.0, rel=0.01)
        assert plan.total_buy_amount == 0

    def test_filters_small_trades(self, planner):
        """Test that trades below minimum are filtered out."""
        # Create positions with tiny difference
        current = create_current_positions(
            {"SPY": 500_050.0},  # $50 more than target
            499_950.0
        )
        target = translate_brain_output(
            {"engine_weights": {"CASH": 0.5, "EQUITY": 0.5, "DEFENSIVE": 0.0, "REAL_ASSET": 0.0}},
            1_000_000.0
        )

        plan = planner.plan(target, current, regime_changed=False)

        # Tiny $50 difference should be filtered
        assert plan.should_execute is False

    def test_halt_on_leverage(self, planner):
        """Test that leverage detection triggers halt."""
        # Current positions exceed equity (leverage)
        current = CurrentPositions(
            positions={"SPY": 1_200_000.0},  # More than equity
            cash=-200_000.0,  # Negative cash = margin
            timestamp=datetime.datetime.now(),
            total_equity=1_000_000.0
        )
        target = translate_brain_output(
            {"engine_weights": {"CASH": 1.0, "EQUITY": 0.0, "DEFENSIVE": 0.0, "REAL_ASSET": 0.0}},
            1_000_000.0
        )

        plan = planner.plan(target, current, regime_changed=True)

        assert plan.halt_reason == HaltReason.LEVERAGE_DETECTED
        assert plan.should_execute is False

    def test_halt_on_short_position(self, planner):
        """Test that short position detection triggers halt."""
        # Current has negative position (short)
        current = CurrentPositions(
            positions={"SPY": -100_000.0},  # Short position
            cash=1_100_000.0,
            timestamp=datetime.datetime.now(),
            total_equity=1_000_000.0
        )
        target = translate_brain_output(
            {"engine_weights": {"CASH": 1.0, "EQUITY": 0.0, "DEFENSIVE": 0.0, "REAL_ASSET": 0.0}},
            1_000_000.0
        )

        plan = planner.plan(target, current, regime_changed=True)

        assert plan.halt_reason == HaltReason.SHORT_DETECTED
        assert plan.should_execute is False

    def test_halt_on_stale_positions(self, planner):
        """Test that stale position data triggers halt."""
        # Positions from 10 minutes ago (stale)
        old_timestamp = datetime.datetime.now() - datetime.timedelta(minutes=10)
        current = CurrentPositions(
            positions={"SPY": 500_000.0},
            cash=500_000.0,
            timestamp=old_timestamp,
            total_equity=1_000_000.0
        )
        target = translate_brain_output(
            {"engine_weights": {"CASH": 1.0, "EQUITY": 0.0, "DEFENSIVE": 0.0, "REAL_ASSET": 0.0}},
            1_000_000.0
        )

        plan = planner.plan(target, current, regime_changed=True)

        assert plan.halt_reason == HaltReason.STALE_POSITIONS
        assert plan.should_execute is False

    def test_halt_on_equity_mismatch(self, planner, sample_brain_output):
        """Test that large equity mismatch triggers halt."""
        # Current equity significantly different from target
        current = create_current_positions({}, 500_000.0)  # $500k
        target = translate_brain_output(sample_brain_output, 1_000_000.0)  # $1M

        plan = planner.plan(target, current, regime_changed=True)

        assert plan.halt_reason == HaltReason.EQUITY_MISMATCH
        assert plan.should_execute is False

    def test_force_rebalance_ignores_tolerance(self, planner, sample_brain_output):
        """Test that force_rebalance ignores tolerance check."""
        # Positions within tolerance
        current = create_current_positions(
            {"SPY": 490_000.0, "TLT": 195_000.0, "GLD": 175_000.0},
            140_000.0
        )
        target = translate_brain_output(sample_brain_output, 1_000_000.0)

        # Normal plan should not execute (within tolerance)
        plan_normal = planner.plan(target, current, regime_changed=False, force_rebalance=False)
        assert plan_normal.should_execute is False

        # Forced plan should execute
        plan_forced = planner.plan(target, current, regime_changed=False, force_rebalance=True)
        assert plan_forced.should_execute is True

    def test_to_dict(self, planner, current_all_cash, target_risk_on):
        """Test that RebalancePlan.to_dict() works."""
        plan = planner.plan(target_risk_on, current_all_cash, regime_changed=True)

        plan_dict = plan.to_dict()

        assert "timestamp" in plan_dict
        assert "should_execute" in plan_dict
        assert "trades" in plan_dict
        assert "total_buy_amount" in plan_dict
        assert "total_sell_amount" in plan_dict


class TestCreateCurrentPositions:
    """Tests for create_current_positions function."""

    def test_creates_valid_positions(self, sample_positions):
        """Test creating current positions from dict."""
        cash = 120_000.0
        result = create_current_positions(sample_positions, cash)

        assert isinstance(result, CurrentPositions)
        assert result.cash == cash
        assert result.positions == sample_positions
        assert result.total_equity == pytest.approx(1_000_000.0)

    def test_empty_positions(self):
        """Test with no positions (100% cash)."""
        result = create_current_positions({}, 1_000_000.0)

        assert result.total_equity == 1_000_000.0
        assert len(result.positions) == 0
        assert result.cash == 1_000_000.0

    def test_timestamp_is_recent(self):
        """Test that timestamp is set to now."""
        result = create_current_positions({}, 1_000_000.0)

        time_diff = datetime.datetime.now() - result.timestamp
        assert time_diff.total_seconds() < 1  # Within 1 second
