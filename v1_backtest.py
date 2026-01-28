"""
V1 Brain Historical Backtest Loop
Purpose: Validate allocator logic across historical data (1997-present)

This backtest does NOT optimize parameters.
It validates that δ, α, and cooldown behave as intended.
"""

import pandas as pd
import numpy as np
import datetime
from copy import deepcopy

# Import frozen V1 parameters and functions
from v1_brain_skeleton import (
    ASSETS, START_DATE, DELTA, ALPHA, COOLDOWN_WEEKS,
    fetch_data
)

# -------------------------------
# ASSET NAME MAPPING
# -------------------------------

ASSET_NAMES = {
    '^GSPC': 'S&P 500',
    '^IXIC': 'Nasdaq',
    '^RUT': 'Russell 2000',
    'EFA': 'MSCI EAFE',
    'EEM': 'Emerging Markets',
    '^TNX': '10Y Treasury',
    'TLT': 'Long Bonds',
    'GLD': 'Gold',
    'DBC': 'Commodities',
    'DX-Y.NYB': 'Dollar Index',
    '^VIX': 'VIX'
}


# -------------------------------
# BACKTEST REGIME DETECTION
# -------------------------------

def detect_regime_at_point(price_df, idx, lookback=4):
    """
    Detect regime at a specific point in time using only past data.
    Uses lookback weeks for volatility calculation.
    """
    if idx < lookback:
        return None, None  # Not enough history

    window = price_df.iloc[idx-lookback:idx+1]
    # Fix FutureWarning: explicitly handle NaN before pct_change
    returns = window.pct_change(fill_method=None).dropna()

    if len(returns) < lookback:
        return None, None

    vol = returns.rolling(lookback).std().mean(axis=1).iloc[-1]

    if pd.isna(vol):
        return None, None
    elif vol < 0.01:
        return "RANGE", vol
    elif vol < 0.02:
        return "TREND", vol
    else:
        return "SHOCK", vol


# -------------------------------
# BACKTEST ALLOCATOR (V1 rules)
# -------------------------------

def allocate_at_point(state, new_regime, current_date):
    """
    Apply V1 allocation rules at a specific point in time.
    Uses exact same logic as v1_brain_skeleton.py
    """
    # Reset flags at start of each call
    state['cooldown_active'] = False
    state['regime_changed'] = False
    state['weight_changes'] = {}

    last_alloc_date = state['last_allocation_date']

    # Cooldown check
    if last_alloc_date:
        weeks_since = (current_date - last_alloc_date).days // 7
        if weeks_since < COOLDOWN_WEEKS:
            state['cooldown_active'] = True
            return state  # cooldown active

    if new_regime == state['last_regime']:
        return state  # no regime change

    state['regime_changed'] = True

    # Target weights per regime (same as V1)
    if new_regime == "TREND":
        target_weights = {a: 0.08 for a in ASSETS}
        cash_target = 0.12
    elif new_regime == "RANGE":
        target_weights = {a: 0.05 for a in ASSETS}
        cash_target = 0.45
    elif new_regime == "SHOCK":
        target_weights = {a: 0.0 for a in ASSETS}
        cash_target = 1.0
    else:
        target_weights = {a: 0.0 for a in ASSETS}
        cash_target = 1.0

    # Track weight changes for this step
    weight_changes = {}

    # Apply ramp (alpha) and cap (delta)
    for a in ASSETS:
        w_current = state['weights'].get(a, 0.0)
        w_target = target_weights[a]
        w_new = w_current + ALPHA * (w_target - w_current)
        w_change = max(min(w_new - w_current, DELTA), -DELTA)
        state['weights'][a] = w_current + w_change
        weight_changes[a] = w_change

    # Cash weight
    w_cash_current = state['cash_weight']
    w_cash_new = w_cash_current + ALPHA * (cash_target - w_cash_current)
    w_cash_change = max(min(w_cash_new - w_cash_current, DELTA), -DELTA)
    state['cash_weight'] = w_cash_current + w_cash_change
    weight_changes['cash'] = w_cash_change

    # Update state
    state['last_regime'] = new_regime
    state['last_allocation_date'] = current_date
    state['weight_changes'] = weight_changes

    return state


