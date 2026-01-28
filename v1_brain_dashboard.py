"""
V1 Brain Dashboard - Streamlit UI
Visualizations, alerts, scheduling, and UI for the V1 Brain Skeleton.
"""

import streamlit as st
import pandas as pd
import numpy as np
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

# Import backtest module
from v1_backtest import (
    run_backtest, calculate_summary, print_summary_report,
    get_regime_history, get_weight_history, get_exposure_history
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
# BACKTEST PAGE
# -------------------------------

@st.cache_data(ttl=3600)  # Cache backtest for 1 hour
def get_backtest_results():
    """Run and cache backtest results."""
    df_prices = get_price_data()
    results_df, summary = run_backtest(df_prices, start_idx=52, verbose=False)
    return results_df, summary


def render_backtest_page():
    """Render the historical backtest page."""
    st.title("📜 V1 Brain Historical Backtest")
    st.caption("Structural validation of allocator logic (1997-present)")

    st.info("⚠️ This backtest validates the V1 rules. It does NOT optimize parameters.")

    # Run backtest button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Re-run Backtest", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Load backtest results
    try:
        with st.spinner("Running historical backtest... This may take a moment."):
            results_df, summary = get_backtest_results()
    except Exception as e:
        st.error(f"Error running backtest: {e}")
        return

    st.success(f"Backtest complete: {summary['total_weeks']} weeks ({summary['start_date']} to {summary['end_date']})")

    st.markdown("---")

    # -------------------------------
    # SUMMARY METRICS
    # -------------------------------

    st.subheader("📊 Validation Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        delta_ok = summary['max_single_weight_change'] <= DELTA + 0.001
        st.metric(
            "Delta Cap (δ)",
            f"{'✅ OK' if delta_ok else '❌ FAIL'}",
            f"Max change: {summary['max_single_weight_change']:.1%}"
        )

    with col2:
        st.metric(
            "Regime Changes",
            summary['total_regime_changes'],
            f"Avg {summary['avg_weeks_between_changes']:.1f} wks apart"
        )

    with col3:
        st.metric(
            "Cooldown Active",
            f"{summary['cooldown_percentage']:.1f}%",
            f"{summary['cooldown_weeks']} weeks"
        )

    with col4:
        st.metric(
            "Avg Cash Weight",
            f"{summary['avg_cash_weight']:.1%}",
            f"Range: {summary['min_cash_weight']:.0%}-{summary['max_cash_weight']:.0%}"
        )

    st.markdown("---")

    # -------------------------------
    # REGIME DISTRIBUTION
    # -------------------------------

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🎯 Regime Distribution")

        regime_data = pd.DataFrame({
            'Regime': list(summary['regime_counts'].keys()),
            'Weeks': list(summary['regime_counts'].values()),
            'Percentage': [summary['regime_percentages'][r] for r in summary['regime_counts'].keys()]
        })

        fig_regime_pie = go.Figure(data=[go.Pie(
            labels=regime_data['Regime'],
            values=regime_data['Weeks'],
            marker_colors=[REGIME_COLORS.get(r, '#888') for r in regime_data['Regime']],
            textinfo='label+percent',
            hole=0.3
        )])

        fig_regime_pie.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig_regime_pie, use_container_width=True)

    with col_right:
        st.subheader("📈 Regime Streak Stats")

        streak_data = pd.DataFrame({
            'Metric': ['Average Streak', 'Longest Streak', 'Shortest Streak'],
            'Weeks': [
                summary['avg_regime_streak'],
                summary['max_regime_streak'],
                summary['min_regime_streak']
            ]
        })

        fig_streak = go.Figure(go.Bar(
            x=streak_data['Metric'],
            y=streak_data['Weeks'],
            marker_color=['steelblue', 'green', 'orange']
        ))

        fig_streak.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=30, b=0),
            yaxis_title="Weeks"
        )
        st.plotly_chart(fig_streak, use_container_width=True)

    st.markdown("---")

    # -------------------------------
    # REGIME TIMELINE
    # -------------------------------

    st.subheader("🗓️ Effective Regime Timeline (Allocator State)")

    # Create regime timeline visualization using EFFECTIVE regime (what allocator uses)
    fig_timeline = go.Figure()

    # Plot effective regime (what the allocator actually uses)
    for regime, color in [('RANGE', REGIME_COLORS['RANGE']),
                          ('TREND', REGIME_COLORS['TREND']),
                          ('SHOCK', REGIME_COLORS['SHOCK'])]:
        mask = results_df['effective_regime'] == regime
        if mask.any():
            fig_timeline.add_trace(go.Scatter(
                x=results_df.index[mask],
                y=[regime] * mask.sum(),
                mode='markers',
                marker=dict(color=color, size=8, symbol='square'),
                name=regime
            ))

    fig_timeline.update_layout(
        height=200,
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis=dict(categoryorder='array', categoryarray=['RANGE', 'TREND', 'SHOCK']),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified"
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

    # Optional: Show detected vs effective comparison
    with st.expander("Compare Detected vs Effective Regime"):
        st.caption("Detected = raw volatility signal | Effective = what allocator acts on (after cooldown)")

        col_det, col_eff = st.columns(2)

        with col_det:
            st.write("**Detected Regime (Raw Signal)**")
            if 'detected_counts' in summary:
                for r, pct in summary['detected_percentages'].items():
                    st.write(f"  {r}: {pct:.1f}%")

        with col_eff:
            st.write("**Effective Regime (Allocator)**")
            for r, pct in summary['regime_percentages'].items():
                st.write(f"  {r}: {pct:.1f}%")

    st.markdown("---")

    # -------------------------------
    # ALLOCATION OVER TIME
    # -------------------------------

    st.subheader("💰 Allocation Over Time")

    # Get weight history
    weight_history = get_weight_history(results_df)

    # Stacked area chart
    fig_alloc = go.Figure()

    for col in weight_history.columns:
        fig_alloc.add_trace(go.Scatter(
            x=weight_history.index,
            y=weight_history[col] * 100,
            name=col,
            mode='lines',
            stackgroup='one',
            hovertemplate='%{y:.1f}%'
        ))

    fig_alloc.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis_title="Weight (%)",
        yaxis=dict(range=[0, 105]),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        hovermode="x unified"
    )
    st.plotly_chart(fig_alloc, use_container_width=True)

    st.markdown("---")

    # -------------------------------
    # CASH VS INVESTED
    # -------------------------------

    st.subheader("💵 Cash vs Invested Exposure")

    col_left, col_right = st.columns(2)

    with col_left:
        exposure_history = get_exposure_history(results_df)

        fig_exposure = go.Figure()

        fig_exposure.add_trace(go.Scatter(
            x=exposure_history.index,
            y=exposure_history['cash_weight'] * 100,
            name='Cash',
            mode='lines',
            fill='tozeroy',
            line=dict(color='green')
        ))

        fig_exposure.add_trace(go.Scatter(
            x=exposure_history.index,
            y=exposure_history['total_invested'] * 100,
            name='Invested',
            mode='lines',
            fill='tozeroy',
            line=dict(color='steelblue')
        ))

        fig_exposure.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=30, b=0),
            yaxis_title="Weight (%)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            hovermode="x unified"
        )
        st.plotly_chart(fig_exposure, use_container_width=True)

    with col_right:
        st.subheader("📉 Weight Change Distribution")

        changes = results_df['max_weight_change'][results_df['max_weight_change'] > 0] * 100

        fig_hist = go.Figure(data=[go.Histogram(
            x=changes,
            nbinsx=30,
            marker_color='steelblue'
        )])

        # Add delta cap line
        fig_hist.add_vline(x=DELTA*100, line_dash="dash", line_color="red",
                          annotation_text=f"δ cap ({DELTA:.0%})")

        fig_hist.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis_title="Max Weight Change (%)",
            yaxis_title="Frequency"
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("---")

    # -------------------------------
    # VOLATILITY DIAGNOSTICS
    # -------------------------------

    st.subheader("📈 Volatility Diagnostics")

    if 'vol_mean' in summary:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Mean Volatility", f"{summary['vol_mean']*100:.2f}%")
        with col2:
            st.metric("Median Volatility", f"{summary['vol_median']*100:.2f}%")
        with col3:
            st.metric("Min Volatility", f"{summary['vol_min']*100:.2f}%")
        with col4:
            st.metric("Max Volatility", f"{summary['vol_max']*100:.2f}%")

        # Volatility histogram with regime thresholds
        st.write("**Volatility Distribution with Regime Thresholds**")

        fig_vol_hist = go.Figure()

        fig_vol_hist.add_trace(go.Histogram(
            x=results_df['volatility'] * 100,
            nbinsx=50,
            marker_color='steelblue',
            name='Volatility'
        ))

        # Add regime threshold lines
        fig_vol_hist.add_vline(x=1, line_dash="dash", line_color="green",
                               annotation_text="RANGE < 1%", annotation_position="top")
        fig_vol_hist.add_vline(x=2, line_dash="dash", line_color="orange",
                               annotation_text="TREND < 2%", annotation_position="top")

        fig_vol_hist.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=50, b=0),
            xaxis_title="Volatility (%)",
            yaxis_title="Frequency",
            showlegend=False
        )
        st.plotly_chart(fig_vol_hist, use_container_width=True)

        # Warning if no RANGE
        if summary.get('vol_below_1pct', 0) == 0:
            st.warning(
                f"⚠️ **No RANGE regime detected.** "
                f"The V1 thresholds (RANGE < 1%, TREND < 2%) may be too low for this 11-asset universe. "
                f"Mean volatility is {summary['vol_mean']*100:.2f}%, well above the 2% SHOCK threshold. "
                f"This is expected behavior - the frozen V1 parameters produce mostly SHOCK regimes with this asset mix."
            )

    st.markdown("---")

    # -------------------------------
    # DETAILED METRICS TABLE
    # -------------------------------

    st.subheader("📋 Detailed Validation Metrics")

    metrics_df = pd.DataFrame({
        'Metric': [
            'Total Weeks Simulated',
            'Total Regime Changes',
            'Avg Weeks Between Changes',
            'Weeks in Cooldown',
            'Cooldown Percentage',
            'Max Single Weight Change',
            'Avg Weight Change (when active)',
            'Average Cash Weight',
            'Min Cash Weight',
            'Max Cash Weight',
            'Average Invested Weight',
            'Max Invested Weight',
            'Avg Regime Streak',
            'Max Regime Streak'
        ],
        'Value': [
            f"{summary['total_weeks']}",
            f"{summary['total_regime_changes']}",
            f"{summary['avg_weeks_between_changes']:.1f} weeks",
            f"{summary['cooldown_weeks']}",
            f"{summary['cooldown_percentage']:.1f}%",
            f"{summary['max_single_weight_change']:.2%}",
            f"{summary['avg_weight_change']:.2%}",
            f"{summary['avg_cash_weight']:.1%}",
            f"{summary['min_cash_weight']:.1%}",
            f"{summary['max_cash_weight']:.1%}",
            f"{summary['avg_invested_weight']:.1%}",
            f"{summary['max_invested_weight']:.1%}",
            f"{summary['avg_regime_streak']:.1f} weeks",
            f"{summary['max_regime_streak']} weeks"
        ]
    })

    st.dataframe(metrics_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # -------------------------------
    # RAW DATA EXPLORER
    # -------------------------------

    with st.expander("🔍 Explore Raw Backtest Data"):
        st.write(f"Showing last 50 weeks of backtest results:")

        display_cols = ['detected_regime', 'effective_regime', 'volatility', 'regime_changed', 'cooldown_active',
                        'cash_weight', 'total_invested', 'max_weight_change']
        st.dataframe(results_df[display_cols].tail(50), use_container_width=True)

        # Download button
        csv = results_df.to_csv()
        st.download_button(
            label="📥 Download Full Backtest CSV",
            data=csv,
            file_name="v1_backtest_results.csv",
            mime="text/csv"
        )


# -------------------------------
# MAIN
# -------------------------------

if __name__ == "__main__":
    # Tab navigation
    tab1, tab2 = st.tabs(["📊 Live Dashboard", "📜 Historical Backtest"])

    with tab1:
        render_dashboard()

    with tab2:
        render_backtest_page()
