"""
V1 Brain Dashboard - Read-Only Regime Display

This dashboard displays the current regime and its semantic meaning.
The UI is strictly read-only and CANNOT trigger brain execution.

ARCHITECTURAL CONSTRAINT:
- Imports ONLY from brain_state_reader (read-only module)
- Has NO access to detect_regime, allocate_capital, or run_v1_brain
- Contains NO buttons, forms, or controls that could trigger execution
- The brain runs on an external schedule; this UI only reads state

REGIME SAFETY CONTRACT:
- Only displays regime label and semantic meaning
- No volatility values, charts, thresholds, or distributions
- No historical statistics or backtest results
- No manual execution or intra-period refresh
"""

import streamlit as st

# CRITICAL: Import ONLY from read-only module
# This module has NO access to brain execution functions
from brain_state_reader import read_regime_state

# -------------------------------
# PAGE CONFIG
# -------------------------------

st.set_page_config(
    page_title="V1 Brain - Regime Status",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# -------------------------------
# REGIME DEFINITIONS (display only)
# -------------------------------

REGIME_COLORS = {
    'RISK_ON': '#00cc66',       # Green
    'RISK_NEUTRAL': '#ffcc00',  # Yellow
    'RISK_OFF': '#ff4444',      # Red
    None: '#888888'             # Gray
}

REGIME_MEANINGS = {
    'RISK_ON': 'Environment permits directional risk-taking',
    'RISK_NEUTRAL': 'Noise dominates - defensive posture',
    'RISK_OFF': 'Capital preservation priority',
    None: 'Regime not yet determined'
}

# -------------------------------
# MAIN DISPLAY (read-only)
# -------------------------------

def render_regime_status():
    """
    Render the regime status display.

    This function is strictly read-only:
    - Reads state from file via brain_state_reader
    - Displays regime label and meaning
    - Has NO access to brain execution functions
    """
    st.title("🧠 V1 Brain")
    st.caption("Regime Status (Read-Only)")

    # Read current state (read-only operation)
    state = read_regime_state()
    regime = state.get('last_regime')
    last_date = state.get('last_allocation_date')

    # Display regime
    regime_color = REGIME_COLORS.get(regime, '#888888')
    regime_meaning = REGIME_MEANINGS.get(regime, 'Unknown regime')

    st.markdown(
        f"""
        <div style='
            background-color: {regime_color};
            padding: 40px;
            border-radius: 15px;
            text-align: center;
            margin: 20px 0;
        '>
            <p style='color: white; margin: 0; font-size: 18px; opacity: 0.9;'>
                Current Regime
            </p>
            <p style='color: white; margin: 10px 0; font-size: 48px; font-weight: bold;'>
                {regime or 'NOT SET'}
            </p>
            <p style='color: white; margin: 0; font-size: 16px; opacity: 0.9;'>
                {regime_meaning}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Display last update date
    if last_date:
        st.caption(f"Last updated: {last_date}")
    else:
        st.caption("Awaiting first regime detection")


# -------------------------------
# MAIN
# -------------------------------

if __name__ == "__main__":
    render_regime_status()
