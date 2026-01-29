"""
Execution Orchestrator - Ties the execution layer together

ROLE: Coordinate the complete execution flow
1. Receive brain output (engine weights)
2. Translate to target positions
3. Get current positions from broker
4. Plan rebalance (with guardrails)
5. Execute trades (if approved)
6. Report results

This is the ONLY entry point for execution.
The brain calls this; it doesn't know about translators or planners.
"""

import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field

from .position_translator import PositionTranslator, TargetPositions, translate_brain_output
from .rebalance_planner import (
    RebalancePlanner, RebalancePlan, CurrentPositions,
    create_current_positions, HaltReason
)
from .broker_adapter import (
    BrokerAdapter, PaperBroker, ExecutionReport,
    create_broker
)


# -------------------------------
# DATA STRUCTURES
# -------------------------------

@dataclass
class ExecutionResult:
    """Complete result of an execution attempt."""
    timestamp: datetime.datetime
    success: bool

    # Input
    brain_output: dict
    regime: str
    regime_changed: bool

    # Translation
    target_positions: Optional[TargetPositions] = None

    # Planning
    rebalance_plan: Optional[RebalancePlan] = None

    # Execution
    execution_report: Optional[ExecutionReport] = None

    # State
    final_positions: Dict[str, float] = field(default_factory=dict)
    final_cash: float = 0.0
    final_equity: float = 0.0

    # Errors/Messages
    error: Optional[str] = None
    message: str = ""

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "regime": self.regime,
            "regime_changed": self.regime_changed,
            "target_positions": self.target_positions.to_dict() if self.target_positions else None,
            "rebalance_plan": self.rebalance_plan.to_dict() if self.rebalance_plan else None,
            "execution_report": self.execution_report.to_dict() if self.execution_report else None,
            "final_positions": self.final_positions,
            "final_cash": self.final_cash,
            "final_equity": self.final_equity,
            "error": self.error,
            "message": self.message,
        }


# -------------------------------
# EXECUTION ORCHESTRATOR
# -------------------------------

