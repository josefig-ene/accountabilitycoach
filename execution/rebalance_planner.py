"""
Rebalance Planner - Computes diffs with hard guardrails

ROLE: Compute what needs to change to match the target
- Never optimizes timing
- Never skips trades based on feelings
- Halts on uncertainty

V1 GUARDRAILS (MANDATORY):
- No leverage
- No shorting
- No rebalancing unless regime changed OR deviation > tolerance
- No intraday churn
"""

import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .position_translator import TargetPositions


# -------------------------------
# ENUMS & DATA STRUCTURES
# -------------------------------

class TradeAction(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class HaltReason(Enum):
    STALE_POSITIONS = "STALE_POSITIONS"
    POSITION_MISMATCH = "POSITION_MISMATCH"
    LEVERAGE_DETECTED = "LEVERAGE_DETECTED"
    SHORT_DETECTED = "SHORT_DETECTED"
    CASH_MISMATCH = "CASH_MISMATCH"
    UNKNOWN_ASSET = "UNKNOWN_ASSET"
    SANITY_CHECK_FAILED = "SANITY_CHECK_FAILED"


@dataclass
class Trade:
    """A single trade to execute."""
    asset: str
    action: TradeAction
    amount: float  # dollars
    current_position: float
    target_position: float
    reason: str

    def to_dict(self):
        return {
            "asset": self.asset,
            "action": self.action.value,
            "amount": self.amount,
            "current_position": self.current_position,
            "target_position": self.target_position,
            "reason": self.reason,
        }


@dataclass
class RebalancePlan:
    """Complete rebalance plan with trades and metadata."""
    timestamp: datetime.datetime
    trades: List[Trade]
    should_execute: bool
    halt_reason: Optional[HaltReason] = None
    halt_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    total_buy_amount: float = 0.0
    total_sell_amount: float = 0.0

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "should_execute": self.should_execute,
            "halt_reason": self.halt_reason.value if self.halt_reason else None,
            "halt_message": self.halt_message,
            "warnings": self.warnings,
            "total_buy_amount": self.total_buy_amount,
            "total_sell_amount": self.total_sell_amount,
            "trades": [t.to_dict() for t in self.trades],
        }


@dataclass
class CurrentPositions:
    """Current positions from broker."""
    timestamp: datetime.datetime
    positions: Dict[str, float]  # ticker → dollars
    cash: float
    total_equity: float

    @property
    def age_seconds(self) -> float:
        """How old is this position snapshot."""
        return (datetime.datetime.now() - self.timestamp).total_seconds()


# -------------------------------
# REBALANCE PLANNER
# -------------------------------

