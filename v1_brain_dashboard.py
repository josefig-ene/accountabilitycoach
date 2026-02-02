"""
V1 Brain Dashboard - Regime Display Only

This dashboard displays the current regime and its semantic meaning.
Regime detection runs on a fixed weekly cadence (read-only in UI).

REGIME SAFETY CONTRACT:
- Only displays regime label and semantic meaning
- No volatility values, charts, thresholds, or distributions
- No historical statistics or backtest results
- No manual execution or intra-period refresh
"""

import streamlit as st
from v1_brain_skeleton import load_state

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
# REGIME DEFINITIONS
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
# MAIN DISPLAY
# -------------------------------

def render_regime_status():
    """Render the regime status display."""
    st.title("🧠 V1 Brain")
    st.caption("Regime Status")

    # Load current state (read-only)
    state = load_state()
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
