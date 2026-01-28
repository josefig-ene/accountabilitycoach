"""
Minimal V1 Brain Skeleton - Updated Universe
Author: V1 Blueprint
Purpose: Regime detection + capital allocation (paper) + alerts

This is a frozen V1 allocator brain.
Do NOT optimize parameters.
Do NOT add indicators.
You may add visualizations, alerts, scheduling, and UI only.
"""

import yfinance as yf
import pandas as pd
import json
import datetime

# -------------------------------
# CONFIG / FIXED PARAMETERS
# -------------------------------

# Updated asset universe (Yahoo-friendly)
ASSETS = [
    '^GSPC',    # S&P 500
    '^IXIC',    # Nasdaq
    '^RUT',     # Russell 2000
    'EFA',      # MSCI EAFE proxy
    'EEM',      # Emerging markets
    '^TNX',     # 10Y Treasury
    'TLT',      # Long bonds ETF
    'GLD',      # Gold
    'DBC',      # Commodities
    'DX-Y.NYB', # Dollar index
    '^VIX'      # Volatility
]

START_DATE = '1997-01-01'
END_DATE = datetime.date.today().isoformat()

# V1 Allocator parameters (frozen)
DELTA = 0.15          # max weight change
ALPHA = 0.33          # ramp fraction
COOLDOWN_WEEKS = 3

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
    """Load the brain state from file, or return default state."""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "last_regime": None,
            "last_allocation_date": None,
            "weights": {a: 0.0 for a in ASSETS},
            "cash_weight": 1.0
        }


def save_state(state):
    """Save the brain state to file."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


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
    Allocate capital based on detected regime.

    Rules:
    - Respects cooldown period between allocations
    - Uses alpha (ramp fraction) for gradual transitions
    - Caps weight changes at delta (max weight change)
    """
    today = datetime.date.today()
    last_alloc_date = state['last_allocation_date']

    # Cooldown check
    if last_alloc_date:
        weeks_since = (today - datetime.datetime.fromisoformat(last_alloc_date).date()).days // 7
        if weeks_since < COOLDOWN_WEEKS:
            return state  # cooldown active

    if new_regime == state['last_regime']:
        return state  # no regime change

    # Target weights per regime (regime = permission level, not signal)
    target_weights = {}
    if new_regime == "RISK_ON":
        # Environment permits directional risk-taking
        target_weights = {a: 0.08 for a in ASSETS}  # spread exposure (sum ~88%)
        cash_target = 0.12
    elif new_regime == "RISK_NEUTRAL":
        # Noise dominates, defensive posture
        target_weights = {a: 0.05 for a in ASSETS}  # light exposure
        cash_target = 0.45
    elif new_regime == "RISK_OFF":
        # Capital preservation priority
        target_weights = {a: 0.0 for a in ASSETS}   # de-risk
        cash_target = 1.0
    else:
        # Default fallback
        target_weights = {a: 0.0 for a in ASSETS}
        cash_target = 1.0

    # Apply ramp (alpha) and cap (delta)
    for a in ASSETS:
        w_current = state['weights'].get(a, 0.0)
        w_target = target_weights[a]
        w_new = w_current + ALPHA * (w_target - w_current)
        w_change = max(min(w_new - w_current, DELTA), -DELTA)
        state['weights'][a] = w_current + w_change

    # Cash weight
    w_cash_current = state['cash_weight']
    w_cash_new = w_cash_current + ALPHA * (cash_target - w_cash_current)
    w_cash_change = max(min(w_cash_new - w_cash_current, DELTA), -DELTA)
    state['cash_weight'] = w_cash_current + w_cash_change

    # Update state
    state['last_regime'] = new_regime
    state['last_allocation_date'] = today.isoformat()

    return state


# -------------------------------
# ALERTS (V1 placeholder)
# -------------------------------

def push_alert(state):
    """Print current regime and allocation state."""
    print(f"[ALERT] Regime: {state['last_regime']}")
    print(f"        Weights: {state['weights']}")
    print(f"        Cash: {state['cash_weight']:.2f}")


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
