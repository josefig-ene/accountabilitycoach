"""
V1 Brain Dashboard - Streamlit UI
Visualizations, alerts, scheduling, and UI for the V1 Brain Skeleton.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import datetime
import time
import threading
from pathlib import Path

# Import from V1 Brain Skeleton
from v1_brain_skeleton import (
    ASSETS, START_DATE, END_DATE, DELTA, ALPHA, COOLDOWN_WEEKS, STATE_FILE,
    fetch_data, load_state, save_state, detect_regime, allocate_capital
)

# -------------------------------
# PAGE CONFIG
# -------------------------------

st.set_page_config(
    page_title="V1 Brain Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
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
# REGIME COLORS
# -------------------------------

REGIME_COLORS = {
    'TREND': '#00cc66',   # Green
    'RANGE': '#ffcc00',   # Yellow
    'SHOCK': '#ff4444',   # Red
    None: '#888888'       # Gray
}

# -------------------------------
# ALERT HISTORY FILE
# -------------------------------

ALERT_HISTORY_FILE = "v1_alert_history.json"


def load_alert_history():
    """Load alert history from file."""
    try:
        with open(ALERT_HISTORY_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_alert_history(history):
    """Save alert history to file."""
    with open(ALERT_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)


def add_alert(message, alert_type="info"):
    """Add an alert to history."""
    history = load_alert_history()
    history.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "message": message,
        "type": alert_type
    })
    # Keep only last 50 alerts
    history = history[-50:]
    save_alert_history(history)


# -------------------------------
# CACHED DATA LOADING
# -------------------------------

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_price_data():
    """Fetch and cache price data."""
    return fetch_data(ASSETS, START_DATE, END_DATE)


def calculate_volatility(price_df):
    """Calculate rolling volatility for regime visualization."""
    returns = price_df.pct_change().dropna()
    vol = returns.rolling(4).std().mean(axis=1)
    return vol


# -------------------------------
# SIDEBAR
# -------------------------------

def render_sidebar():
    """Render the sidebar with controls."""
    st.sidebar.title("🧠 V1 Brain Controls")

    st.sidebar.markdown("---")

    # Current State Display
    state = load_state()

    st.sidebar.subheader("Current State")
    regime = state.get('last_regime', 'Unknown')
    regime_color = REGIME_COLORS.get(regime, '#888888')

    st.sidebar.markdown(
        f"<div style='background-color:{regime_color};padding:10px;border-radius:5px;text-align:center;'>"
        f"<strong style='color:white;font-size:20px;'>{regime or 'Not Set'}</strong></div>",
        unsafe_allow_html=True
    )

    if state.get('last_allocation_date'):
        st.sidebar.caption(f"Last allocation: {state['last_allocation_date']}")

    st.sidebar.markdown("---")

    # Manual Run Button
    st.sidebar.subheader("Manual Execution")
    if st.sidebar.button("🚀 Run V1 Brain Now", use_container_width=True):
        with st.spinner("Running V1 Brain..."):
            run_brain_and_update()
        st.rerun()

    st.sidebar.markdown("---")

    # Frozen Parameters Display
    st.sidebar.subheader("Frozen Parameters")
    st.sidebar.text(f"Delta (δ): {DELTA:.0%}")
    st.sidebar.text(f"Alpha (α): {ALPHA:.0%}")
    st.sidebar.text(f"Cooldown: {COOLDOWN_WEEKS} weeks")

    st.sidebar.markdown("---")

    # Scheduling
    st.sidebar.subheader("Scheduling")
    schedule_enabled = st.sidebar.checkbox("Enable Auto-Run", value=False)

    if schedule_enabled:
        schedule_interval = st.sidebar.selectbox(
            "Run Interval",
            ["Every Hour", "Every 6 Hours", "Daily", "Weekly"],
            index=2
        )
        st.sidebar.info(f"Auto-run: {schedule_interval}")

        # Store scheduling preference in session state
        st.session_state['schedule_enabled'] = True
        st.session_state['schedule_interval'] = schedule_interval
    else:
        st.session_state['schedule_enabled'] = False

    st.sidebar.markdown("---")

    # Data Refresh
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    return state


def run_brain_and_update():
    """Run the V1 Brain and update state."""
    try:
        df_prices = get_price_data()
        state = load_state()
        old_regime = state.get('last_regime')

        regime = detect_regime(df_prices)
        state = allocate_capital(state, regime)
        save_state(state)

        # Add alert if regime changed
        if regime != old_regime:
            add_alert(f"Regime changed: {old_regime} → {regime}", "warning")
        else:
            add_alert(f"Brain executed. Regime: {regime}", "info")

        return state, regime
    except Exception as e:
        add_alert(f"Error running brain: {str(e)}", "error")
        raise


# -------------------------------
# MAIN DASHBOARD
# -------------------------------

def render_dashboard():
    """Render the main dashboard."""
    st.title("🧠 V1 Brain Dashboard")
    st.caption("Regime Detection & Capital Allocation System")

    # Render sidebar and get state
    state = render_sidebar()

    # Load data
    try:
        with st.spinner("Loading market data..."):
            df_prices = get_price_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    # Calculate current regime and volatility
    current_regime = detect_regime(df_prices)
    volatility = calculate_volatility(df_prices)

    # -------------------------------
    # TOP METRICS ROW
    # -------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        regime_color = REGIME_COLORS.get(current_regime, '#888888')
        st.markdown(
            f"<div style='background-color:{regime_color};padding:20px;border-radius:10px;text-align:center;'>"
            f"<p style='color:white;margin:0;font-size:14px;'>Current Regime</p>"
            f"<p style='color:white;margin:0;font-size:28px;font-weight:bold;'>{current_regime}</p></div>",
            unsafe_allow_html=True
        )

    with col2:
        current_vol = volatility.iloc[-1] * 100 if len(volatility) > 0 else 0
        st.metric("Avg Volatility (4wk)", f"{current_vol:.2f}%")

    with col3:
        cash_weight = state.get('cash_weight', 1.0)
        st.metric("Cash Weight", f"{cash_weight:.1%}")

    with col4:
        total_invested = sum(state.get('weights', {}).values())
        st.metric("Total Invested", f"{total_invested:.1%}")

    st.markdown("---")

    # -------------------------------
    # CHARTS ROW 1: Prices & Volatility
    # -------------------------------

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📈 Asset Prices (Normalized)")

        # Normalize prices to 100 at start
        df_normalized = df_prices / df_prices.iloc[0] * 100
        df_normalized = df_normalized.tail(252)  # Last ~5 years of weekly data

        fig_prices = go.Figure()
        for col in df_normalized.columns:
            fig_prices.add_trace(go.Scatter(
                x=df_normalized.index,
                y=df_normalized[col],
                name=ASSET_NAMES.get(col, col),
                mode='lines'
            ))

        fig_prices.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3),
            hovermode="x unified"
        )
        st.plotly_chart(fig_prices, use_container_width=True)

    with col_right:
        st.subheader("📊 Volatility & Regime Zones")

        vol_df = volatility.tail(252) * 100  # Convert to percentage

        fig_vol = go.Figure()

        # Add regime zones as shaded areas
        fig_vol.add_hrect(y0=0, y1=1, fillcolor="green", opacity=0.1,
                         annotation_text="RANGE", annotation_position="top left")
        fig_vol.add_hrect(y0=1, y1=2, fillcolor="yellow", opacity=0.1,
                         annotation_text="TREND", annotation_position="top left")
        fig_vol.add_hrect(y0=2, y1=vol_df.max()*1.1, fillcolor="red", opacity=0.1,
                         annotation_text="SHOCK", annotation_position="top left")

        fig_vol.add_trace(go.Scatter(
            x=vol_df.index,
            y=vol_df.values,
            name='Avg Volatility',
            mode='lines',
            line=dict(color='blue', width=2)
        ))

        fig_vol.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=30, b=0),
            yaxis_title="Volatility (%)",
            hovermode="x unified"
        )
        st.plotly_chart(fig_vol, use_container_width=True)

    st.markdown("---")

    # -------------------------------
    # CHARTS ROW 2: Allocation
    # -------------------------------

    col_pie, col_bar = st.columns(2)

    with col_pie:
        st.subheader("🥧 Current Allocation")

        weights = state.get('weights', {})
        cash = state.get('cash_weight', 1.0)

        # Build allocation data
        labels = [ASSET_NAMES.get(a, a) for a in weights.keys()] + ['Cash']
        values = list(weights.values()) + [cash]

        # Filter out zero weights for cleaner pie
        filtered_data = [(l, v) for l, v in zip(labels, values) if v > 0.001]
        if filtered_data:
            labels, values = zip(*filtered_data)

        fig_pie = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            textinfo='label+percent',
            textposition='outside'
        )])

        fig_pie.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        st.subheader("📊 Asset Weights")

        weights = state.get('weights', {})

        # Create bar chart data
        bar_data = pd.DataFrame({
            'Asset': [ASSET_NAMES.get(a, a) for a in weights.keys()],
            'Weight': [v * 100 for v in weights.values()]
        })
        bar_data = bar_data.sort_values('Weight', ascending=True)

        fig_bar = go.Figure(go.Bar(
            x=bar_data['Weight'],
            y=bar_data['Asset'],
            orientation='h',
            marker_color='steelblue'
        ))

        fig_bar.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis_title="Weight (%)",
            yaxis_title=""
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # -------------------------------
    # REGIME TARGET WEIGHTS TABLE
    # -------------------------------

    st.subheader("📋 Regime Target Weights")

    regime_table = pd.DataFrame({
        'Regime': ['TREND', 'RANGE', 'SHOCK'],
        'Per-Asset Weight': ['8%', '5%', '0%'],
        'Total Asset Weight': ['88%', '55%', '0%'],
        'Cash Weight': ['12%', '45%', '100%'],
        'Description': [
            'Moderate volatility - spread exposure across assets',
            'Low volatility - light exposure, higher cash',
            'High volatility - full de-risk to cash'
        ]
    })

    st.dataframe(regime_table, use_container_width=True, hide_index=True)

    st.markdown("---")

    # -------------------------------
    # ALERTS SECTION
    # -------------------------------

    st.subheader("🔔 Alert History")

    alert_history = load_alert_history()

    if alert_history:
        # Show last 10 alerts in reverse order (newest first)
        for alert in reversed(alert_history[-10:]):
            alert_type = alert.get('type', 'info')
            timestamp = alert.get('timestamp', '')[:19].replace('T', ' ')
            message = alert.get('message', '')

            if alert_type == 'error':
                st.error(f"**{timestamp}** - {message}")
            elif alert_type == 'warning':
                st.warning(f"**{timestamp}** - {message}")
            else:
                st.info(f"**{timestamp}** - {message}")
    else:
        st.info("No alerts yet. Run the brain to generate alerts.")

    # Clear alerts button
    if st.button("Clear Alert History"):
        save_alert_history([])
        st.rerun()

    st.markdown("---")

    # -------------------------------
    # RAW STATE DISPLAY
    # -------------------------------

    with st.expander("🔧 Raw State Data"):
        st.json(state)

    with st.expander("📊 Data Summary"):
        st.write(f"**Data Range:** {df_prices.index[0].date()} to {df_prices.index[-1].date()}")
        st.write(f"**Total Data Points:** {len(df_prices)} weeks")
        st.write(f"**Assets Loaded:** {len(df_prices.columns)}")
        st.dataframe(df_prices.tail(10))


# -------------------------------
# MAIN
# -------------------------------

if __name__ == "__main__":
    render_dashboard()
