"""
CEO Dashboard - Three Engines of Life
Track Venture Studio (Wealth), Cohort Business (Cashflow), and Personal Sustainability (Longevity)
"""

# Load environment variables from .env file (for local development)
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from database import Database

# Page configuration
st.set_page_config(
    page_title="CEO Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern look
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #FF4B4B;
        color: white;
    }
    .stButton>button:hover {
        background-color: #FF6B6B;
        color: white;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
    }
    .stage-card {
        padding: 1rem;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 0.5rem 0;
    }
    h1 {
        color: #1f1f1f;
        padding-bottom: 1rem;
    }
    h2 {
        color: #262730;
        padding-top: 1rem;
    }
    h3 {
        color: #464646;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize database
db = Database()


def studio_cockpit():
    """Venture Studio Engine - Track Ideas and Milestones"""
    st.title("🚀 Studio Cockpit")
    st.markdown("### Venture Studio Engine - Wealth Creation")

    # Get all ideas
    ideas = db.get_all_ideas()

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Portfolio Overview", "➕ Add New Idea", "🎯 Manage Milestones"])

    with tab1:
        if not ideas:
            st.info("No ideas yet. Add your first idea in the 'Add New Idea' tab!")
        else:
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Ideas", len(ideas))
            with col2:
                avg_confidence = sum(i['confidence_score'] for i in ideas) / len(ideas)
                st.metric("Avg Confidence", f"{avg_confidence:.0f}%")
            with col3:
                active_ideas = len([i for i in ideas if i['stage'] not in ['exit']])
                st.metric("Active Ideas", active_ideas)
            with col4:
                exited = len([i for i in ideas if i['stage'] == 'exit'])
                st.metric("Exited", exited)

            st.markdown("---")

            # Kanban Board View
            st.subheader("📋 Stage Pipeline")

            stages = ['seed', 'validation', 'mvp', 'pilot', 'scale', 'exit']
            stage_labels = {
                'seed': '🌱 Seed',
                'validation': '🔍 Validation',
                'mvp': '⚙️ MVP',
                'pilot': '🧪 Pilot',
                'scale': '📈 Scale',
                'exit': '🎉 Exit'
            }

            cols = st.columns(6)

            for idx, stage in enumerate(stages):
                with cols[idx]:
                    st.markdown(f"**{stage_labels[stage]}**")
                    stage_ideas = [i for i in ideas if i['stage'] == stage]

                    if stage_ideas:
                        for idea in stage_ideas:
                            confidence_color = (
                                "🟢" if idea['confidence_score'] >= 70
                                else "🟡" if idea['confidence_score'] >= 40
                                else "🔴"
                            )

                            with st.container():
                                st.markdown(f"""
                                <div style='padding: 0.8rem; margin: 0.5rem 0; background-color: white;
                                     border-radius: 8px; border-left: 4px solid #FF4B4B; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                                    <div style='font-weight: 600; margin-bottom: 0.3rem;'>{idea['name']}</div>
                                    <div style='font-size: 0.85rem; color: #666;'>
                                        {confidence_color} {idea['confidence_score']}% confidence
                                    </div>
                                    <div style='font-size: 0.8rem; color: #888; margin-top: 0.3rem;'>
                                        👤 {idea['owner']}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                                # Quick action buttons
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    if st.button("📝", key=f"edit_{idea['id']}", help="View details"):
                                        st.session_state.selected_idea = idea['id']
                                        st.rerun()
                                with col_b:
                                    if st.button("🗑️", key=f"del_{idea['id']}", help="Delete"):
                                        db.delete_idea(idea['id'])
                                        st.rerun()
                    else:
                        st.markdown("<div style='text-align: center; color: #ccc; padding: 1rem;'>—</div>",
                                  unsafe_allow_html=True)

            st.markdown("---")

            # Detailed table view
            st.subheader("📊 Detailed View")
            df = pd.DataFrame(ideas)
            df = df[['name', 'stage', 'owner', 'confidence_score', 'description']]
            df.columns = ['Idea', 'Stage', 'Owner', 'Confidence %', 'Description']
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("➕ Add New Idea")

        with st.form("add_idea_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                idea_name = st.text_input("Idea Name *", placeholder="e.g., AI-Powered CRM")
                stage = st.selectbox("Stage *", ['seed', 'validation', 'mvp', 'pilot', 'scale', 'exit'])

            with col2:
                owner = st.text_input("Owner *", placeholder="e.g., John Doe")

            description = st.text_area("Description", placeholder="Brief summary of the idea...")

            submitted = st.form_submit_button("🚀 Add Idea")

            if submitted:
                if idea_name and owner:
                    idea_id = db.add_idea(idea_name, description, stage, owner)
                    st.success(f"✅ Idea '{idea_name}' added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all required fields (*).")

    with tab3:
        st.subheader("🎯 Manage Milestones")

        if not ideas:
            st.info("Add an idea first to create milestones.")
        else:
            # Select idea
            idea_options = {idea['name']: idea['id'] for idea in ideas}
            selected_idea_name = st.selectbox("Select Idea", list(idea_options.keys()))
            selected_idea_id = idea_options[selected_idea_name]

            # Get idea details
            idea = db.get_idea_by_id(selected_idea_id)
            st.info(f"**Stage:** {idea['stage']} | **Confidence Score:** {idea['confidence_score']}%")

            # Get milestones
            milestones = db.get_milestones_by_idea(selected_idea_id)

            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("**Current Milestones**")
                if milestones:
                    for milestone in milestones:
                        status_icon = {
                            'not_started': '⚪',
                            'in_progress': '🔵',
                            'done': '✅'
                        }[milestone['status']]

                        col_m1, col_m2, col_m3, col_m4 = st.columns([3, 1, 1, 1])

                        with col_m1:
                            st.markdown(f"{status_icon} **{milestone['milestone_name']}** "
                                      f"({milestone['category']}) - Weight: {milestone['weight']}")
                        with col_m2:
                            new_status = st.selectbox(
                                "Status",
                                ['not_started', 'in_progress', 'done'],
                                index=['not_started', 'in_progress', 'done'].index(milestone['status']),
                                key=f"status_{milestone['id']}",
                                label_visibility="collapsed"
                            )
                            if new_status != milestone['status']:
                                db.update_milestone_status(milestone['id'], new_status)
                                st.rerun()
                        with col_m3:
                            if st.button("🗑️", key=f"del_m_{milestone['id']}", help="Delete milestone"):
                                db.delete_milestone(milestone['id'])
                                st.rerun()

                    # Progress bar
                    total_weight = sum(m['weight'] for m in milestones)
                    completed_weight = sum(m['weight'] for m in milestones if m['status'] == 'done')
                    progress = completed_weight / total_weight if total_weight > 0 else 0

                    st.progress(progress)
                    st.caption(f"Progress: {completed_weight}/{total_weight} weighted milestones completed")
                else:
                    st.info("No milestones yet. Add one below!")

            with col2:
                st.markdown("**Add Milestone**")
                with st.form("add_milestone_form", clear_on_submit=True):
                    milestone_name = st.text_input("Milestone Name", placeholder="e.g., 10 customer interviews")
                    category = st.selectbox("Category", ['tech', 'market', 'business', 'ops'])
                    weight = st.slider("Weight", 1, 5, 3)
                    status = st.selectbox("Status", ['not_started', 'in_progress', 'done'])
                    notes = st.text_area("Notes", placeholder="Optional notes...")

                    if st.form_submit_button("➕ Add Milestone"):
                        if milestone_name:
                            db.add_milestone(selected_idea_id, milestone_name, category, status, weight, notes)
                            st.success("Milestone added!")
                            st.rerun()
                        else:
                            st.error("Milestone name is required.")


def cohort_lab():
    """Cohort Business Engine - Track Offers"""
    st.title("💼 Cohort Lab")
    st.markdown("### Cohort Business Engine - Cashflow Generation")

    # Get all offers
    offers = db.get_all_offers()

    tab1, tab2 = st.tabs(["📊 Offers Dashboard", "➕ Add New Offer"])

    with tab1:
        if not offers:
            st.info("No offers yet. Add your first offer in the 'Add New Offer' tab!")
        else:
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Offers", len(offers))
            with col2:
                avg_ai_score = sum(o['ai_score'] or 0 for o in offers) / len(offers)
                st.metric("Avg AI Score", f"{avg_ai_score:.0f}")
            with col3:
                go_offers = len([o for o in offers if o['go_no_go'] == 'go'])
                st.metric("Ready to Launch", go_offers)
            with col4:
                high_score_offers = len([o for o in offers if (o['ai_score'] or 0) >= 70])
                st.metric("High Performers", high_score_offers)

            st.markdown("---")

            # High-scoring offers
            st.subheader("🚀 High-Scoring Offers (Ready for Launch)")
            high_scoring = [o for o in offers if (o['ai_score'] or 0) >= 70]

            if high_scoring:
                for offer in high_scoring:
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

                    with col1:
                        go_badge = "✅ GO" if offer['go_no_go'] == 'go' else "🚫 NO-GO" if offer['go_no_go'] == 'no-go' else "⏳ PENDING"
                        st.markdown(f"**{offer['offer_name']}** {go_badge}")
                        if offer['notes']:
                            st.caption(offer['notes'])

                    with col2:
                        st.metric("AI Score", offer['ai_score'])
                    with col3:
                        st.metric("Pricing", f"{offer['pricing_fit']}/10")
                    with col4:
                        st.metric("Audience", f"{offer['audience_fit']}/10")
                    with col5:
                        if st.button("🗑️", key=f"del_offer_{offer['id']}", help="Delete offer"):
                            db.delete_offer(offer['id'])
                            st.rerun()

                st.markdown("---")

            # All offers table
            st.subheader("📋 All Offers")

            df = pd.DataFrame(offers)
            df = df[['offer_name', 'ai_score', 'pricing_fit', 'audience_fit', 'go_no_go', 'notes']]
            df.columns = ['Offer Name', 'AI Score', 'Pricing Fit', 'Audience Fit', 'Go/No-Go', 'Notes']

            st.dataframe(df, use_container_width=True, hide_index=True)

            # Visualization
            st.subheader("📊 Offer Analysis")

            col1, col2 = st.columns(2)

            with col1:
                # AI Score distribution
                fig = px.bar(
                    df,
                    x='Offer Name',
                    y='AI Score',
                    title='AI Score by Offer',
                    color='AI Score',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Fit scores scatter
                fig = px.scatter(
                    df,
                    x='Pricing Fit',
                    y='Audience Fit',
                    size='AI Score',
                    color='Go/No-Go',
                    hover_data=['Offer Name'],
                    title='Pricing vs Audience Fit',
                    color_discrete_map={'go': 'green', 'no-go': 'red', 'pending': 'orange'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("➕ Add New Offer")

        with st.form("add_offer_form", clear_on_submit=True):
            offer_name = st.text_input("Offer Name *", placeholder="e.g., AI Mastery Cohort")

            col1, col2, col3 = st.columns(3)

            with col1:
                ai_score = st.slider("AI Score", 0, 100, 50, help="Overall AI evaluation score")
            with col2:
                pricing_fit = st.slider("Pricing Fit", 0, 10, 5, help="How well pricing matches market")
            with col3:
                audience_fit = st.slider("Audience Fit", 0, 10, 5, help="How well it fits target audience")

            go_no_go = st.radio("Go/No-Go Decision", ['pending', 'go', 'no-go'], horizontal=True)

            notes = st.text_area("Notes", placeholder="AI pressure test results, market insights, etc.")

            submitted = st.form_submit_button("💼 Add Offer")

            if submitted:
                if offer_name:
                    db.add_offer(offer_name, ai_score, pricing_fit, audience_fit, go_no_go, notes)
                    st.success(f"✅ Offer '{offer_name}' added successfully!")
                    st.rerun()
                else:
                    st.error("Offer name is required.")


def sustainability_dashboard():
    """Personal Sustainability Engine - Energy Tracking"""
    st.title("🌿 Sustainability Dashboard")
    st.markdown("### Personal Sustainability Engine - Longevity & Energy")

    # Get energy entries
    entries = db.get_energy_entries(days=30)

    tab1, tab2 = st.tabs(["📊 Energy Tracking", "➕ Add Daily Entry"])

    with tab1:
        if not entries:
            st.info("No energy entries yet. Start tracking in the 'Add Daily Entry' tab!")
        else:
            # Metrics
            avg_energy = sum(e['energy_score'] for e in entries) / len(entries)
            recovery_days = sum(1 for e in entries if e['recovery_block'])
            recent_trend = "📈" if len(entries) >= 2 and entries[0]['energy_score'] > entries[1]['energy_score'] else "📉"

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Avg Energy Score", f"{avg_energy:.1f}/10")
            with col2:
                st.metric("Days Tracked", len(entries))
            with col3:
                st.metric("Recovery Days", recovery_days)
            with col4:
                st.metric("Recent Trend", recent_trend)

            st.markdown("---")

            # Energy chart
            st.subheader("📈 Energy Score Trend (Last 30 Days)")

            # Prepare data for chart
            df = pd.DataFrame(entries)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')

            # Create figure
            fig = go.Figure()

            # Energy score line
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['energy_score'],
                mode='lines+markers',
                name='Energy Score',
                line=dict(color='#FF4B4B', width=3),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(255, 75, 75, 0.1)'
            ))

            # Recovery blocks as background
            recovery_dates = df[df['recovery_block'] == True]['date']
            for rec_date in recovery_dates:
                fig.add_vrect(
                    x0=rec_date,
                    x1=rec_date + timedelta(days=1),
                    fillcolor="lightgreen",
                    opacity=0.2,
                    layer="below",
                    line_width=0,
                )

            # Add average line
            fig.add_hline(
                y=avg_energy,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"Average: {avg_energy:.1f}",
                annotation_position="right"
            )

            fig.update_layout(
                title="Energy Score Over Time",
                xaxis_title="Date",
                yaxis_title="Energy Score",
                yaxis=dict(range=[0, 10]),
                height=400,
                showlegend=True,
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Recent entries table
            st.subheader("📅 Recent Entries")
            display_df = df[['date', 'energy_score', 'recovery_block', 'notes']].copy()
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
            display_df['recovery_block'] = display_df['recovery_block'].map({True: '✅ Yes', False: '❌ No'})
            display_df.columns = ['Date', 'Energy Score', 'Recovery Block', 'Notes']

            st.dataframe(display_df.head(10), use_container_width=True, hide_index=True)

            # Energy distribution
            col1, col2 = st.columns(2)

            with col1:
                # Score distribution
                fig = px.histogram(
                    df,
                    x='energy_score',
                    nbins=10,
                    title='Energy Score Distribution',
                    labels={'energy_score': 'Energy Score', 'count': 'Days'},
                    color_discrete_sequence=['#FF4B4B']
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Recovery vs non-recovery comparison
                recovery_stats = df.groupby('recovery_block')['energy_score'].mean().reset_index()
                recovery_stats['recovery_block'] = recovery_stats['recovery_block'].map({True: 'Recovery Days', False: 'Regular Days'})

                fig = px.bar(
                    recovery_stats,
                    x='recovery_block',
                    y='energy_score',
                    title='Average Energy: Recovery vs Regular Days',
                    labels={'energy_score': 'Avg Energy Score', 'recovery_block': ''},
                    color='recovery_block',
                    color_discrete_map={'Recovery Days': 'lightgreen', 'Regular Days': '#FF4B4B'}
                )
                fig.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("➕ Add Daily Energy Entry")

        with st.form("add_energy_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                entry_date = st.date_input("Date *", value=date.today())
                energy_score = st.slider("Energy Score *", 1, 10, 5,
                                        help="Rate your energy level (1=exhausted, 10=peak energy)")

            with col2:
                recovery_block = st.checkbox("Recovery Block", help="Did you have a recovery/rest block today?")

            notes = st.text_area("Notes", placeholder="Sleep quality, activities, mood, etc.")

            submitted = st.form_submit_button("🌿 Log Entry")

            if submitted:
                db.add_energy_entry(str(entry_date), energy_score, recovery_block, notes)
                st.success(f"✅ Energy entry for {entry_date} logged successfully!")
                st.rerun()


def main():
    """Main application"""

    # Sidebar navigation
    st.sidebar.title("🎯 CEO Dashboard")
    st.sidebar.markdown("### Three Engines of Life")

    page = st.sidebar.radio(
        "Navigate",
        ["🚀 Studio Cockpit", "💼 Cohort Lab", "🌿 Sustainability"],
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Track your three engines:**")
    st.sidebar.markdown("🚀 **Venture Studio** - Wealth")
    st.sidebar.markdown("💼 **Cohort Business** - Cashflow")
    st.sidebar.markdown("🌿 **Personal Sustainability** - Longevity")

    st.sidebar.markdown("---")
    st.sidebar.caption("Built with Streamlit & SQLite")

    # Route to appropriate page
    if page == "🚀 Studio Cockpit":
        studio_cockpit()
    elif page == "💼 Cohort Lab":
        cohort_lab()
    elif page == "🌿 Sustainability":
        sustainability_dashboard()


if __name__ == "__main__":
    main()
