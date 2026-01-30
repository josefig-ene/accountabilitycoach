"""
Tests for execution/broker_adapter.py
"""

import pytest
import os

from execution import (
    PaperBroker, Order, OrderType, OrderStatus,
    Fill, FillStatus, ExecutionReport,
    create_broker, TradeAction,
    RebalancePlanner, create_current_positions, translate_brain_output
)


class TestPaperBroker:
    """Tests for PaperBroker class."""

    def test_initial_state(self, paper_broker):
        """Test initial broker state."""
        assert paper_broker.get_cash() == 1_000_000.0
        assert paper_broker.get_equity() == 1_000_000.0
        assert paper_broker.get_positions() == {}

    def test_reset(self, paper_broker):
        """Test resetting broker to initial state."""
        # Make some trades first
        order = Order(
            order_id="test-1",
            asset="SPY",
            action=TradeAction.BUY,
            amount=100_000.0,
            order_type=OrderType.MARKET,
        )
        paper_broker.submit_order(order)

        # Reset
        paper_broker.reset(initial_cash=500_000.0)

        assert paper_broker.get_cash() == 500_000.0
        assert paper_broker.get_positions() == {}
        assert len(paper_broker.trade_history) == 0

    def test_buy_order(self, paper_broker):
        """Test executing a buy order."""
        order = Order(
            order_id="test-buy",
            asset="SPY",
            action=TradeAction.BUY,
            amount=100_000.0,
            order_type=OrderType.MARKET,
        )

        success, message = paper_broker.submit_order(order)

        assert success is True
        assert paper_broker.get_cash() == 900_000.0
        assert paper_broker.get_positions()["SPY"] == 100_000.0

    def test_sell_order(self, paper_broker):
        """Test executing a sell order."""
        # First buy
        buy_order = Order(
            order_id="test-buy",
            asset="SPY",
            action=TradeAction.BUY,
            amount=100_000.0,
            order_type=OrderType.MARKET,
        )
        paper_broker.submit_order(buy_order)

        # Then sell
        sell_order = Order(
            order_id="test-sell",
            asset="SPY",
            action=TradeAction.SELL,
            amount=50_000.0,
            order_type=OrderType.MARKET,
        )
        success, message = paper_broker.submit_order(sell_order)

        assert success is True
        assert paper_broker.get_cash() == 950_000.0
        assert paper_broker.get_positions()["SPY"] == 50_000.0

    def test_buy_insufficient_cash(self, paper_broker):
        """Test that buy fails with insufficient cash."""
        order = Order(
            order_id="test-big-buy",
            asset="SPY",
            action=TradeAction.BUY,
            amount=2_000_000.0,  # More than available cash
            order_type=OrderType.MARKET,
        )

        success, message = paper_broker.submit_order(order)

        assert success is False
        assert "Insufficient cash" in message
        assert paper_broker.get_cash() == 1_000_000.0  # Unchanged

    def test_sell_insufficient_position(self, paper_broker):
        """Test that sell fails with insufficient position."""
        order = Order(
            order_id="test-sell-no-position",
            asset="SPY",
            action=TradeAction.SELL,
            amount=100_000.0,  # No position to sell
            order_type=OrderType.MARKET,
        )

        success, message = paper_broker.submit_order(order)

        assert success is False
        assert "Insufficient position" in message

    def test_get_fill(self, paper_broker):
        """Test getting fill for an order."""
        order = Order(
            order_id="test-fill",
            asset="SPY",
            action=TradeAction.BUY,
            amount=100_000.0,
            order_type=OrderType.MARKET,
        )
        paper_broker.submit_order(order)

        fill = paper_broker.get_fill("test-fill")

        assert fill is not None
        assert fill.order_id == "test-fill"
        assert fill.asset == "SPY"
        assert fill.filled_amount == 100_000.0
        assert fill.status == FillStatus.FULL

    def test_get_fill_nonexistent(self, paper_broker):
        """Test getting fill for nonexistent order."""
        fill = paper_broker.get_fill("nonexistent")
        assert fill is None

    def test_equity_calculation(self, paper_broker):
        """Test equity calculation with positions."""
        # Buy some positions
        for asset, amount in [("SPY", 300_000), ("TLT", 200_000)]:
            order = Order(
                order_id=f"buy-{asset}",
                asset=asset,
                action=TradeAction.BUY,
                amount=float(amount),
                order_type=OrderType.MARKET,
            )
            paper_broker.submit_order(order)

        # Equity should still be $1M
        assert paper_broker.get_equity() == pytest.approx(1_000_000.0)
        assert paper_broker.get_cash() == 500_000.0
        assert sum(paper_broker.get_positions().values()) == 500_000.0

    def test_trade_history_recorded(self, paper_broker):
        """Test that trades are recorded in history."""
        order = Order(
            order_id="test-history",
            asset="SPY",
            action=TradeAction.BUY,
            amount=100_000.0,
            order_type=OrderType.MARKET,
        )
        paper_broker.submit_order(order)

        assert len(paper_broker.trade_history) == 1
        assert paper_broker.trade_history[0]["asset"] == "SPY"
        assert paper_broker.trade_history[0]["amount"] == 100_000.0

    def test_state_persistence(self, temp_dir):
        """Test that state persists to file."""
        state_file = os.path.join(temp_dir, "broker_state.json")

        # Create broker and make a trade
        broker1 = PaperBroker(initial_cash=1_000_000.0, state_file=state_file)
        order = Order(
            order_id="test-persist",
            asset="SPY",
            action=TradeAction.BUY,
            amount=100_000.0,
            order_type=OrderType.MARKET,
        )
        broker1.submit_order(order)

        # Create new broker instance from same file
        broker2 = PaperBroker(initial_cash=1_000_000.0, state_file=state_file)

        assert broker2.get_cash() == 900_000.0
        assert broker2.get_positions()["SPY"] == 100_000.0

    def test_sell_cleans_up_zero_positions(self, paper_broker):
        """Test that selling all of a position removes it from dict."""
        # Buy
        buy_order = Order(
            order_id="buy",
            asset="SPY",
            action=TradeAction.BUY,
            amount=100_000.0,
            order_type=OrderType.MARKET,
        )
        paper_broker.submit_order(buy_order)

        # Sell all
        sell_order = Order(
            order_id="sell-all",
            asset="SPY",
            action=TradeAction.SELL,
            amount=100_000.0,
            order_type=OrderType.MARKET,
        )
        paper_broker.submit_order(sell_order)

        # Position should be removed
        assert "SPY" not in paper_broker.get_positions()


