"""
V1 Execution Layer

This module provides clean separation between brain (allocation decisions)
and execution (order management).

ARCHITECTURE:
- Brain outputs engine weights (CASH, EQUITY, DEFENSIVE, REAL_ASSET)
- Execution layer translates to orders and executes

COMPONENTS:
- PositionTranslator: Converts engine weights to dollar positions
- RebalancePlanner: Computes diffs with hard guardrails
- BrokerAdapter: Abstract interface for brokers
- PaperBroker: Paper trading implementation
- ExecutionOrchestrator: Ties everything together

USAGE:
    from execution import ExecutionOrchestrator, PaperBroker

    broker = PaperBroker(initial_cash=1_000_000)
    orchestrator = ExecutionOrchestrator(broker=broker)

    result = orchestrator.execute(
        brain_output={"engine_weights": {...}},
        regime="RISK_ON",
        regime_changed=True,
    )
"""

# Position Translator
from .position_translator import (
    PositionTranslator,
    TargetPositions,
    translate_brain_output,
)

# Rebalance Planner
from .rebalance_planner import (
    RebalancePlanner,
    RebalancePlan,
    CurrentPositions,
    Trade,
    TradeAction,
    HaltReason,
    create_current_positions,
)

# Broker Adapter
from .broker_adapter import (
    BrokerAdapter,
    PaperBroker,
    Order,
    OrderType,
    OrderStatus,
    Fill,
    FillStatus,
    ExecutionReport,
    create_broker,
)

# Execution Orchestrator
from .execution_orchestrator import (
    ExecutionOrchestrator,
    ExecutionResult,
    execute_brain_output,
)

__all__ = [
    # Position Translator
    "PositionTranslator",
    "TargetPositions",
    "translate_brain_output",
    # Rebalance Planner
    "RebalancePlanner",
    "RebalancePlan",
    "CurrentPositions",
    "Trade",
    "TradeAction",
    "HaltReason",
    "create_current_positions",
    # Broker Adapter
    "BrokerAdapter",
    "PaperBroker",
    "Order",
    "OrderType",
    "OrderStatus",
    "Fill",
    "FillStatus",
    "ExecutionReport",
    "create_broker",
    # Execution Orchestrator
    "ExecutionOrchestrator",
    "ExecutionResult",
    "execute_brain_output",
]
