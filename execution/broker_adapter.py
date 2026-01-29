"""
Broker Adapter - Abstract interface and Paper Broker implementation

ROLE: Translate trades into broker-specific orders
- Never decides WHAT to trade (that's the planner)
- Only handles HOW to trade
- Reports fills back honestly

V1: Paper broker only (no real money)
Future: IBKR, Alpaca adapters
"""

import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import os
import tempfile

from .rebalance_planner import Trade, TradeAction, RebalancePlan


# -------------------------------
# CONSTANTS
# -------------------------------

MAX_TRADE_HISTORY = 100  # Maximum trades to keep in history


# -------------------------------
# ENUMS & DATA STRUCTURES
# -------------------------------

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIAL_FILL = "PARTIAL_FILL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class FillStatus(Enum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"
    NONE = "NONE"


@dataclass
class Order:
    """A broker order."""
    order_id: str
    asset: str
    action: TradeAction
    amount: float  # dollars
    order_type: OrderType
    limit_price: Optional[float] = None
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    status: OrderStatus = OrderStatus.PENDING

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "asset": self.asset,
            "action": self.action.value,
            "amount": self.amount,
            "order_type": self.order_type.value,
            "limit_price": self.limit_price,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
        }


@dataclass
class Fill:
    """A fill report from broker."""
    order_id: str
    asset: str
    action: TradeAction
    requested_amount: float
    filled_amount: float
    fill_price: float
    timestamp: datetime.datetime
    status: FillStatus
    commission: float = 0.0
    message: Optional[str] = None

    @property
    def slippage(self) -> float:
        """Slippage as percentage (paper broker: always 0)."""
        return 0.0  # V1 paper broker assumes no slippage

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "asset": self.asset,
            "action": self.action.value,
            "requested_amount": self.requested_amount,
            "filled_amount": self.filled_amount,
            "fill_price": self.fill_price,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "commission": self.commission,
            "message": self.message,
        }


@dataclass
class ExecutionReport:
    """Summary of execution attempt."""
    timestamp: datetime.datetime
    orders: List[Order]
    fills: List[Fill]
    total_bought: float
    total_sold: float
    total_commission: float
    all_filled: bool
    errors: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "orders": [o.to_dict() for o in self.orders],
            "fills": [f.to_dict() for f in self.fills],
            "total_bought": self.total_bought,
            "total_sold": self.total_sold,
            "total_commission": self.total_commission,
            "all_filled": self.all_filled,
            "errors": self.errors,
        }


# -------------------------------
# ABSTRACT BROKER ADAPTER
# -------------------------------

class BrokerAdapter(ABC):
    """
    Abstract interface for broker adapters.

    All brokers must implement these methods.
    The execution layer doesn't care which broker is used.
    """

    @abstractmethod
    def get_positions(self) -> Dict[str, float]:
        """
        Get current positions from broker.

        Returns:
            Dict of asset → dollar value
        """
        pass

    @abstractmethod
    def get_cash(self) -> float:
        """Get current cash balance."""
        pass

    @abstractmethod
    def get_equity(self) -> float:
        """Get total account equity (positions + cash)."""
        pass

    @abstractmethod
    def submit_order(self, order: Order) -> Tuple[bool, str]:
        """
        Submit an order to the broker.

        Returns:
            (success, message)
        """
        pass

    @abstractmethod
    def get_fill(self, order_id: str) -> Optional[Fill]:
        """Get fill status for an order."""
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        pass

    @abstractmethod
    def execute_plan(self, plan: RebalancePlan) -> ExecutionReport:
        """
        Execute a complete rebalance plan.

        This is the main entry point for execution.
        """
        pass


# -------------------------------
# PAPER BROKER IMPLEMENTATION
# -------------------------------