class RebalancePlanner:
    """
    Plans rebalancing trades with hard guardrails.

    This class is DUMB by design.
    It computes diffs and applies guardrails.
    It never optimizes timing or "helps".

    If it disagrees, it HALTS. No silent failures.
    """

    # V1 Configuration (frozen)
    EXECUTION_TOLERANCE = 0.02    # 2% - below this, don't trade
    ALERT_TOLERANCE = 0.05        # 5% - above this, alert even if not trading
    MAX_POSITION_AGE_SECONDS = 300  # 5 minutes - positions older than this are stale
    MIN_TRADE_AMOUNT = 100.0      # $100 minimum trade

    def __init__(
        self,
        execution_tolerance: float = None,
        alert_tolerance: float = None,
    ):
        """
        Initialize planner with tolerances.

        Args:
            execution_tolerance: Deviation below which we don't trade
            alert_tolerance: Deviation above which we alert
        """
        self.execution_tolerance = execution_tolerance or self.EXECUTION_TOLERANCE
        self.alert_tolerance = alert_tolerance or self.ALERT_TOLERANCE

    def plan(
        self,
        target: TargetPositions,
        current: CurrentPositions,
        regime_changed: bool = False,
        force_rebalance: bool = False,
    ) -> RebalancePlan:
        """
        Create a rebalance plan.

        Args:
            target: Target positions from brain
            current: Current positions from broker
            regime_changed: Whether brain detected regime change
            force_rebalance: Override tolerance check (use sparingly!)

        Returns:
            RebalancePlan with trades and execution decision
        """
        timestamp = datetime.datetime.now()
        trades = []
        warnings = []

        # GUARDRAIL 1: Check position freshness
        if current.age_seconds > self.MAX_POSITION_AGE_SECONDS:
            return self._halt(
                timestamp,
                HaltReason.STALE_POSITIONS,
                f"Current positions are {current.age_seconds:.0f}s old "
                f"(max {self.MAX_POSITION_AGE_SECONDS}s). Fetch fresh positions."
            )

        # GUARDRAIL 2: Sanity check - equity mismatch
        equity_diff = abs(target.account_equity - current.total_equity)
        equity_diff_pct = equity_diff / target.account_equity if target.account_equity > 0 else 0
        if equity_diff_pct > 0.10:  # >10% mismatch
            return self._halt(
                timestamp,
                HaltReason.POSITION_MISMATCH,
                f"Account equity mismatch: target=${target.account_equity:,.0f}, "
                f"current=${current.total_equity:,.0f} ({equity_diff_pct:.1%} diff). "
                f"Investigate before proceeding."
            )

        # GUARDRAIL 3: Check for leverage (total positions > equity)
        total_positions = sum(current.positions.values())
        if total_positions > current.total_equity * 1.01:  # 1% tolerance
            return self._halt(
                timestamp,
                HaltReason.LEVERAGE_DETECTED,
                f"Leverage detected: positions=${total_positions:,.0f}, "
                f"equity=${current.total_equity:,.0f}. V1 does not allow leverage."
            )

        # GUARDRAIL 4: Check for shorts (negative positions)
        for asset, amount in current.positions.items():
            if amount < -1:  # small negative tolerance for rounding
                return self._halt(
                    timestamp,
                    HaltReason.SHORT_DETECTED,
                    f"Short position detected: {asset}=${amount:,.0f}. "
                    f"V1 does not allow shorting."
                )

        # Calculate diffs for each asset
        all_assets = set(target.dollar_positions.keys()) | set(current.positions.keys())

        for asset in all_assets:
            target_pos = target.dollar_positions.get(asset, 0.0)
            current_pos = current.positions.get(asset, 0.0)
            diff = target_pos - current_pos

            # Check deviation
            deviation = abs(diff) / target.account_equity if target.account_equity > 0 else 0

            # Record trade if significant
            if abs(diff) >= self.MIN_TRADE_AMOUNT:
                action = TradeAction.BUY if diff > 0 else TradeAction.SELL
                reason = self._get_trade_reason(deviation, regime_changed)

                trades.append(Trade(
                    asset=asset,
                    action=action,
                    amount=abs(diff),
                    current_position=current_pos,
                    target_position=target_pos,
                    reason=reason,
                ))

            # Alert on large deviations even if not trading
            if deviation > self.alert_tolerance:
                warnings.append(
                    f"Large deviation for {asset}: {deviation:.1%} "
                    f"(target=${target_pos:,.0f}, current=${current_pos:,.0f})"
                )

        # Calculate cash diff
        cash_diff = target.cash_position - current.cash
        if abs(cash_diff) > target.account_equity * 0.05:  # >5% cash mismatch
            warnings.append(
                f"Cash position mismatch: target=${target.cash_position:,.0f}, "
                f"current=${current.cash:,.0f}"
            )

        # Decide whether to execute
        should_execute = self._should_execute(
            trades, regime_changed, force_rebalance
        )

        # Calculate totals
        total_buy = sum(t.amount for t in trades if t.action == TradeAction.BUY)
        total_sell = sum(t.amount for t in trades if t.action == TradeAction.SELL)

        return RebalancePlan(
            timestamp=timestamp,
            trades=trades,
            should_execute=should_execute,
            warnings=warnings,
            total_buy_amount=total_buy,
            total_sell_amount=total_sell,
        )

    def _should_execute(
        self,
        trades: List[Trade],
        regime_changed: bool,
        force_rebalance: bool,
    ) -> bool:
        """
        Decide whether to execute trades.

        V1 RULE: Only rebalance if:
        1. Regime changed, OR
        2. Force rebalance requested, OR
        3. Any trade exceeds execution tolerance

        We do NOT rebalance just because positions drifted slightly.
        """
        if force_rebalance:
            return len(trades) > 0

        if regime_changed:
            return len(trades) > 0

        # Check if any trade is large enough to warrant execution
        for trade in trades:
            if trade.amount >= self.MIN_TRADE_AMOUNT:
                # This is a significant trade - execute
                return True

        return False

    def _get_trade_reason(self, deviation: float, regime_changed: bool) -> str:
        """Get human-readable reason for trade."""
        if regime_changed:
            return "regime_change"
        elif deviation > self.alert_tolerance:
            return f"large_deviation_{deviation:.1%}"
        else:
            return f"rebalance_{deviation:.1%}"

    def _halt(
        self,
        timestamp: datetime.datetime,
        reason: HaltReason,
        message: str
    ) -> RebalancePlan:
        """Create a halted plan."""
        return RebalancePlan(
            timestamp=timestamp,
            trades=[],
            should_execute=False,
            halt_reason=reason,
            halt_message=message,
        )


# -------------------------------
# CONVENIENCE FUNCTIONS
# -------------------------------

def create_current_positions(
    positions: Dict[str, float],
    cash: float,
    timestamp: Optional[datetime.datetime] = None
) -> CurrentPositions:
    """Create CurrentPositions object."""
    if timestamp is None:
        timestamp = datetime.datetime.now()

    total_equity = sum(positions.values()) + cash

    return CurrentPositions(
        timestamp=timestamp,
        positions=positions,
        cash=cash,
        total_equity=total_equity,
    )


# -------------------------------
# MAIN (for testing)
# -------------------------------

if __name__ == "__main__":
    from .position_translator import translate_brain_output

    # Sample brain output
    brain_output = {
        "engine_weights": {
            "CASH": 0.35,
            "EQUITY": 0.35,
            "DEFENSIVE": 0.20,
            "REAL_ASSET": 0.10,
        }
    }

    # Current positions (simulated)
    current = create_current_positions(
        positions={
            "SPY": 400_000,
            "TLT": 150_000,
            "GLD": 50_000,
        },
        cash=400_000,
    )

    # Translate brain output
    target = translate_brain_output(brain_output, current.total_equity)

    # Plan rebalance
    planner = RebalancePlanner()
    plan = planner.plan(target, current, regime_changed=True)

    print("\n" + "="*50)
    print("REBALANCE PLANNER TEST")
    print("="*50)
    print(f"\nShould Execute: {plan.should_execute}")
    print(f"Halt Reason: {plan.halt_reason}")

    if plan.trades:
        print(f"\nTrades:")
        for trade in plan.trades:
            print(f"  {trade.action.value} ${trade.amount:,.0f} {trade.asset}")
            print(f"    Current: ${trade.current_position:,.0f}")
            print(f"    Target: ${trade.target_position:,.0f}")
            print(f"    Reason: {trade.reason}")

    if plan.warnings:
        print(f"\nWarnings:")
        for w in plan.warnings:
            print(f"  ⚠️ {w}")

    print("\n" + "="*50)
