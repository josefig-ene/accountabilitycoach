"""
V1 Brain Dashboard - Opaque Regime Display

This dashboard displays the current regime label and its semantic meaning.
The UI is strictly read-only and regime output is OPAQUE.

ARCHITECTURAL CONSTRAINT:
- Imports ONLY from brain_state_reader (read-only, opaque module)
- Has NO access to detect_regime, allocate_capital, or run_v1_brain
- Contains NO buttons, forms, or controls that could trigger execution

OPACITY CONTRACT:
- Displays ONLY: regime label and semantic meaning
- Does NOT display: volatility values, charts, thresholds, distributions,
  engine weights, or any intermediate signal
- User sees the label, not the signal
- No data that could allow inferring proximity to regime boundaries
"""

import streamlit as st

# CRITICAL: Import ONLY opaque accessor functions
# These return ONLY label and date - no signals or intermediate values
from brain_state_reader import get_current_regime, get_last_update_date

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
# REGIME DISPLAY CONSTANTS
# -------------------------------

_REGIME_COLORS = {
    'RISK_ON': '#00cc66',
    'RISK_NEUTRAL': '#ffcc00',
    'RISK_OFF': '#ff4444',
    None: '#888888'
}

_REGIME_MEANINGS = {
    'RISK_ON': 'Environment permits directional risk-taking',
    'RISK_NEUTRAL': 'Defensive posture',
    'RISK_OFF': 'Capital preservation priority',
    None: 'Regime not yet determined'
}

# -------------------------------
# MAIN DISPLAY
# -------------------------------

def render_regime_status():
    """
    Render the opaque regime status display.

    OPACITY: Displays only the discrete regime label and its meaning.
    No volatility, thresholds, weights, or signals are shown.
    """
    st.title("🧠 V1 Brain")
    st.caption("Regime Status")

    # Get opaque regime data (label and date only)
    regime = get_current_regime()
    last_date = get_last_update_date()

    # Display regime label and meaning
    regime_color = _REGIME_COLORS.get(regime, '#888888')
    regime_meaning = _REGIME_MEANINGS.get(regime, 'Unknown')

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

    if last_date:
        st.caption(f"Last updated: {last_date}")
    else:
        st.caption("Awaiting first regime detection")


# -------------------------------
# MAIN
# -------------------------------

if __name__ == "__main__":
    render_regime_status()
