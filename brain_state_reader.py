"""
Read-Only Brain State Accessor

This module provides READ-ONLY access to the brain state.
It is intentionally isolated from all brain execution functions.

ARCHITECTURAL CONSTRAINT:
- This module MUST NOT import from v1_brain_skeleton
- This module MUST NOT contain or reference detect_regime, allocate_capital, or run_v1_brain
- This module provides ONLY read operations

The UI imports from this module exclusively, creating an architectural
barrier that makes it impossible for the UI to trigger brain execution.
"""

import json
import os
from typing import Optional

# Configuration (duplicated intentionally to avoid importing from brain)
STATE_FILE = "v1_brain_state.json"

# Valid regimes (for validation only)
VALID_REGIMES = {'RISK_ON', 'RISK_NEUTRAL', 'RISK_OFF', None}

# Engine names (for validation only)
ENGINES = ['CASH', 'EQUITY', 'DEFENSIVE', 'REAL_ASSET']


def _safe_load_json(filepath: str, default: dict) -> dict:
    """
    Safely load JSON from file with validation.

    This is a local implementation to avoid importing from modules
    that have access to brain execution functions.
    """
    if not os.path.exists(filepath):
        return default.copy()

    try:
        with open(filepath, 'r') as f:
            content = f.read().strip()
            if not content:
                return default.copy()
            data = json.loads(content)
            if not isinstance(data, dict):
                return default.copy()
            return data
    except (json.JSONDecodeError, IOError, OSError):
        return default.copy()


def _validate_state(state: dict) -> dict:
    """
    Validate and sanitize state for safe reading.
    Returns a sanitized copy of the state.
    """
    validated = {}

    # Validate last_regime
    regime = state.get('last_regime')
    if regime in VALID_REGIMES or regime is None:
        validated['last_regime'] = regime
    else:
        validated['last_regime'] = None

    # Validate last_allocation_date (basic string check)
    last_date = state.get('last_allocation_date')
    if isinstance(last_date, str) and len(last_date) == 10:
        validated['last_allocation_date'] = last_date
    else:
        validated['last_allocation_date'] = None

    # Validate engine_weights
    raw_weights = state.get('engine_weights', {})
    validated['engine_weights'] = {}
    for engine in ENGINES:
        weight = raw_weights.get(engine, 0.0)
        if isinstance(weight, (int, float)) and 0.0 <= weight <= 1.0:
            validated['engine_weights'][engine] = float(weight)
        else:
            validated['engine_weights'][engine] = 0.0

    return validated


def read_regime_state() -> dict:
    """
    Read the current brain state (read-only).

    Returns a validated, sanitized copy of the state.
    This function has NO side effects and CANNOT trigger brain execution.

    Returns:
        dict with keys:
            - last_regime: str or None ('RISK_ON', 'RISK_NEUTRAL', 'RISK_OFF')
            - last_allocation_date: str or None (ISO date format)
            - engine_weights: dict mapping engine names to weights
    """
    default = {
        "last_regime": None,
        "last_allocation_date": None,
        "engine_weights": {e: 0.0 for e in ENGINES}
    }
    default['engine_weights']['CASH'] = 1.0

    raw_state = _safe_load_json(STATE_FILE, default)
    return _validate_state(raw_state)


def get_current_regime() -> Optional[str]:
    """
    Get the current regime label only.

    Returns:
        str or None: 'RISK_ON', 'RISK_NEUTRAL', 'RISK_OFF', or None
    """
    state = read_regime_state()
    return state.get('last_regime')


def get_last_update_date() -> Optional[str]:
    """
    Get the last allocation date.

    Returns:
        str or None: ISO date string or None
    """
    state = read_regime_state()
    return state.get('last_allocation_date')


# Explicitly define what can be imported from this module
__all__ = [
    'read_regime_state',
    'get_current_regime',
    'get_last_update_date',
    'VALID_REGIMES',
]