class ExecutionOrchestrator:
    """
    Orchestrates the complete execution flow.

    This class is the SINGLE entry point for execution.
    It coordinates:
    - Translation (weights → dollars)
    - Planning (diffs + guardrails)
    - Execution (broker orders)

    It NEVER makes allocation decisions.
    It NEVER overrides the brain.
    It only translates and executes.
    """

    def __init__(
        self,
        broker: Optional[BrokerAdapter] = None,
        translator: Optional[PositionTranslator] = None,
        planner: Optional[RebalancePlanner] = None,
        dry_run: bool = False,
    ):
        """
        Initialize orchestrator.

        Args:
            broker: Broker adapter (defaults to PaperBroker)
            translator: Position translator (defaults to V1 config)
            planner: Rebalance planner (defaults to V1 config)
            dry_run: If True, plan but don't execute
        """
        self.broker = broker or PaperBroker()
        self.translator = translator or PositionTranslator()
        self.planner = planner or RebalancePlanner()
        self.dry_run = dry_run

        # Execution history
        self.history = []

    def execute(
        self,
        brain_output: dict,
        regime: str,
        regime_changed: bool = False,
        force_rebalance: bool = False,
    ) -> ExecutionResult:
        """
        Execute brain output through the complete pipeline.

        This is the main entry point.

        Args:
            brain_output: Dict containing 'engine_weights'
            regime: Current detected regime
            regime_changed: Whether regime changed from previous
            force_rebalance: Override tolerance checks

        Returns:
            ExecutionResult with complete execution details
        """
        timestamp = datetime.datetime.now()

        try:
            # Step 1: Get current state from broker
            current_positions = create_current_positions(
                self.broker.get_positions(),
                self.broker.get_cash(),
            )
            account_equity = current_positions.total_equity

            # Step 2: Translate brain output to target positions
            target_positions = translate_brain_output(brain_output, account_equity)

            # Step 3: Plan rebalance
            rebalance_plan = self.planner.plan(
                target=target_positions,
                current=current_positions,
                regime_changed=regime_changed,
                force_rebalance=force_rebalance,
            )

            # Step 4: Check for halt conditions
            if rebalance_plan.halt_reason:
                return ExecutionResult(
                    timestamp=timestamp,
                    success=False,
                    brain_output=brain_output,
                    regime=regime,
                    regime_changed=regime_changed,
                    target_positions=target_positions,
                    rebalance_plan=rebalance_plan,
                    final_positions=self.broker.get_positions(),
                    final_cash=self.broker.get_cash(),
                    final_equity=self.broker.get_equity(),
                    error=f"HALT: {rebalance_plan.halt_reason.value}",
                    message=rebalance_plan.halt_message or "Execution halted",
                )

            # Step 5: Check if execution needed
            if not rebalance_plan.should_execute:
                return ExecutionResult(
                    timestamp=timestamp,
                    success=True,
                    brain_output=brain_output,
                    regime=regime,
                    regime_changed=regime_changed,
                    target_positions=target_positions,
                    rebalance_plan=rebalance_plan,
                    final_positions=self.broker.get_positions(),
                    final_cash=self.broker.get_cash(),
                    final_equity=self.broker.get_equity(),
                    message="No rebalance needed - within tolerance",
                )

            # Step 6: Execute (or dry run)
            if self.dry_run:
                execution_report = None
                message = "DRY RUN - trades not executed"
            else:
                execution_report = self.broker.execute_plan(rebalance_plan)
                if execution_report.all_filled:
                    message = f"Executed {len(execution_report.fills)} trades successfully"
                else:
                    message = f"Partial execution: {len(execution_report.errors)} errors"

            # Step 7: Build result
            result = ExecutionResult(
                timestamp=timestamp,
                success=execution_report.all_filled if execution_report else True,
                brain_output=brain_output,
                regime=regime,
                regime_changed=regime_changed,
                target_positions=target_positions,
                rebalance_plan=rebalance_plan,
                execution_report=execution_report,
                final_positions=self.broker.get_positions(),
                final_cash=self.broker.get_cash(),
                final_equity=self.broker.get_equity(),
                message=message,
            )

            # Record in history
            self.history.append(result)

            return result

        except Exception as e:
            return ExecutionResult(
                timestamp=timestamp,
                success=False,
                brain_output=brain_output,
                regime=regime,
                regime_changed=regime_changed,
                final_positions=self.broker.get_positions(),
                final_cash=self.broker.get_cash(),
                final_equity=self.broker.get_equity(),
                error=str(e),
                message=f"Execution failed: {e}",
            )

    def get_status(self) -> dict:
        """Get current orchestrator status."""
        return {
            "broker_type": type(self.broker).__name__,
            "dry_run": self.dry_run,
            "equity": self.broker.get_equity(),
            "cash": self.broker.get_cash(),
            "positions": self.broker.get_positions(),
            "execution_count": len(self.history),
        }

    def get_last_execution(self) -> Optional[ExecutionResult]:
        """Get the most recent execution result."""
        return self.history[-1] if self.history else None


# -------------------------------
# CONVENIENCE FUNCTIONS
# -------------------------------

def execute_brain_output(
    brain_output: dict,
    regime: str,
    regime_changed: bool = False,
    broker: Optional[BrokerAdapter] = None,
    dry_run: bool = False,
) -> ExecutionResult:
    """
    Convenience function to execute brain output.

    Args:
        brain_output: Dict containing 'engine_weights'
        regime: Current detected regime
        regime_changed: Whether regime changed
        broker: Optional broker (defaults to PaperBroker)
        dry_run: If True, plan but don't execute

    Returns:
        ExecutionResult
    """
    orchestrator = ExecutionOrchestrator(
        broker=broker,
        dry_run=dry_run,
    )
    return orchestrator.execute(
        brain_output=brain_output,
        regime=regime,
        regime_changed=regime_changed,
    )


# -------------------------------
# MAIN (for testing)
# -------------------------------