# -------------------------------
# MAIN BACKTEST LOOP
# -------------------------------

def run_backtest(price_df=None, start_idx=52, verbose=False):
    """
    Run historical backtest from start_idx to end of data.

    Args:
        price_df: Price DataFrame (fetched if None)
        start_idx: Index to start backtest (default 52 = ~1 year warmup)
        verbose: Print progress updates

    Returns:
        results: DataFrame with weekly backtest results
        summary: Dict with summary statistics
    """
    if price_df is None:
        print("Fetching historical data...")
        price_df = fetch_data(ASSETS, START_DATE, datetime.date.today().isoformat())

    print(f"Running backtest on {len(price_df)} weeks of data...")
    print(f"Date range: {price_df.index[0].date()} to {price_df.index[-1].date()}")
    print(f"Assets: {len(price_df.columns)}")

    # Initialize state
    state = {
        "last_regime": None,
        "last_allocation_date": None,
        "weights": {a: 0.0 for a in ASSETS},
        "cash_weight": 1.0,
        "cooldown_active": False,
        "regime_changed": False,
        "weight_changes": {}
    }

    # Results storage
    results = []

    for idx in range(start_idx, len(price_df)):
        current_date = price_df.index[idx].date()

        # Detect regime using only past data (returns regime and volatility value)
        detected_regime, vol_value = detect_regime_at_point(price_df, idx)

        if detected_regime is None:
            continue

        # Store pre-allocation state for comparison
        old_regime = state['last_regime']
        old_weights = deepcopy(state['weights'])
        old_cash = state['cash_weight']

        # Apply allocation rules
        state = allocate_at_point(state, detected_regime, current_date)

        # Effective regime is what the allocator is using (last_regime after allocation)
        # This accounts for cooldown blocking regime changes
        effective_regime = state['last_regime'] if state['last_regime'] else detected_regime

        # Calculate metrics for this week
        total_invested = sum(state['weights'].values())
        max_weight_change = 0
        if state.get('weight_changes'):
            max_weight_change = max(abs(v) for v in state['weight_changes'].values())

        # Record result
        result = {
            'date': current_date,
            'detected_regime': detected_regime,      # What volatility says
            'effective_regime': effective_regime,    # What allocator uses
            'volatility': vol_value,                 # Raw volatility value for diagnostics
            'regime_changed': state.get('regime_changed', False),
            'cooldown_active': state.get('cooldown_active', False),
            'cash_weight': state['cash_weight'],
            'total_invested': total_invested,
            'max_weight_change': max_weight_change,
        }

        # Add individual asset weights
        for a in ASSETS:
            result[f'weight_{a}'] = state['weights'].get(a, 0.0)

        results.append(result)

        if verbose and idx % 100 == 0:
            print(f"  Week {idx}: {current_date} | Regime: {regime} | Cash: {state['cash_weight']:.1%}")

    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    results_df.set_index('date', inplace=True)

    # Calculate summary statistics
    summary = calculate_summary(results_df)

    print("\nBacktest complete!")
    print(f"Total weeks simulated: {len(results_df)}")

    return results_df, summary


