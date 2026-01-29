"""
Position Translator - Converts engine weights to dollar positions

ROLE: Translator, not decision-maker
- Never infers regime
- Never optimizes weights
- Never "helps"

Converts: weights → target dollars
"""

import datetime
from typing import Dict, Optional
from dataclasses import dataclass

# Import engine configuration (frozen)
import sys
sys.path.insert(0, '..')
from execution_config import ENGINE_ASSET_MAP, ENGINES


# -------------------------------
# DATA STRUCTURES
# -------------------------------

@dataclass
class TargetPositions:
    """Target positions in dollars."""
    timestamp: datetime.datetime
    account_equity: float
    engine_weights: Dict[str, float]
    dollar_positions: Dict[str, float]  # ticker → dollars
    cash_position: float

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "account_equity": self.account_equity,
            "engine_weights": self.engine_weights,
            "dollar_positions": self.dollar_positions,
            "cash_position": self.cash_position,
        }


# -------------------------------
# POSITION TRANSLATOR
# -------------------------------

class PositionTranslator:
    """
    Converts brain output (engine weights) to target dollar positions.

    This class is DUMB by design.
    It does not know:
    - How regime was detected
    - What signals were used
    - What volatility is doing

    It only translates.
    """

    def __init__(self, engine_asset_map: Optional[Dict[str, str]] = None):
        """
        Initialize with engine-to-asset mapping.

        Args:
            engine_asset_map: Frozen mapping of engines to assets.
                              Defaults to V1 mapping from execution_config.
        """
        self.engine_asset_map = engine_asset_map or ENGINE_ASSET_MAP

        # Validate mapping completeness
        self._validate_mapping()

    def _validate_mapping(self):
        """Validate that all engines have mappings."""
        for engine in ENGINES:
            if engine not in self.engine_asset_map:
                raise ValueError(f"Missing mapping for engine: {engine}")

    def translate(
        self,
        engine_weights: Dict[str, float],
        account_equity: float
    ) -> TargetPositions:
        """
        Translate engine weights to target dollar positions.

        Args:
            engine_weights: Dict of engine → weight (must sum to 1.0)
            account_equity: Total account value in dollars

        Returns:
            TargetPositions with dollar amounts per asset

        Raises:
            ValueError: If weights don't sum to 1.0 or contain unknown engines
        """
        # Validate inputs and normalize weights
        normalized_weights = self._validate_weights(engine_weights)
        self._validate_equity(account_equity)

        # Calculate dollar positions using normalized weights
        dollar_positions = {}
        cash_position = 0.0

        for engine, weight in normalized_weights.items():
            asset = self.engine_asset_map.get(engine)
            dollar_amount = account_equity * weight

            if asset is None:
                # CASH engine - no ticker
                cash_position = dollar_amount
            else:
                dollar_positions[asset] = dollar_amount

        return TargetPositions(
            timestamp=datetime.datetime.now(),
            account_equity=account_equity,
            engine_weights=engine_weights.copy(),
            dollar_positions=dollar_positions,
            cash_position=cash_position,
        )

    def _validate_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Validate and normalize engine weights.

        Returns normalized weights (sum exactly 1.0) to handle float precision.
        """
        # Check for unknown engines (CRITICAL - prevents silent expansion)
        unknown_engines = set(weights.keys()) - set(ENGINES)
        if unknown_engines:
            raise ValueError(
                f"Unknown engines in weights: {unknown_engines}. "
                f"Expected engines: {ENGINES}. "
                f"If you added new engines, update execution_config.py first."
            )

        # Check for missing engines
        missing_engines = set(ENGINES) - set(weights.keys())
        if missing_engines:
            raise ValueError(
                f"Missing engines in weights: {missing_engines}. "
                f"All engines must have explicit weights."
            )

        # Check non-negative weights (no shorting in V1)
        for engine, weight in weights.items():
            if weight < 0:
                raise ValueError(
                    f"Negative weight for {engine}: {weight}. "
                    f"V1 does not allow shorting."
                )

        # Check weights sum to approximately 1.0 (allow 1% tolerance for float issues)
        total = sum(weights.values())
        WEIGHT_TOLERANCE = 0.01  # 1% tolerance for float precision

        if abs(total - 1.0) > WEIGHT_TOLERANCE:
            raise ValueError(
                f"Engine weights must sum to 1.0 (±1%), got {total:.4f}. "
                f"Weights: {weights}"
            )

        # Normalize to exactly 1.0 to handle float precision issues
        # e.g., 0.12 + 0.50 + 0.20 + 0.18 might not equal exactly 1.0
        if total != 1.0 and total > 0:
            normalized = {engine: weight / total for engine, weight in weights.items()}
            return normalized

        return weights

    def _validate_equity(self, equity: float):
        """Validate account equity."""
        if equity <= 0:
            raise ValueError(f"Account equity must be positive, got {equity}")

        # Sanity check for reasonable account size
        if equity < 100:
            raise ValueError(
                f"Account equity {equity} seems too small. "
                f"Did you pass cents instead of dollars?"
            )


# -------------------------------
# CONVENIENCE FUNCTIONS
# -------------------------------

def translate_brain_output(brain_output: dict, account_equity: float) -> TargetPositions:
    """
    Convenience function to translate brain output to positions.

    Args:
        brain_output: Brain state containing 'engine_weights'
        account_equity: Total account value

    Returns:
        TargetPositions
    """
    translator = PositionTranslator()

    # Extract weights from brain output
    if 'engine_weights' in brain_output:
        weights = brain_output['engine_weights']
    elif 'weights' in brain_output:
        weights = brain_output['weights']
    else:
        raise ValueError("Brain output must contain 'engine_weights' or 'weights'")

    return translator.translate(weights, account_equity)


# -------------------------------
# MAIN (for testing)
# -------------------------------

if __name__ == "__main__":
    # Test with sample brain output
    brain_output = {
        "engine_weights": {
            "CASH": 0.35,
            "EQUITY": 0.35,
            "DEFENSIVE": 0.20,
            "REAL_ASSET": 0.10,
        }
    }

    account_equity = 1_000_000  # $1M account

    positions = translate_brain_output(brain_output, account_equity)

    print("\n" + "="*50)
    print("POSITION TRANSLATOR TEST")
    print("="*50)
    print(f"\nAccount Equity: ${account_equity:,.0f}")
    print(f"\nEngine Weights:")
    for engine, weight in positions.engine_weights.items():
        print(f"  {engine}: {weight:.1%}")

    print(f"\nTarget Dollar Positions:")
    for ticker, dollars in positions.dollar_positions.items():
        print(f"  {ticker}: ${dollars:,.0f}")
    print(f"  CASH: ${positions.cash_position:,.0f}")

    print("\n" + "="*50)
