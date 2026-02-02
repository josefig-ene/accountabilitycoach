"""
Read-Only Brain State Accessor - Opaque Regime Output

This module provides READ-ONLY, OPAQUE access to regime status.
It exposes ONLY the regime label and update date - no intermediate signals.

ARCHITECTURAL CONSTRAINT:
- This module MUST NOT import from v1_brain_skeleton
- This module MUST NOT expose detect_regime, allocate_capital, or run_v1_brain
- This module provides ONLY read operations

OPACITY CONTRACT:
- Exposes ONLY: regime label (RISK_ON, RISK_NEUTRAL, RISK_OFF) and last update date
- Does NOT expose: volatility values, thresholds, engine weights, or any intermediate signal
- User sees the label, not the signal
- No data that could allow inferring proximity to regime boundaries
"""

import json
import os
from typing import Optional

# Configuration (duplicated intentionally to avoid importing from brain)
_STATE_FILE = "v1_brain_state.json"

# Valid regimes (for internal validation only - not exposed)
_VALID_REGIMES = {'RISK_ON', 'RISK_NEUTRAL', 'RISK_OFF'}


def _safe_load_json(filepath: str, default: dict) -> dict:
    """
    Safely load JSON from file with validation.
    Internal function - not exposed to UI.
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


def get_current_regime() -> Optional[str]:
    """
    Get the current regime label only.

    OPACITY: Returns ONLY the discrete label.
    No volatility values, thresholds, weights, or signals are exposed.
    The user cannot infer proximity to regime boundaries from this output.

    Returns:
        str or None: 'RISK_ON', 'RISK_NEUTRAL', 'RISK_OFF', or None if not set
    """
    default = {"last_regime": None}
    state = _safe_load_json(_STATE_FILE, default)

    regime = state.get('last_regime')

    # Validate regime is one of the known values
    if regime in _VALID_REGIMES:
        return regime
    return None


def get_last_update_date() -> Optional[str]:
    """
    Get the date of the last regime update.

    Returns:
        str or None: ISO date string (YYYY-MM-DD) or None if not set
    """
    default = {"last_allocation_date": None}
    state = _safe_load_json(_STATE_FILE, default)

    last_date = state.get('last_allocation_date')

    # Basic validation: must be string of correct length
    if isinstance(last_date, str) and len(last_date) == 10:
        return last_date
    return None


# Explicitly define what can be imported from this module
# OPACITY: Only label and date - no signals, weights, or intermediate values
__all__ = [
    'get_current_regime',
    'get_last_update_date',
]