def calculate_summary(results_df):
    """Calculate summary statistics from backtest results."""

    # Use effective_regime for allocation-related stats
    regime_col = 'effective_regime'

    # Regime statistics (based on effective regime - what allocator uses)
    regime_counts = results_df[regime_col].value_counts()
    regime_pcts = results_df[regime_col].value_counts(normalize=True) * 100

    # Detected regime stats (raw volatility signals)
    detected_counts = results_df['detected_regime'].value_counts()
    detected_pcts = results_df['detected_regime'].value_counts(normalize=True) * 100

    # Regime transitions (actual allocation changes)
    regime_changes = results_df['regime_changed'].sum()
    total_weeks = len(results_df)

    # Cooldown statistics
    cooldown_weeks = results_df['cooldown_active'].sum()
    cooldown_pct = cooldown_weeks / total_weeks * 100

    # Weight change statistics
    max_single_change = results_df['max_weight_change'].max()
    avg_change_when_changed = results_df[results_df['max_weight_change'] > 0]['max_weight_change'].mean()

    # Exposure statistics
    avg_cash = results_df['cash_weight'].mean()
    min_cash = results_df['cash_weight'].min()
    max_cash = results_df['cash_weight'].max()

    avg_invested = results_df['total_invested'].mean()
    max_invested = results_df['total_invested'].max()

    # Time in each effective regime (what allocator uses)
    regime_streaks = []
    current_streak = 1
    for i in range(1, len(results_df)):
        if results_df[regime_col].iloc[i] == results_df[regime_col].iloc[i-1]:
            current_streak += 1
        else:
            regime_streaks.append(current_streak)
            current_streak = 1
    regime_streaks.append(current_streak)

    # Volatility statistics (for diagnostics)
    vol_mean = results_df['volatility'].mean()
    vol_min = results_df['volatility'].min()
    vol_max = results_df['volatility'].max()
    vol_median = results_df['volatility'].median()
    vol_below_1pct = (results_df['volatility'] < 0.01).sum()
    vol_below_2pct = (results_df['volatility'] < 0.02).sum()

    summary = {
        # Basic stats
        'total_weeks': total_weeks,
        'start_date': results_df.index[0],
        'end_date': results_df.index[-1],

        # Effective regime distribution (what allocator uses)
        'regime_counts': regime_counts.to_dict(),
        'regime_percentages': regime_pcts.to_dict(),

        # Detected regime distribution (raw volatility signals)
        'detected_counts': detected_counts.to_dict(),
        'detected_percentages': detected_pcts.to_dict(),

        # Volatility diagnostics
        'vol_mean': vol_mean,
        'vol_min': vol_min,
        'vol_max': vol_max,
        'vol_median': vol_median,
        'vol_below_1pct': vol_below_1pct,
        'vol_below_2pct': vol_below_2pct,

        # Transitions
        'total_regime_changes': regime_changes,
        'avg_weeks_between_changes': total_weeks / max(regime_changes, 1),

        # Cooldown
        'cooldown_weeks': cooldown_weeks,
        'cooldown_percentage': cooldown_pct,

        # Weight changes
        'max_single_weight_change': max_single_change,
        'avg_weight_change': avg_change_when_changed if not pd.isna(avg_change_when_changed) else 0,

        # Exposure
        'avg_cash_weight': avg_cash,
        'min_cash_weight': min_cash,
        'max_cash_weight': max_cash,
        'avg_invested_weight': avg_invested,
        'max_invested_weight': max_invested,

        # Regime streaks (effective)
        'avg_regime_streak': np.mean(regime_streaks),
        'max_regime_streak': max(regime_streaks),
        'min_regime_streak': min(regime_streaks),
    }

    return summary


# -------------------------------
# PRINT SUMMARY REPORT
# -------------------------------

