"""
Minimal V1 Brain Skeleton - Updated Universe
Author: V1 Blueprint
Purpose: Regime detection + capital allocation (paper) + alerts

ARCHITECTURE:
- SENSING: 11 assets for regime detection (broad market view)
- ALLOCATION: 4 engines for capital deployment (SPY, TLT, GLD, Cash)

This is a frozen V1 allocator brain.
Do NOT optimize parameters.
Do NOT add indicators.
You may add visualizations, alerts, scheduling, and UI only.
"""

import yfinance as yf
import pandas as pd
import json
import datetime

# Import engine configuration
from execution_config import (
    ENGINES, REGIME_ENGINE_TARGETS, ENGINE_ASSET_MAP,
    validate_engine_weights, brain_output_to_orders
)

# Import utilities for safe operations
from utils import (
    atomic_write_json, safe_load_json, validate_brain_state
)

# -------------------------------
# CONFIG / FIXED PARAMETERS
# -------------------------------

# SENSING UNIVERSE: 11 assets for regime detection (Yahoo-friendly)
# These are used to SENSE the market environment, not for allocation
SENSING_ASSETS = [
    '^GSPC',    # S&P 500
    '^IXIC',    # Nasdaq
    '^RUT',     # Russell 2000
    'EFA',      # MSCI EAFE proxy
    'EEM',      # Emerging markets
    '^TNX',     # 10Y Treasury yield
    'TLT',      # Long bonds ETF
    'GLD',      # Gold
    'DBC',      # Commodities
    'DX-Y.NYB', # Dollar index
    '^VIX'      # Volatility
]

# Legacy alias for backwards compatibility
ASSETS = SENSING_ASSETS

START_DATE = '1997-01-01'
END_DATE = datetime.date.today().isoformat()

# V1 Allocator parameters (frozen)
DELTA = 0.15          # max weight change per rebalance
ALPHA = 0.33          # ramp fraction (gradual transition)
COOLDOWN_WEEKS = 3    # minimum weeks between allocation changes

STATE_FILE = "v1_brain_state.json"


# -------------------------------
# DATA INGESTION
# -------------------------------

def fetch_data(assets, start, end):
    """Fetch price data for all assets from Yahoo Finance."""
    data = {}
    for a in assets:
        try:
            df = yf.download(a, start=start, end=end, progress=False, auto_adjust=True)
            # Handle different yfinance versions - use Close (auto_adjust=True adjusts it)
            if isinstance(df.columns, pd.MultiIndex):
                # Newer yfinance with multi-index columns
                price_col = df['Close'][a] if a in df['Close'].columns else df['Close'].iloc[:, 0]
            elif 'Close' in df.columns:
                price_col = df['Close']
            else:
                print(f"Warning: Could not find price column for {a}")
                continue

            price_col.name = a
            data[a] = price_col
        except Exception as e:
            print(f"Warning: Could not fetch {a} -> {e}")

    if not data:
        raise ValueError("No data could be fetched for any asset")

    df_all = pd.DataFrame(data)
    df_all = df_all.resample('W-FRI').last()  # weekly resample
    df_all.dropna(how='all', inplace=True)
    return df_all


# -------------------------------
# STATE PERSISTENCE
# -------------------------------

def load_state():
    """Load and validate the brain state from file, or return default state."""
    default = {
        "last_regime": None,
        "last_allocation_date": None,
        "engine_weights": {
            "CASH": 1.0,
            "EQUITY": 0.0,
            "DEFENSIVE": 0.0,
            "REAL_ASSET": 0.0,
        }
    }
    raw_state = safe_load_json(STATE_FILE, default)

    # Migrate old state format if needed
    if 'engine_weights' not in raw_state:
        raw_state['engine_weights'] = {e: 0.0 for e in ENGINES}
        raw_state['engine_weights']['CASH'] = 1.0

    # Validate and sanitize state
    return validate_brain_state(raw_state)


def save_state(state):
    """Atomically save the brain state to file."""
    atomic_write_json(STATE_FILE, state)