class TestPaperBrokerExecutePlan:
    """Tests for PaperBroker.execute_plan method."""

    def test_execute_buy_plan(self, paper_broker, sample_brain_output):
        """Test executing a plan with buy orders."""
        # Create target positions
        target = translate_brain_output(sample_brain_output, 1_000_000.0)
        current = create_current_positions({}, 1_000_000.0)

        # Plan the rebalance
        planner = RebalancePlanner()
        plan = planner.plan(target, current, regime_changed=True)

        # Execute
        report = paper_broker.execute_plan(plan)

        assert isinstance(report, ExecutionReport)
        assert report.all_filled is True
        assert len(report.errors) == 0
        assert report.total_bought == pytest.approx(880_000.0, rel=0.01)

        # Check broker state
        positions = paper_broker.get_positions()
        assert "SPY" in positions
        assert "TLT" in positions
        assert "GLD" in positions

    def test_execute_sell_plan(self, paper_broker, sample_brain_output):
        """Test executing a plan with sell orders."""
        # Setup: buy positions first
        target = translate_brain_output(sample_brain_output, 1_000_000.0)
        current = create_current_positions({}, 1_000_000.0)
        planner = RebalancePlanner()
        plan = planner.plan(target, current, regime_changed=True)
        paper_broker.execute_plan(plan)

        # Now plan to sell everything (RISK_OFF)
        target_cash = translate_brain_output(
            {"engine_weights": {"CASH": 1.0, "EQUITY": 0.0, "DEFENSIVE": 0.0, "REAL_ASSET": 0.0}},
            1_000_000.0
        )
        current_invested = create_current_positions(
            paper_broker.get_positions(),
            paper_broker.get_cash()
        )
        sell_plan = planner.plan(target_cash, current_invested, regime_changed=True)

        # Execute sell plan
        report = paper_broker.execute_plan(sell_plan)

        assert report.all_filled is True
        assert report.total_sold == pytest.approx(880_000.0, rel=0.01)
        assert paper_broker.get_cash() == pytest.approx(1_000_000.0, rel=0.01)

    def test_execute_plan_not_executable(self, paper_broker):
        """Test that plan with should_execute=False is not executed."""
        from execution.rebalance_planner import RebalancePlan

        plan = RebalancePlan(
            timestamp=None,
            should_execute=False,
            trades=[],
            total_buy_amount=0,
            total_sell_amount=0,
        )

        report = paper_broker.execute_plan(plan)

        assert report.all_filled is True
        assert len(report.orders) == 0
        assert "should_execute=False" in report.errors[0]


class TestCreateBroker:
    """Tests for create_broker factory function."""

    def test_create_paper_broker(self, temp_dir):
        """Test creating a paper broker."""
        state_file = os.path.join(temp_dir, "broker.json")
        broker = create_broker("paper", state_file=state_file)

        assert isinstance(broker, PaperBroker)

    def test_create_unknown_broker_raises(self):
        """Test that unknown broker type raises error."""
        with pytest.raises(ValueError, match="Unknown broker type"):
            create_broker("unknown_broker")

    def test_create_ibkr_not_implemented(self):
        """Test that IBKR broker raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            create_broker("ibkr")

    def test_create_alpaca_not_implemented(self):
        """Test that Alpaca broker raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            create_broker("alpaca")
