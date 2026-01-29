"""
V1 Execution Config - Engine to Asset Mapping
Author: V1 Blueprint
Purpose: Maps abstract engines to concrete tradable assets

ARCHITECTURE:
- The brain allocates to ENGINES (abstract concepts)
- Engines map to ASSETS (concrete ETFs)
- This separation keeps the brain sane

V1 RULE:
"V1 allocates only to SPY, TLT, GLD, and Cash — nothing else."
Everything else is sensing or future work.

This file lives OUTSIDE regime logic. OUTSIDE feature code.
"""

# -------------------------------
# V1 ENGINE DEFINITIONS
# -------------------------------

# The four V1 engines (abstract allocation targets)
ENGINES = ["CASH", "EQUITY", "DEFENSIVE", "REAL_ASSET"]

# -------------------------------
# ENGINE → ASSET MAPPING (FROZEN)
# -------------------------------

ENGINE_ASSET_MAP = {
    "CASH": None,           # Real cash / T-bills / money market (no ticker needed)
    "EQUITY": "SPY",        # Broad risk-on exposure, clean beta
    "DEFENSIVE": "TLT",     # Growth scare hedge, crisis convexity
    "REAL_ASSET": "GLD",    # Inflation hedge, monetary debasement protection
}

# Human-readable descriptions
ENGINE_DESCRIPTIONS = {
    "CASH": "Capital preservation, dry powder, behavioral safety",
    "EQUITY": "Broad risk-on exposure, capture equity momentum regimes",
    "DEFENSIVE": "Growth scare hedge, equity crash convexity, risk ballast",
    "REAL_ASSET": "Inflation regimes, monetary debasement, non-financial exposure",
}

# Why these specific assets (documentation)
ENGINE_RATIONALE = {
    "CASH": "Literal cash/T-bills. No ETF needed. BIL/SHV for backtest proxy only.",
    "EQUITY": "SPY: Deep liquidity, long history, clean beta, no factor opinions.",
    "DEFENSIVE": "TLT: Strong crisis response, long duration, clean risk-off behavior.",
    "REAL_ASSET": "GLD: Long history, liquid, clean inflation/real-rate sensitivity.",
}

# -------------------------------
# BACKTEST PROXIES
# -------------------------------

# For backtesting, we need ticker proxies for cash
BACKTEST_ASSET_MAP = {
    "CASH": "BIL",          # SPDR 1-3 Month T-Bill ETF (proxy for cash)
    "EQUITY": "SPY",
    "DEFENSIVE": "TLT",
    "REAL_ASSET": "GLD",
}

# Asset start dates (for backtest availability)
ASSET_START_DATES = {
    "SPY": "1993-01-29",    # SPY inception
    "TLT": "2002-07-26",    # TLT inception
    "GLD": "2004-11-18",    # GLD inception
    "BIL": "2007-05-25",    # BIL inception (use risk-free rate before this)
}

# -------------------------------
# V1 REGIME → ENGINE ALLOCATION
# -------------------------------

# Target engine weights per regime (frozen V1 parameters)
# Regime = permission level, not a signal
REGIME_ENGINE_TARGETS = {
    "RISK_ON": {
        # Environment permits directional risk-taking
        "EQUITY": 0.50,
        "DEFENSIVE": 0.20,
        "REAL_ASSET": 0.18,
        "CASH": 0.12,
    },
    "RISK_NEUTRAL": {
        # Noise dominates, defensive posture
        "EQUITY": 0.25,
        "DEFENSIVE": 0.15,
        "REAL_ASSET": 0.15,
        "CASH": 0.45,
    },
    "RISK_OFF": {
        # Capital preservation priority
        "EQUITY": 0.00,
        "DEFENSIVE": 0.00,
        "REAL_ASSET": 0.00,
        "CASH": 1.00,
    },
}

# -------------------------------
# VALIDATION
# -------------------------------

def validate_engine_weights(weights):
    """Validate that engine weights sum to 1.0 and are non-negative."""
    total = sum(weights.values())
    if abs(total - 1.0) > 0.001:
        raise ValueError(f"Engine weights must sum to 1.0, got {total}")
    for engine, weight in weights.items():
        if weight < 0:
            raise ValueError(f"Engine weight for {engine} cannot be negative: {weight}")
        if engine not in ENGINES:
            raise ValueError(f"Unknown engine: {engine}")
    return True


def get_asset_for_engine(engine, for_backtest=False):
    """Get the asset ticker for a given engine."""
    if for_backtest:
        return BACKTEST_ASSET_MAP.get(engine)
    return ENGINE_ASSET_MAP.get(engine)


def get_target_weights(regime):
    """Get target engine weights for a given regime."""
    if regime not in REGIME_ENGINE_TARGETS:
        raise ValueError(f"Unknown regime: {regime}")
    return REGIME_ENGINE_TARGETS[regime].copy()


# -------------------------------
# EXECUTION HELPERS
# -------------------------------

def brain_output_to_orders(brain_output, for_backtest=False):
    """
    Convert brain output (engine weights) to executable orders.

    Args:
        brain_output: dict of {engine: weight}
        for_backtest: if True, use backtest proxies (e.g., BIL for cash)

    Returns:
        dict of {ticker: weight} (None tickers excluded for live trading)
    """
    orders = {}
    for engine, weight in brain_output.items():
        ticker = get_asset_for_engine(engine, for_backtest)
        if ticker is not None or for_backtest:
            orders[ticker] = weight
    return orders


# -------------------------------
# DISPLAY HELPERS
# -------------------------------

def print_engine_config():
    """Print the V1 engine configuration."""
    print("\n" + "="*60)
    print("V1 ENGINE CONFIGURATION")
    print("="*60)

    print("\n--- ENGINE → ASSET MAPPING ---")
    for engine in ENGINES:
        asset = ENGINE_ASSET_MAP[engine]
        desc = ENGINE_DESCRIPTIONS[engine]
        print(f"  {engine:12} → {str(asset):6} | {desc}")

    print("\n--- REGIME → ENGINE TARGETS ---")
    for regime, targets in REGIME_ENGINE_TARGETS.items():
        print(f"\n  {regime}:")
        for engine, weight in targets.items():
            print(f"    {engine:12}: {weight:5.0%}")

    print("\n" + "="*60)
    print("V1 allocates only to SPY, TLT, GLD, and Cash — nothing else.")
    print("="*60 + "\n")


# -------------------------------
# MAIN
# -------------------------------

if __name__ == "__main__":
    print_engine_config()

    # Validate all regime targets
    for regime, targets in REGIME_ENGINE_TARGETS.items():
        validate_engine_weights(targets)
        print(f"✅ {regime} weights valid")