# -------------------------------
# SIMPLE REGIME DETECTION (V1)
# -------------------------------

def detect_regime(price_df):
    """
    Simple V1 volatility-based regime detection.

    Regimes (semantic: permission to take risk, not price signals):
    - RISK_NEUTRAL: Low volatility environment (vol < 1%) - defensive posture
    - RISK_ON: Moderate volatility (1% <= vol < 2%) - environment permits risk
    - RISK_OFF: High volatility (vol >= 2%) - capital preservation mode
    """
    returns = price_df.pct_change().dropna()
    vol = returns.rolling(4).std().mean(axis=1).iloc[-1]  # avg vol last month

    # Thresholds are illustrative
    if vol < 0.01:
        return "RISK_NEUTRAL"
    elif vol < 0.02:
        return "RISK_ON"
    else:
        return "RISK_OFF"


# -------------------------------
# CAPITAL ALLOCATOR (V1 rules)
# -------------------------------

def allocate_capital(state, new_regime):
    """
    Allocate capital to ENGINES based on detected regime.

    The brain outputs engine weights (CASH, EQUITY, DEFENSIVE, REAL_ASSET).
    The execution layer maps engines to assets (SPY, TLT, GLD, Cash).

    Rules:
    - Respects cooldown period between allocations
    - Uses alpha (ramp fraction) for gradual transitions
    - Caps weight changes at delta (max weight change)
    """
    today = datetime.date.today()
    last_alloc_date = state['last_allocation_date']

    # Cooldown check - but SKIP cooldown if last_regime is None (initial setup)
    if last_alloc_date and state['last_regime'] is not None:
        weeks_since = (today - datetime.datetime.fromisoformat(last_alloc_date).date()).days // 7
        if weeks_since < COOLDOWN_WEEKS:
            return state  # cooldown active

    if new_regime == state['last_regime']:
        return state  # no regime change

    # Get target engine weights from execution_config (frozen V1 targets)
    target_weights = REGIME_ENGINE_TARGETS.get(new_regime, REGIME_ENGINE_TARGETS["RISK_OFF"])

    # Apply ramp (alpha) and cap (delta) to each engine
    for engine in ENGINES:
        w_current = state['engine_weights'].get(engine, 0.0)
        w_target = target_weights[engine]
        w_new = w_current + ALPHA * (w_target - w_current)
        w_change = max(min(w_new - w_current, DELTA), -DELTA)
        state['engine_weights'][engine] = w_current + w_change

    # Update state
    state['last_regime'] = new_regime
    state['last_allocation_date'] = today.isoformat()

    return state


# -------------------------------
# ALERTS (V1 placeholder)
# -------------------------------

def push_alert(state):
    """Print current regime and engine allocation state."""
    print(f"\n[ALERT] Regime: {state['last_regime']}")
    print(f"        Engine Weights:")
    for engine, weight in state['engine_weights'].items():
        asset = ENGINE_ASSET_MAP.get(engine, "N/A")
        print(f"          {engine:12} → {str(asset):6}: {weight:6.1%}")

    # Show executable orders
    orders = brain_output_to_orders(state['engine_weights'])
    print(f"\n        Executable Orders:")
    for ticker, weight in orders.items():
        if ticker and weight > 0:
            print(f"          {ticker}: {weight:.1%}")


# -------------------------------
# MAIN V1 EXECUTION
# -------------------------------

def run_v1_brain():
    """Main execution loop for V1 Brain."""
    print("Starting V1 Brain execution...")
    print(f"Fetching data from {START_DATE} to {END_DATE}")

    df_prices = fetch_data(ASSETS, START_DATE, END_DATE)
    print(f"Loaded {len(df_prices)} weekly data points")

    state = load_state()

    regime = detect_regime(df_prices)
    print(f"Detected regime: {regime}")

    state = allocate_capital(state, regime)

    save_state(state)

    push_alert(state)

    print("V1 Brain execution complete.")
    return state


# -------------------------------
# RUN
# -------------------------------

if __name__ == "__main__":
    run_v1_brain()
