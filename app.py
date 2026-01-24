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
from admin_panel import admin_panel
import io
import streamlit.components.v1 as components

# Page configuration
st.set_page_config(
    page_title="CEO Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean, readable theme
st.markdown("""
    <style>
    /* Main background - lighter, easier on eyes */
    .stApp {
        background-color: #1e2433;
    }

    .main {
        background-color: #1e2433;
        color: #ffffff;
        padding: 1rem 2rem;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #252b3b;
    }

    /* Headers - clean and readable */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    h1 {
        font-size: 2.2rem !important;
    }

    .subtitle {
        color: #b8c5db;
        font-size: 1rem;
        margin-bottom: 2rem;
    }

    /* Buttons - simple and clear */
    .stButton>button {
        background-color: #4c6ef5;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: background-color 0.2s;
    }

    .stButton>button:hover {
        background-color: #5c7cfa;
    }

    /* Metrics - clean boxes */
    div[data-testid="stMetric"] {
        background-color: #2d3548;
        padding: 1.2rem;
        border-radius: 8px;
        border: 1px solid #3d4564;
    }

    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #ffffff;
        font-weight: 600;
    }

    div[data-testid="stMetricLabel"] {
        color: #b8c5db;
        font-size: 0.9rem;
    }

    /* Tabs - clean and simple */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #2d3548;
        border-radius: 8px;
        padding: 0.25rem;
        gap: 0.25rem;
    }

    .stTabs [data-baseweb="tab"] {
        color: #b8c5db;
        background-color: transparent;
        border-radius: 6px;
        padding: 0.5rem 1rem;
    }

    .stTabs [aria-selected="true"] {
        background-color: #4c6ef5;
        color: white !important;
    }

    /* Forms - clear and visible */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox select,
    .stNumberInput input {
        background-color: #2d3548 !important;
        color: #ffffff !important;
        border: 1px solid #3d4564 !important;
        border-radius: 6px !important;
    }

    .stTextInput label,
    .stTextArea label,
    .stSelectbox label,
    .stNumberInput label,
    .stDateInput label {
        color: #ffffff !important;
        font-weight: 500 !important;
        margin-bottom: 0.5rem !important;
    }

    /* Radio and checkbox */
    .stRadio label,
    .stCheckbox label {
        color: #ffffff !important;
    }

    /* Info boxes */
    .stAlert {
        background-color: #2d3548;
        border: 1px solid #3d4564;
        color: #ffffff;
        border-radius: 6px;
    }

    /* Dataframes */
    .dataframe {
        background-color: #2d3548 !important;
        color: #ffffff !important;
    }

    /* Simplify everything else */
    p, span, div {
        color: #ffffff;
    }

    </style>
    """, unsafe_allow_html=True)

# Initialize database
db = Database()


def export_to_csv(data, filename):
    """Export data to CSV"""
    df = pd.DataFrame(data)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()


def studio_cockpit():
    """Venture Studio Engine - Track Ideas and Milestones"""

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h1>🚀 Studio Cockpit</h1>", unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Venture Studio Engine — Building Wealth</p>', unsafe_allow_html=True)

    # Get all ideas
    ideas = db.get_all_ideas()

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Portfolio Overview", "📈 Analytics", "➕ Add New Idea", "🎯 Manage Milestones"])

    with tab1:
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📚 Total Ideas", len(ideas))
        with col2:
            avg_confidence = sum(i['confidence_score'] for i in ideas) / len(ideas) if ideas else 0
            st.metric("📈 Avg Confidence", f"{avg_confidence:.0f}%")
        with col3:
            at_risk = len([i for i in ideas if i.get('risk_flags', '')])
            st.metric("⚠️ At Risk", at_risk)
        with col4:
            active_ideas = len([i for i in ideas if i['stage'] not in ['exit']])
            st.metric("✨ Active Ideas", active_ideas)

        st.markdown("---")

        # Export buttons
        col1, col2, col3, col4 = st.columns([1, 1, 1.5, 1.5])
        with col1:
            if st.button("📄 Export Ideas CSV"):
                csv_data = export_to_csv(ideas, "ideas.csv")
                st.download_button(
                    label="⬇️ Download Ideas CSV",
                    data=csv_data,
                    file_name=f"ideas_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

        with col2:
            if ideas:
                all_milestones = []
                for idea in ideas:
                    milestones = db.get_milestones_by_idea(idea['id'])
                    for m in milestones:
                        m['idea_name'] = idea['name']
                    all_milestones.extend(milestones)

                if st.button("📄 Export Milestones CSV"):
                    csv_data = export_to_csv(all_milestones, "milestones.csv")
                    st.download_button(
                        label="⬇️ Download Milestones CSV",
                        data=csv_data,
                        file_name=f"milestones_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )

        st.markdown("---")

        # Kanban Board View
        st.subheader("📋 Stage Pipeline")

        if not ideas:
            st.info("No ideas yet. Add your first idea in the 'Add New Idea' tab!")
        else:
            stages = ['seed', 'validation', 'mvp', 'pilot', 'scale', 'exit']
            stage_labels = {
                'seed': '🌱 Seed',
                'validation': '🔍 Validation',
                'mvp': '⚙️ MVP',
                'pilot': '🧪 Pilot',
                'scale': '📈 Scale',
                'exit': '🎉 Exit'
            }

            stage_colors = {
                'seed': '#8b4513',
                'validation': '#4a5568',
                'mvp': '#5a67d8',
                'pilot': '#2c7a7b',
                'scale': '#3182ce',
                'exit': '#742a2a'
            }

            # Build HTML for horizontal scrollable Kanban board
            kanban_html = """
            <style>
                .kanban-board-container {
                    display: flex;
                    overflow-x: auto;
                    gap: 1rem;
                    padding: 1rem 0;
                }
                .kanban-board-container::-webkit-scrollbar {
                    height: 10px;
                }
                .kanban-board-container::-webkit-scrollbar-track {
                    background: #2d3548;
                    border-radius: 4px;
                }
                .kanban-board-container::-webkit-scrollbar-thumb {
                    background: #4c6ef5;
                    border-radius: 4px;
                }
                .kb-column-wrap {
                    min-width: 300px;
                    flex-shrink: 0;
                }
                .kb-header {
                    font-weight: 600;
                    font-size: 0.95rem;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 1rem;
                    padding-bottom: 0.75rem;
                    border-bottom: 3px solid;
                    color: #ffffff;
                }
                .kb-column {
                    background-color: #2d3548;
                    padding: 1rem;
                    border-radius: 8px;
                    border: 1px solid #3d4564;
                    min-height: 500px;
                }
                .kb-card {
                    padding: 1.25rem;
                    border-radius: 6px;
                    background-color: #3d4564;
                    margin: 0.75rem 0;
                    border-left: 4px solid;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
                    transition: all 0.2s;
                }
                .kb-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                }
                .kb-empty {
                    text-align: center;
                    color: #8892a6;
                    padding: 2rem;
                    font-size: 0.9rem;
                }
            </style>
            <div class="kanban-board-container">
            """

            for stage in stages:
                stage_ideas = [i for i in ideas if i['stage'] == stage]

                kanban_html += f'<div class="kb-column-wrap">'
                kanban_html += f'<div class="kb-header" style="border-color: {stage_colors[stage]};">{stage_labels[stage]}</div>'
                kanban_html += f'<div class="kb-column">'

                if stage_ideas:
                    for idea in stage_ideas:
                        confidence_color = "🟢" if idea['confidence_score'] >= 70 else "🟡" if idea['confidence_score'] >= 40 else "🔴"
                        risk_badge = " ⚠️" if idea.get('risk_flags', '') else ""

                        name = str(idea['name']).replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
                        owner = str(idea['owner']).replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

                        kanban_html += f'''
                        <div class="kb-card" style="border-left-color: {stage_colors[stage]};">
                            <div style="font-weight: 600; margin-bottom: 0.75rem; color: #ffffff; font-size: 1rem;">{name}{risk_badge}</div>
                            <div style="font-size: 0.9rem; color: #b8c5db; margin-bottom: 0.5rem;">
                                {confidence_color} {idea['confidence_score']}% confidence
                            </div>
                            <div style="font-size: 0.85rem; color: #b8c5db;">
                                👤 {owner}
                            </div>
                        </div>
                        '''
                else:
                    kanban_html += '<div class="kb-empty">No ideas</div>'

                kanban_html += '</div></div>'

            kanban_html += '</div>'

            components.html(kanban_html, height=600, scrolling=False)

            # Action panel for idea management
            st.markdown("---")
            st.markdown("### 🎯 Manage Ideas")

            # Create dropdown to select and manage ideas
            if ideas:
                idea_names = {f"{i['name']} ({i['stage']})": i for i in ideas}
                selected_idea_name = st.selectbox("Select an idea to manage:", list(idea_names.keys()))

                if selected_idea_name:
                    selected_idea = idea_names[selected_idea_name]

                    col1, col2 = st.columns(2)
                    with col1:
                        with st.expander(f"📝 View Details: {selected_idea['name']}", expanded=False):
                            st.write(f"**Description:** {selected_idea.get('description', 'N/A')}")
                            st.write(f"**Next Steps:** {selected_idea.get('next_steps', 'N/A')}")
                            st.write(f"**Risk Flags:** {selected_idea.get('risk_flags', 'None')}")
                            st.write(f"**Confidence:** {selected_idea['confidence_score']}%")
                            st.write(f"**Owner:** {selected_idea['owner']}")

                    with col2:
                        if st.button("🗑️ Delete This Idea", key=f"del_manage_{selected_idea['id']}"):
                            db.delete_idea(selected_idea['id'])
                            st.success(f"Deleted '{selected_idea['name']}'")
                            st.rerun()

            st.markdown("---")

            # Detailed table view
            st.subheader("📊 Detailed View")
            df = pd.DataFrame(ideas)
            display_cols = ['name', 'stage', 'owner', 'confidence_score', 'risk_flags', 'next_steps']
            df_display = df[[col for col in display_cols if col in df.columns]]
            df_display.columns = ['Idea', 'Stage', 'Owner', 'Confidence %', 'Risk Flags', 'Next Steps']
            st.dataframe(df_display, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("📈 Analytics")

        if not ideas:
            st.info("Add some ideas to see analytics!")
        else:
            # Charts
            col1, col2 = st.columns(2)

            with col1:
                # Ideas by stage
                stage_counts = pd.DataFrame([{'Stage': i['stage'], 'Count': 1} for i in ideas])
                stage_summary = stage_counts.groupby('Stage').count().reset_index()

                fig = px.bar(
                    stage_summary,
                    x='Stage',
                    y='Count',
                    title='Ideas by Stage',
                    color='Stage',
                    color_discrete_map={
                        'seed': '#8b4513',
                        'validation': '#4a5568',
                        'mvp': '#5a67d8',
                        'pilot': '#2c7a7b',
                        'scale': '#3182ce',
                        'exit': '#742a2a'
                    }
                )
                fig.update_layout(
                    showlegend=False,
                    height=400,
                    plot_bgcolor='#1a1f2e',
                    paper_bgcolor='#1a1f2e',
                    font=dict(color='#e0e6ed')
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Confidence distribution
                fig = px.histogram(
                    pd.DataFrame(ideas),
                    x='confidence_score',
                    nbins=10,
                    title='Confidence Score Distribution',
                    color_discrete_sequence=['#667eea']
                )
                fig.update_layout(
                    height=400,
                    plot_bgcolor='#1a1f2e',
                    paper_bgcolor='#1a1f2e',
                    font=dict(color='#e0e6ed'),
                    xaxis_title='Confidence Score',
                    yaxis_title='Number of Ideas'
                )
                st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("➕ Add New Idea")

        with st.form("add_idea_form", clear_on_submit=True):
            idea_name = st.text_input("Idea Name *", placeholder="e.g., AI-Powered CRM")

            col1, col2 = st.columns(2)
            with col1:
                stage = st.selectbox("Stage *", ['seed', 'validation', 'mvp', 'pilot', 'scale', 'exit'])
            with col2:
                owner = st.text_input("Owner *", placeholder="e.g., John Doe")

            description = st.text_area("Description", placeholder="Brief summary of the idea...")
            next_steps = st.text_area("Next Steps", placeholder="Immediate next actions to take...")
            risk_flags = st.text_input("Risk Flags", placeholder="e.g., Market saturation, Technical complexity")

            submitted = st.form_submit_button("🚀 Create Idea")

            if submitted:
                if idea_name and owner:
                    idea_id = db.add_idea(idea_name, description, stage, owner, next_steps, risk_flags)
                    st.success(f"✅ Idea '{idea_name}' added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all required fields (*).")

    with tab4:
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

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Stage", idea['stage'])
            with col2:
                st.metric("Confidence Score", f"{idea['confidence_score']}%")
            with col3:
                risk_status = "⚠️ At Risk" if idea.get('risk_flags', '') else "✅ On Track"
                st.metric("Status", risk_status)

            st.markdown("---")

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

                        col_m1, col_m2, col_m3 = st.columns([3, 1, 1])

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
                    st.caption(f"Progress: {completed_weight}/{total_weight} weighted milestones completed ({progress*100:.0f}%)")
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
    st.markdown("<h1>💼 Cohort Lab</h1>", unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Cohort Business Engine — Cashflow Generation</p>', unsafe_allow_html=True)

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
                st.metric("📦 Total Offers", len(offers))
            with col2:
                avg_ai_score = sum(o['ai_score'] or 0 for o in offers) / len(offers)
                st.metric("🤖 Avg AI Score", f"{avg_ai_score:.0f}")
            with col3:
                go_offers = len([o for o in offers if o['go_no_go'] == 'go'])
                st.metric("🚀 Ready to Launch", go_offers)
            with col4:
                high_score_offers = len([o for o in offers if (o['ai_score'] or 0) >= 70])
                st.metric("⭐ High Performers", high_score_offers)

            st.markdown("---")

            # Export button
            if st.button("📄 Export Offers CSV"):
                csv_data = export_to_csv(offers, "offers.csv")
                st.download_button(
                    label="⬇️ Download Offers CSV",
                    data=csv_data,
                    file_name=f"offers_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

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
                fig.update_layout(
                    showlegend=False,
                    height=400,
                    plot_bgcolor='#1a1f2e',
                    paper_bgcolor='#1a1f2e',
                    font=dict(color='#e0e6ed')
                )
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
                    color_discrete_map={'go': '#48bb78', 'no-go': '#f56565', 'pending': '#ed8936'}
                )
                fig.update_layout(
                    height=400,
                    plot_bgcolor='#1a1f2e',
                    paper_bgcolor='#1a1f2e',
                    font=dict(color='#e0e6ed')
                )
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
    st.markdown("<h1>🌿 Sustainability Dashboard</h1>", unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Personal Sustainability Engine — Longevity & Energy</p>', unsafe_allow_html=True)

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
                st.metric("⚡ Avg Energy Score", f"{avg_energy:.1f}/10")
            with col2:
                st.metric("📅 Days Tracked", len(entries))
            with col3:
                st.metric("🛌 Recovery Days", recovery_days)
            with col4:
                st.metric("📊 Recent Trend", recent_trend)

            st.markdown("---")

            # Export button
            if st.button("📄 Export Energy CSV"):
                csv_data = export_to_csv(entries, "energy_tracking.csv")
                st.download_button(
                    label="⬇️ Download Energy CSV",
                    data=csv_data,
                    file_name=f"energy_tracking_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

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
                line=dict(color='#667eea', width=3),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(102, 126, 234, 0.2)'
            ))

            # Recovery blocks as background
            recovery_dates = df[df['recovery_block'] == True]['date']
            for rec_date in recovery_dates:
                fig.add_vrect(
                    x0=rec_date,
                    x1=rec_date + timedelta(days=1),
                    fillcolor="#48bb78",
                    opacity=0.2,
                    layer="below",
                    line_width=0,
                )

            # Add average line
            fig.add_hline(
                y=avg_energy,
                line_dash="dash",
                line_color="#a8b3cf",
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
                hovermode='x unified',
                plot_bgcolor='#1a1f2e',
                paper_bgcolor='#1a1f2e',
                font=dict(color='#e0e6ed')
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
                    color_discrete_sequence=['#667eea']
                )
                fig.update_layout(
                    height=300,
                    plot_bgcolor='#1a1f2e',
                    paper_bgcolor='#1a1f2e',
                    font=dict(color='#e0e6ed')
                )
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
                    color_discrete_map={'Recovery Days': '#48bb78', 'Regular Days': '#667eea'}
                )
                fig.update_layout(
                    showlegend=False,
                    height=300,
                    plot_bgcolor='#1a1f2e',
                    paper_bgcolor='#1a1f2e',
                    font=dict(color='#e0e6ed')
                )
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


def help_page():
    """Display the user guide"""
    st.markdown("<h1>📖 User Guide</h1>", unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Complete guide to using the CEO Dashboard</p>', unsafe_allow_html=True)

    try:
        with open("USER_GUIDE.md", "r") as f:
            guide_content = f.read()

        # Display the markdown content
        st.markdown(guide_content, unsafe_allow_html=True)

    except FileNotFoundError:
        st.error("USER_GUIDE.md not found. Please ensure the file exists in the project directory.")
        st.info("You can find the user guide at: https://github.com/your-repo/USER_GUIDE.md")


def main():
    """Main application"""

    # Sidebar navigation
    st.sidebar.markdown("<h1 style='text-align: center;'>🎯 CEO Dashboard</h1>", unsafe_allow_html=True)
    st.sidebar.markdown("<p style='text-align: center; color: #a8b3cf;'>Command Center</p>", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    st.sidebar.markdown("### ENGINES")

    page = st.sidebar.radio(
        "Navigate",
        ["🚀 Studio Cockpit", "💼 Cohort Lab", "🌿 Sustainability"],
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown('<span class="engine-label wealth">WEALTH</span>', unsafe_allow_html=True)
    st.sidebar.markdown('<span class="engine-label cashflow">CASHFLOW</span>', unsafe_allow_html=True)
    st.sidebar.markdown('<span class="engine-label longevity">LONGEVITY</span>', unsafe_allow_html=True)

    st.sidebar.markdown("---")

    # Admin section
    st.sidebar.markdown("### ADMIN")
    admin_page = st.sidebar.button("⚙️ Admin Panel", use_container_width=True)

    st.sidebar.markdown("---")

    # Help section
    st.sidebar.markdown("### HELP")
    help_page_button = st.sidebar.button("📖 User Guide", use_container_width=True)

    with st.sidebar.expander("💡 Quick Tips"):
        st.markdown("""
        **🚀 Studio Cockpit**
        - Track ideas from seed to exit
        - Add milestones to boost confidence
        - Use risk flags for blockers

        **💼 Cohort Lab**
        - Manage cohort offers
        - Track 3 key metrics (0-100)
        - Monitor performance trends

        **🌿 Sustainability**
        - Log daily energy (1-10)
        - Track 5 dimensions
        - Identify patterns

        **💡 Pro Tips**
        - Export data regularly (📄 buttons)
        - Use Admin Panel for insights
        - Click "User Guide" for full docs
        """)

    st.sidebar.markdown("---")

    # Database indicator
    if db.use_turso:
        st.sidebar.success("☁️ Using Turso Cloud")
    else:
        st.sidebar.info("💻 Using Local SQLite")

    st.sidebar.caption("Built with Streamlit & Turso")

    # Route to appropriate page
    if help_page_button:
        help_page()
    elif admin_page:
        admin_panel(db)
    elif page == "🚀 Studio Cockpit":
        studio_cockpit()
    elif page == "💼 Cohort Lab":
        cohort_lab()
    elif page == "🌿 Sustainability":
        sustainability_dashboard()


if __name__ == "__main__":
    main()