if __name__ == "__main__":
    print("\n" + "="*60)
    print("EXECUTION ORCHESTRATOR TEST")
    print("="*60)

    # Initialize with paper broker
    broker = PaperBroker(initial_cash=1_000_000.0)
    broker.reset()

    orchestrator = ExecutionOrchestrator(
        broker=broker,
        dry_run=False,  # Actually execute
    )

    print("\n--- Initial Status ---")
    status = orchestrator.get_status()
    print(f"Broker: {status['broker_type']}")
    print(f"Equity: ${status['equity']:,.0f}")
    print(f"Cash: ${status['cash']:,.0f}")
    print(f"Positions: {status['positions']}")

    # Simulate RISK_ON regime
    print("\n--- Executing RISK_ON Allocation ---")
    brain_output_risk_on = {
        "engine_weights": {
            "CASH": 0.12,
            "EQUITY": 0.50,
            "DEFENSIVE": 0.20,
            "REAL_ASSET": 0.18,
        }
    }

    result = orchestrator.execute(
        brain_output=brain_output_risk_on,
        regime="RISK_ON",
        regime_changed=True,
    )

    print(f"\nExecution Result:")
    print(f"  Success: {result.success}")
    print(f"  Message: {result.message}")
    if result.error:
        print(f"  Error: {result.error}")

    if result.target_positions:
        print(f"\n  Target Positions:")
        for ticker, amount in result.target_positions.dollar_positions.items():
            print(f"    {ticker}: ${amount:,.0f}")
        print(f"    CASH: ${result.target_positions.cash_position:,.0f}")

    if result.rebalance_plan:
        print(f"\n  Rebalance Plan:")
        print(f"    Should Execute: {result.rebalance_plan.should_execute}")
        print(f"    Trades: {len(result.rebalance_plan.trades)}")
        for trade in result.rebalance_plan.trades:
            print(f"      {trade.action.value} ${trade.amount:,.0f} {trade.asset}")

    if result.execution_report:
        print(f"\n  Execution Report:")
        print(f"    All Filled: {result.execution_report.all_filled}")
        print(f"    Total Bought: ${result.execution_report.total_bought:,.0f}")
        print(f"    Total Sold: ${result.execution_report.total_sold:,.0f}")

    print(f"\n  Final State:")
    print(f"    Equity: ${result.final_equity:,.0f}")
    print(f"    Cash: ${result.final_cash:,.0f}")
    print(f"    Positions: {result.final_positions}")

    # Test no-change scenario
    print("\n--- Executing Same Allocation (No Change) ---")
    result2 = orchestrator.execute(
        brain_output=brain_output_risk_on,
        regime="RISK_ON",
        regime_changed=False,  # No regime change
    )

    print(f"\nExecution Result:")
    print(f"  Success: {result2.success}")
    print(f"  Message: {result2.message}")
    print(f"  Trades: {len(result2.rebalance_plan.trades) if result2.rebalance_plan else 0}")

    # Test RISK_OFF transition
    print("\n--- Executing RISK_OFF Transition ---")
    brain_output_risk_off = {
        "engine_weights": {
            "CASH": 1.00,
            "EQUITY": 0.00,
            "DEFENSIVE": 0.00,
            "REAL_ASSET": 0.00,
        }
    }

    result3 = orchestrator.execute(
        brain_output=brain_output_risk_off,
        regime="RISK_OFF",
        regime_changed=True,
    )

    print(f"\nExecution Result:")
    print(f"  Success: {result3.success}")
    print(f"  Message: {result3.message}")
    if result3.rebalance_plan:
        print(f"  Trades: {len(result3.rebalance_plan.trades)}")
        for trade in result3.rebalance_plan.trades:
            print(f"    {trade.action.value} ${trade.amount:,.0f} {trade.asset}")

    print(f"\n  Final State:")
    print(f"    Equity: ${result3.final_equity:,.0f}")
    print(f"    Cash: ${result3.final_cash:,.0f}")
    print(f"    Positions: {result3.final_positions}")

    print("\n" + "="*60)
    print(f"Total executions: {len(orchestrator.history)}")
    print("="*60)