def print_summary_report(summary):
    """Print a formatted summary report."""

    print("\n" + "="*60)
    print("V1 BRAIN BACKTEST SUMMARY REPORT")
    print("="*60)

    print(f"\n📅 Period: {summary['start_date']} to {summary['end_date']}")
    print(f"📊 Total weeks: {summary['total_weeks']}")

    print("\n--- REGIME DISTRIBUTION ---")
    for regime, pct in summary['regime_percentages'].items():
        count = summary['regime_counts'][regime]
        print(f"  {regime}: {pct:.1f}% ({count} weeks)")

    print("\n--- REGIME TRANSITIONS ---")
    print(f"  Total regime changes: {summary['total_regime_changes']}")
    print(f"  Avg weeks between changes: {summary['avg_weeks_between_changes']:.1f}")
    print(f"  Avg regime streak: {summary['avg_regime_streak']:.1f} weeks")
    print(f"  Longest streak: {summary['max_regime_streak']} weeks")

    print("\n--- COOLDOWN BEHAVIOR ---")
    print(f"  Weeks in cooldown: {summary['cooldown_weeks']} ({summary['cooldown_percentage']:.1f}%)")

    print("\n--- WEIGHT CHANGES (δ={:.0%}, α={:.0%}) ---".format(DELTA, ALPHA))
    print(f"  Max single change: {summary['max_single_weight_change']:.2%}")
    print(f"  Avg change (when active): {summary['avg_weight_change']:.2%}")
    print(f"  Delta cap respected: {'✅ Yes' if summary['max_single_weight_change'] <= DELTA + 0.001 else '❌ No'}")

    print("\n--- EXPOSURE ---")
    print(f"  Avg cash weight: {summary['avg_cash_weight']:.1%}")
    print(f"  Cash range: {summary['min_cash_weight']:.1%} - {summary['max_cash_weight']:.1%}")
    print(f"  Avg invested: {summary['avg_invested_weight']:.1%}")
    print(f"  Max invested: {summary['max_invested_weight']:.1%}")

    print("\n--- VOLATILITY DIAGNOSTICS ---")
    print(f"  Mean volatility: {summary['vol_mean']:.4f} ({summary['vol_mean']*100:.2f}%)")
    print(f"  Min volatility: {summary['vol_min']:.4f} ({summary['vol_min']*100:.2f}%)")
    print(f"  Max volatility: {summary['vol_max']:.4f} ({summary['vol_max']*100:.2f}%)")
    print(f"  Median volatility: {summary['vol_median']:.4f} ({summary['vol_median']*100:.2f}%)")
    print(f"  Weeks with vol < 1% (RANGE): {summary['vol_below_1pct']}")
    print(f"  Weeks with vol < 2% (RANGE+TREND): {summary['vol_below_2pct']}")
    print(f"  ⚠️ RANGE threshold (1%) may be too low for this asset universe")

    print("\n--- VALIDATION ---")
    delta_ok = summary['max_single_weight_change'] <= DELTA + 0.001
    cooldown_ok = summary['cooldown_percentage'] > 0  # Cooldown was active at some point
    ramp_ok = summary['avg_weight_change'] < DELTA  # Ramping prevents max jumps

    print(f"  ✅ Delta cap enforced: {delta_ok}")
    print(f"  ✅ Cooldown active: {cooldown_ok}")
    print(f"  ✅ Alpha ramping works: {ramp_ok}")

    print("\n" + "="*60)


# -------------------------------
# VISUALIZATION HELPERS
# -------------------------------

def get_regime_history(results_df):
    """Extract regime history for plotting."""
    return results_df[['detected_regime', 'effective_regime']].copy()


def get_weight_history(results_df):
    """Extract weight history for plotting."""
    weight_cols = [c for c in results_df.columns if c.startswith('weight_')]
    df = results_df[weight_cols + ['cash_weight']].copy()
    # Rename columns to friendly names
    df.columns = [ASSET_NAMES.get(c.replace('weight_', ''), c) for c in weight_cols] + ['Cash']
    return df


def get_exposure_history(results_df):
    """Extract exposure history for plotting."""
    return results_df[['cash_weight', 'total_invested']].copy()


def get_regime_transitions(results_df):
    """Get list of regime transition points."""
    transitions = results_df[results_df['regime_changed']].copy()
    return transitions


# -------------------------------
# MAIN EXECUTION
# -------------------------------

if __name__ == "__main__":
    # Run backtest
    results_df, summary = run_backtest(verbose=True)

    # Print summary report
    print_summary_report(summary)

    # Save results to CSV
    results_df.to_csv("v1_backtest_results.csv")
    print("\n📁 Results saved to v1_backtest_results.csv")
