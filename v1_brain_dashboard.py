"""
V1 Regime Appliance - Read-Only Status Display

A minimal, informational display of the current regime.
Designed to be boring, calm, and purely informational.

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

BACKTEST ISOLATION:
- This web app has NO imports, pages, or references to backtesting
- Backtesting exists ONLY as a separate CLI tool (v1_backtest.py)
- The import chain is: dashboard -> brain_state_reader -> (stdlib only)

APPLIANCE DESIGN:
- No charts, bars, or percentages
- No urgency or call to action
- Boring, calm, informational
"""

import streamlit as st
from brain_state_reader import get_current_regime, get_last_update_date

# -------------------------------
# PAGE CONFIG
# -------------------------------

st.set_page_config(
    page_title="Regime Status",
    page_icon="",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit UI elements for cleaner appliance look
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {background-color: #fafafa;}
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# REGIME DEFINITIONS
# -------------------------------

_REGIME_LABELS = {
    'RISK_ON': 'Risk-On',
    'RISK_NEUTRAL': 'Risk-Neutral',
    'RISK_OFF': 'Risk-Off',
    None: 'Pending'
}

_REGIME_EXPLANATIONS = {
    'RISK_ON': 'Market environment is currently favorable.',
    'RISK_NEUTRAL': 'Market environment is currently mixed.',
    'RISK_OFF': 'Market environment is currently unfavorable.',
    None: 'Awaiting first scheduled update.'
}

# -------------------------------
# MAIN DISPLAY
# -------------------------------

def render_appliance():
    """
    Render the regime appliance display.

    Design: Boring, calm, informational.
    No charts, no colors implying urgency, no action prompts.
    """

    # Get opaque regime data
    regime = get_current_regime()
    last_date = get_last_update_date()

    # Appliance header
    st.markdown(
        """
        <div style='
            text-align: center;
            padding: 40px 20px 20px 20px;
        '>
            <p style='
                color: #666;
                font-size: 14px;
                margin: 0;
                letter-spacing: 2px;
                text-transform: uppercase;
            '>
                Regime Status
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Regime display - single dominant element
    regime_label = _REGIME_LABELS.get(regime, 'Unknown')
    regime_explanation = _REGIME_EXPLANATIONS.get(regime, '')

    st.markdown(
        f"""
        <div style='
            text-align: center;
            padding: 30px 20px;
            background-color: #f5f5f5;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            margin: 0 auto;
            max-width: 400px;
        '>
            <p style='
                color: #333;
                font-size: 32px;
                font-weight: 500;
                margin: 0 0 16px 0;
                font-family: system-ui, -apple-system, sans-serif;
            '>
                {regime_label}
            </p>
            <p style='
                color: #666;
                font-size: 14px;
                margin: 0;
                line-height: 1.5;
            '>
                {regime_explanation}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Timestamp section
    st.markdown(
        f"""
        <div style='
            text-align: center;
            padding: 30px 20px;
            max-width: 400px;
            margin: 0 auto;
        '>
            <p style='
                color: #999;
                font-size: 12px;
                margin: 0 0 8px 0;
            '>
                Last updated: {last_date if last_date else 'Never'}
            </p>
            <p style='
                color: #999;
                font-size: 12px;
                margin: 0;
            '>
                Next update: Weekly (Friday close)
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Static disclaimer - always visible, not dismissible
    st.markdown(
        """
        <div style='
            text-align: center;
            padding: 20px;
            margin: 40px auto 20px auto;
            max-width: 400px;
            border-top: 1px solid #e0e0e0;
        '>
            <p style='
                color: #999;
                font-size: 11px;
                margin: 0 0 6px 0;
                line-height: 1.5;
            '>
                This system reports market environment only.
            </p>
            <p style='
                color: #999;
                font-size: 11px;
                margin: 0 0 6px 0;
                line-height: 1.5;
            '>
                It does not predict direction or timing.
            </p>
            <p style='
                color: #999;
                font-size: 11px;
                margin: 0;
                line-height: 1.5;
            '>
                No action is required or implied.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# -------------------------------
# MAIN
# -------------------------------

if __name__ == "__main__":
    render_appliance()
