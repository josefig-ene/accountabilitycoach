"""
Utility functions for V1 Brain system.

Provides:
- Atomic file operations (prevent corruption)
- State validation (prevent injection)
- Safe JSON handling
"""

import json
import os
import tempfile
from typing import Any, Dict, Optional, List
from pathlib import Path


# -------------------------------
# CONSTANTS
# -------------------------------

VALID_ENGINES = {"CASH", "EQUITY", "DEFENSIVE", "REAL_ASSET"}
VALID_REGIMES = {"RISK_ON", "RISK_NEUTRAL", "RISK_OFF", None}

MAX_WEIGHT = 1.0
MIN_WEIGHT = 0.0
WEIGHT_SUM_TOLERANCE = 0.01  # 1% tolerance for float precision

MAX_EQUITY = 1_000_000_000  # $1B max
MIN_EQUITY = 0

MAX_HISTORY_SIZE = 100  # Max items in any history list


# -------------------------------
# ATOMIC FILE OPERATIONS
# -------------------------------

def atomic_write_json(filepath: str, data: dict, indent: int = 2) -> None:
    """
    Atomically write JSON to file.

    Uses write-to-temp-then-rename pattern to prevent corruption
    if process is killed mid-write.

    Args:
        filepath: Target file path
        data: Data to write
        indent: JSON indent level
    """
    filepath = Path(filepath)

    # Create parent directory if needed
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file in same directory (for atomic rename)
    fd, temp_path = tempfile.mkstemp(
        dir=filepath.parent,
        prefix=f".{filepath.name}.",
        suffix=".tmp"
    )

    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=indent, default=str)

        # Atomic rename (on POSIX systems)
        # On Windows, this may not be fully atomic but is still safer
        os.replace(temp_path, filepath)

    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def safe_load_json(filepath: str, default: Optional[dict] = None) -> dict:
    """
    Safely load JSON with fallback to default.

    Args:
        filepath: File to load
        default: Default value if file doesn't exist or is corrupted

    Returns:
        Loaded data or default
    """
    if default is None:
        default = {}

    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return default.copy()
    except json.JSONDecodeError:
        # File is corrupted - return default but don't overwrite
        # (let caller decide what to do)
        return default.copy()


# -------------------------------
# STATE VALIDATION
# -------------------------------

def validate_engine_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """
    Validate and sanitize engine weights.

    Checks:
    - All engines are known
    - No negative weights
    - No weights > 1.0
    - Sum is approximately 1.0

    Args:
        weights: Engine weights dict

    Returns:
        Validated weights (may be normalized)

    Raises:
        ValueError: If weights are invalid and cannot be fixed
    """
    if not weights:
        # Default to 100% cash
        return {"CASH": 1.0, "EQUITY": 0.0, "DEFENSIVE": 0.0, "REAL_ASSET": 0.0}

    validated = {}

    for engine, weight in weights.items():
        # Check engine is known
        if engine not in VALID_ENGINES:
            raise ValueError(f"Unknown engine: {engine}")

        # Convert to float if needed
        try:
            weight = float(weight)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid weight for {engine}: {weight}")

        # Check bounds
        if weight < MIN_WEIGHT:
            raise ValueError(f"Negative weight for {engine}: {weight}")
        if weight > MAX_WEIGHT + WEIGHT_SUM_TOLERANCE:
            raise ValueError(f"Weight > 100% for {engine}: {weight}")

        validated[engine] = weight

    # Ensure all engines present
    for engine in VALID_ENGINES:
        if engine not in validated:
            validated[engine] = 0.0

    # Check sum
    total = sum(validated.values())
    if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
        raise ValueError(f"Weights sum to {total:.4f}, not 1.0")

    # Normalize to exactly 1.0 (fix float precision issues)
    if total != 1.0 and total > 0:
        for engine in validated:
            validated[engine] = validated[engine] / total

    return validated


def validate_brain_state(state: dict) -> dict:
    """
    Validate and sanitize brain state loaded from file.

    Args:
        state: Raw state from file

    Returns:
        Validated state with safe defaults
    """
    validated = {}

    # Validate regime
    regime = state.get('last_regime')
    if regime not in VALID_REGIMES:
        regime = None
    validated['last_regime'] = regime

    # Validate allocation date
    last_date = state.get('last_allocation_date')
    if last_date:
        try:
            # Try to parse it to validate format
            from datetime import datetime
            if isinstance(last_date, str):
                datetime.fromisoformat(last_date.replace('Z', '+00:00'))
            validated['last_allocation_date'] = last_date
        except (ValueError, TypeError):
            validated['last_allocation_date'] = None
    else:
        validated['last_allocation_date'] = None

    # Validate engine weights
    try:
        validated['engine_weights'] = validate_engine_weights(
            state.get('engine_weights', {})
        )
    except ValueError:
        # Fall back to 100% cash if weights are corrupted
        validated['engine_weights'] = {
            "CASH": 1.0,
            "EQUITY": 0.0,
            "DEFENSIVE": 0.0,
            "REAL_ASSET": 0.0
        }

    return validated


def validate_execution_state(state: dict) -> dict:
    """
    Validate and sanitize execution state.

    Args:
        state: Raw state from file

    Returns:
        Validated state
    """
    validated = {
        'last_execution': None,
        'execution_history': [],
        'last_regime': None,
        'account_equity': 1_000_000.0,
    }

    # Validate account equity
    equity = state.get('account_equity')
    if equity is not None:
        try:
            equity = float(equity)
            if MIN_EQUITY < equity <= MAX_EQUITY:
                validated['account_equity'] = equity
        except (TypeError, ValueError):
            pass

    # Validate last regime
    regime = state.get('last_regime')
    if regime in VALID_REGIMES:
        validated['last_regime'] = regime

    # Validate history (just limit size, don't validate each entry)
    history = state.get('execution_history', [])
    if isinstance(history, list):
        validated['execution_history'] = history[-MAX_HISTORY_SIZE:]

    # Keep last execution as-is (for display only)
    validated['last_execution'] = state.get('last_execution')

    return validated


def validate_broker_state(state: dict) -> dict:
    """
    Validate and sanitize broker state.

    Args:
        state: Raw state from file

    Returns:
        Validated state
    """
    validated = {
        'positions': {},
        'cash': 1_000_000.0,
        'trade_history': [],
    }

    # Validate cash
    cash = state.get('cash')
    if cash is not None:
        try:
            cash = float(cash)
            if cash >= 0:
                validated['cash'] = cash
        except (TypeError, ValueError):
            pass

    # Validate positions
    positions = state.get('positions', {})
    if isinstance(positions, dict):
        for asset, value in positions.items():
            try:
                value = float(value)
                if value >= 0:
                    validated['positions'][asset] = value
            except (TypeError, ValueError):
                pass

    # Validate trade history (limit size)
    history = state.get('trade_history', [])
    if isinstance(history, list):
        validated['trade_history'] = history[-MAX_HISTORY_SIZE:]

    return validated


# -------------------------------
# SAFE MATH
# -------------------------------

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.

    Args:
        numerator: Top of fraction
        denominator: Bottom of fraction
        default: Value to return if denominator is 0

    Returns:
        Result or default
    """
    if denominator == 0:
        return default
    return numerator / denominator


def safe_percentage(part: float, whole: float, default: float = 0.0) -> float:
    """
    Safely calculate percentage.

    Args:
        part: The part
        whole: The whole
        default: Value if whole is 0

    Returns:
        Percentage (0-100) or default
    """
    return safe_divide(part, whole, default) * 100