class PaperBroker(BrokerAdapter):
    """
    Paper trading broker for V1.

    - Simulates instant fills at current price
    - Tracks positions in memory and file
    - No slippage, no partial fills
    - Perfect for testing
    """

    STATE_FILE = "paper_broker_state.json"

    def __init__(
        self,
        initial_cash: float = 1_000_000.0,
        state_file: Optional[str] = None,
    ):
        """
        Initialize paper broker.

        Args:
            initial_cash: Starting cash balance
            state_file: Path to state file (for persistence)
        """
        self.state_file = state_file or self.STATE_FILE
        self._order_counter = 0

        # Load or initialize state
        state = self._load_state()
        if state:
            self.positions = state.get('positions', {})
            self.cash = state.get('cash', initial_cash)
            self.trade_history = state.get('trade_history', [])
        else:
            self.positions = {}
            self.cash = initial_cash
            self.trade_history = []

    def _load_state(self) -> Optional[dict]:
        """Load and validate state from file."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)

                # Validate and sanitize state
                validated = {
                    'positions': {},
                    'cash': 0.0,
                    'trade_history': [],
                }

                # Validate cash (must be non-negative)
                cash = state.get('cash', 0.0)
                if isinstance(cash, (int, float)) and cash >= 0:
                    validated['cash'] = float(cash)

                # Validate positions (must be non-negative floats)
                positions = state.get('positions', {})
                if isinstance(positions, dict):
                    for asset, value in positions.items():
                        if isinstance(value, (int, float)) and value >= 0:
                            validated['positions'][str(asset)] = float(value)

                # Bound trade history
                history = state.get('trade_history', [])
                if isinstance(history, list):
                    validated['trade_history'] = history[-MAX_TRADE_HISTORY:]

                return validated
        except json.JSONDecodeError:
            print(f"Warning: Corrupted broker state file, using defaults")
        except Exception as e:
            print(f"Warning: Could not load paper broker state: {e}")
        return None

    def _save_state(self):
        """Atomically save state to file."""
        # Bound trade history before saving
        self.trade_history = self.trade_history[-MAX_TRADE_HISTORY:]

        state = {
            'positions': self.positions,
            'cash': self.cash,
            'trade_history': self.trade_history,
            'last_updated': datetime.datetime.now().isoformat(),
        }

        # Atomic write using temp file + rename
        try:
            dir_path = os.path.dirname(self.state_file) or '.'
            fd, temp_path = tempfile.mkstemp(
                dir=dir_path,
                prefix='.broker_state.',
                suffix='.tmp'
            )
            try:
                with os.fdopen(fd, 'w') as f:
                    json.dump(state, f, indent=2)
                os.replace(temp_path, self.state_file)
            except Exception:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                raise
        except Exception as e:
            print(f"Warning: Could not save paper broker state: {e}")

    def _generate_order_id(self) -> str:
        """Generate unique order ID."""
        self._order_counter += 1
        return f"PAPER-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{self._order_counter:04d}"

    # --- Interface Implementation ---

    def get_positions(self) -> Dict[str, float]:
        """Get current positions."""
        return self.positions.copy()

    def get_cash(self) -> float:
        """Get cash balance."""
        return self.cash

    def get_equity(self) -> float:
        """Get total equity."""
        return sum(self.positions.values()) + self.cash

    def submit_order(self, order: Order) -> Tuple[bool, str]:
        """
        Submit order (paper broker: instant fill).

        Paper broker simulates instant, perfect fills.
        """
        # Validate order
        if order.amount <= 0:
            return False, f"Invalid order amount: {order.amount}"

        if order.action == TradeAction.BUY:
            # Check cash availability
            if order.amount > self.cash:
                return False, f"Insufficient cash: need ${order.amount:,.0f}, have ${self.cash:,.0f}"

            # Execute buy
            self.cash -= order.amount
            current = self.positions.get(order.asset, 0.0)
            self.positions[order.asset] = current + order.amount

        elif order.action == TradeAction.SELL:
            # Check position availability
            current = self.positions.get(order.asset, 0.0)
            if order.amount > current + 1:  # $1 tolerance
                return False, f"Insufficient position: need ${order.amount:,.0f}, have ${current:,.0f}"

            # Execute sell
            self.positions[order.asset] = max(0, current - order.amount)
            self.cash += order.amount

            # Clean up zero positions
            if self.positions[order.asset] < 1:
                del self.positions[order.asset]

        else:
            return False, f"Unknown action: {order.action}"

        # Record trade
        self.trade_history.append({
            'order_id': order.order_id,
            'asset': order.asset,
            'action': order.action.value,
            'amount': order.amount,
            'timestamp': datetime.datetime.now().isoformat(),
        })

        # Persist state
        self._save_state()

        order.status = OrderStatus.FILLED
        return True, "Order filled"

    def get_fill(self, order_id: str) -> Optional[Fill]:
        """Get fill for order (paper broker: always instant full fill)."""
        # Find order in history
        for trade in reversed(self.trade_history):
            if trade['order_id'] == order_id:
                return Fill(
                    order_id=order_id,
                    asset=trade['asset'],
                    action=TradeAction(trade['action']),
                    requested_amount=trade['amount'],
                    filled_amount=trade['amount'],
                    fill_price=1.0,  # Paper broker doesn't track prices
                    timestamp=datetime.datetime.fromisoformat(trade['timestamp']),
                    status=FillStatus.FULL,
                    commission=0.0,
                    message="Paper fill - instant execution",
                )
        return None

    def cancel_order(self, order_id: str) -> bool:
        """Cancel order (paper broker: always succeeds, but orders are instant)."""
        return True  # Paper broker has instant fills, so nothing to cancel

    def execute_plan(self, plan: RebalancePlan) -> ExecutionReport:
        """
        Execute a complete rebalance plan.

        V1 Paper Broker Strategy:
        1. Execute all sells first (to free up cash)
        2. Then execute all buys
        3. Report results
        """
        timestamp = datetime.datetime.now()
        orders = []
        fills = []
        errors = []

        if not plan.should_execute:
            return ExecutionReport(
                timestamp=timestamp,
                orders=[],
                fills=[],
                total_bought=0.0,
                total_sold=0.0,
                total_commission=0.0,
                all_filled=True,
                errors=["Plan marked as should_execute=False"],
            )

        if plan.halt_reason:
            return ExecutionReport(
                timestamp=timestamp,
                orders=[],
                fills=[],
                total_bought=0.0,
                total_sold=0.0,
                total_commission=0.0,
                all_filled=False,
                errors=[f"Plan halted: {plan.halt_message}"],
            )

        # Separate sells and buys
        sells = [t for t in plan.trades if t.action == TradeAction.SELL]
        buys = [t for t in plan.trades if t.action == TradeAction.BUY]

        # Execute sells first
        for trade in sells:
            order = Order(
                order_id=self._generate_order_id(),
                asset=trade.asset,
                action=trade.action,
                amount=trade.amount,
                order_type=OrderType.MARKET,
            )
            orders.append(order)

            success, message = self.submit_order(order)
            if success:
                fill = self.get_fill(order.order_id)
                if fill:
                    fills.append(fill)
            else:
                errors.append(f"Sell {trade.asset} failed: {message}")

        # Execute buys
        for trade in buys:
            order = Order(
                order_id=self._generate_order_id(),
                asset=trade.asset,
                action=trade.action,
                amount=trade.amount,
                order_type=OrderType.MARKET,
            )
            orders.append(order)

            success, message = self.submit_order(order)
            if success:
                fill = self.get_fill(order.order_id)
                if fill:
                    fills.append(fill)
            else:
                errors.append(f"Buy {trade.asset} failed: {message}")

        # Calculate totals
        total_bought = sum(f.filled_amount for f in fills if f.action == TradeAction.BUY)
        total_sold = sum(f.filled_amount for f in fills if f.action == TradeAction.SELL)
        total_commission = sum(f.commission for f in fills)
        all_filled = len(fills) == len(orders) and len(errors) == 0

        return ExecutionReport(
            timestamp=timestamp,
            orders=orders,
            fills=fills,
            total_bought=total_bought,
            total_sold=total_sold,
            total_commission=total_commission,
            all_filled=all_filled,
            errors=errors,
        )

    # --- Paper Broker Specific Methods ---

    def reset(self, initial_cash: float = 1_000_000.0):
        """Reset paper broker to initial state."""
        self.positions = {}
        self.cash = initial_cash
        self.trade_history = []
        self._save_state()

    def set_positions(self, positions: Dict[str, float], cash: float):
        """
        Manually set positions (for testing/simulation).

        Args:
            positions: Dict of asset → dollar value
            cash: Cash balance
        """
        self.positions = positions.copy()
        self.cash = cash
        self._save_state()

    def get_summary(self) -> dict:
        """Get summary of paper broker state."""
        return {
            'equity': self.get_equity(),
            'cash': self.cash,
            'positions': self.positions.copy(),
            'trade_count': len(self.trade_history),
        }


# -------------------------------
# FACTORY FUNCTION
# -------------------------------

def create_broker(broker_type: str = "paper", **kwargs) -> BrokerAdapter:
    """
    Factory function to create broker adapter.

    Args:
        broker_type: Type of broker ("paper", "ibkr", "alpaca")
        **kwargs: Broker-specific arguments

    Returns:
        BrokerAdapter instance
    """
    if broker_type == "paper":
        return PaperBroker(**kwargs)
    elif broker_type == "ibkr":
        raise NotImplementedError("IBKR adapter not implemented in V1")
    elif broker_type == "alpaca":
        raise NotImplementedError("Alpaca adapter not implemented in V1")
    else:
        raise ValueError(f"Unknown broker type: {broker_type}")


# -------------------------------
# MAIN (for testing)
# -------------------------------

if __name__ == "__main__":
    from .position_translator import translate_brain_output
    from .rebalance_planner import RebalancePlanner, create_current_positions

    print("\n" + "="*50)
    print("PAPER BROKER TEST")
    print("="*50)

    # Initialize paper broker
    broker = PaperBroker(initial_cash=1_000_000.0)
    broker.reset()  # Start fresh

    print(f"\nInitial state:")
    print(f"  Equity: ${broker.get_equity():,.0f}")
    print(f"  Cash: ${broker.get_cash():,.0f}")
    print(f"  Positions: {broker.get_positions()}")

    # Simulate brain output (RISK_ON regime)
    brain_output = {
        "engine_weights": {
            "CASH": 0.12,
            "EQUITY": 0.50,
            "DEFENSIVE": 0.20,
            "REAL_ASSET": 0.18,
        }
    }

    # Translate to target positions
    target = translate_brain_output(brain_output, broker.get_equity())
    print(f"\nTarget positions (RISK_ON):")
    for ticker, amount in target.dollar_positions.items():
        print(f"  {ticker}: ${amount:,.0f}")
    print(f"  CASH: ${target.cash_position:,.0f}")

    # Create current positions from broker
    current = create_current_positions(
        broker.get_positions(),
        broker.get_cash(),
    )

    # Plan rebalance
    planner = RebalancePlanner()
    plan = planner.plan(target, current, regime_changed=True)

    print(f"\nRebalance plan:")
    print(f"  Should execute: {plan.should_execute}")
    print(f"  Total buy: ${plan.total_buy_amount:,.0f}")
    print(f"  Total sell: ${plan.total_sell_amount:,.0f}")

    if plan.trades:
        print(f"\n  Trades:")
        for trade in plan.trades:
            print(f"    {trade.action.value} ${trade.amount:,.0f} {trade.asset}")

    # Execute plan
    report = broker.execute_plan(plan)

    print(f"\nExecution report:")
    print(f"  All filled: {report.all_filled}")
    print(f"  Total bought: ${report.total_bought:,.0f}")
    print(f"  Total sold: ${report.total_sold:,.0f}")

    if report.errors:
        print(f"  Errors: {report.errors}")

    print(f"\nFinal state:")
    print(f"  Equity: ${broker.get_equity():,.0f}")
    print(f"  Cash: ${broker.get_cash():,.0f}")
    print(f"  Positions: {broker.get_positions()}")

    print("\n" + "="*50)
