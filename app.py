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

# Soothing, warm theme with calming colors
st.markdown("""
    <style>
    /* Main background - soft, warm, soothing */
    .stApp {
        background: linear-gradient(135deg, #f5f3f0 0%, #e8e6e3 100%);
    }

    .main {
        background: transparent;
        color: #2c3e50;
        padding: 1rem 2rem;
    }

    /* Sidebar - warm, inviting */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f6f4 0%, #ede9e5 100%);
        border-right: 1px solid #d4cfc8;
    }

    /* Headers - professional but warm */
    h1, h2, h3 {
        color: #2c3e50 !important;
        font-weight: 600 !important;
    }

    h1 {
        font-size: 2.2rem !important;
    }

    .subtitle {
        color: #5a6c7d;
        font-size: 1rem;
        margin-bottom: 2rem;
    }

    /* Buttons - soft, calming accent */
    .stButton>button {
        background-color: #6b9bd1;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
        transition: all 0.2s;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .stButton>button:hover {
        background-color: #5a8bc4;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-1px);
    }

    /* Metrics - clean, light boxes */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 1.2rem;
        border-radius: 12px;
        border: 1px solid #e0dbd5;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }

    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #2c3e50;
        font-weight: 600;
    }

    div[data-testid="stMetricLabel"] {
        color: #5a6c7d;
        font-size: 0.9rem;
    }

    /* Tabs - soft and inviting */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #f8f6f4;
        border-radius: 10px;
        padding: 0.3rem;
        gap: 0.25rem;
        border: 1px solid #e0dbd5;
    }

    .stTabs [data-baseweb="tab"] {
        color: #5a6c7d;
        background-color: transparent;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background-color: #6b9bd1;
        color: white !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Forms - clean and readable */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox select,
    .stNumberInput input,
    .stDateInput input {
        background-color: white !important;
        color: #2c3e50 !important;
        border: 2px solid #e0dbd5 !important;
        border-radius: 8px !important;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus,
    .stSelectbox select:focus,
    .stNumberInput input:focus {
        border-color: #6b9bd1 !important;
        box-shadow: 0 0 0 3px rgba(107, 155, 209, 0.1) !important;
    }

    .stTextInput label,
    .stTextArea label,
    .stSelectbox label,
    .stNumberInput label,
    .stDateInput label {
        color: #2c3e50 !important;
        font-weight: 500 !important;
        margin-bottom: 0.5rem !important;
    }

    /* Radio and checkbox */
    .stRadio label,
    .stCheckbox label {
        color: #2c3e50 !important;
    }

    /* Info boxes - soft colors */
    .stAlert {
        background-color: #f8f9fa;
        border: 1px solid #e0dbd5;
        color: #2c3e50;
        border-radius: 8px;
    }

    /* Dataframes - clean white */
    .dataframe {
        background-color: white !important;
        color: #2c3e50 !important;
    }

    /* General text */
    p, span, div, label {
        color: #2c3e50;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #f8f6f4;
        border-radius: 8px;
        color: #2c3e50 !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    ::-webkit-scrollbar-track {
        background: #f8f6f4;
    }

    ::-webkit-scrollbar-thumb {
        background: #c4bcb3;
        border-radius: 5px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #a8a199;
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

    # Handle drag-and-drop moves from Kanban board
    if 'kanban_processed' not in st.session_state:
        st.session_state.kanban_processed = False

    try:
        query_params = st.query_params
        if 'move_idea' in query_params and 'new_stage' in query_params and not st.session_state.kanban_processed:
            idea_id = str(query_params['move_idea'])
            new_stage = str(query_params['new_stage'])

            # Validate stage
            valid_stages = ['goals', 'planning', 'seed', 'validation', 'mvp', 'pilot', 'scale', 'exit']
            if new_stage in valid_stages:
                # Update the idea's stage in the database
                db.update_idea_stage(idea_id, new_stage)

                # Mark as processed to prevent duplicate updates
                st.session_state.kanban_processed = True

                # Show success message
                st.success(f"✅ Idea moved to {new_stage.upper()} stage!")

                # Clear the query parameters and rerun
                st.query_params.clear()
                st.rerun()
            else:
                st.error(f"❌ Invalid stage: {new_stage}")
                st.query_params.clear()
        elif 'move_idea' not in query_params:
            # Reset the processed flag when query params are cleared
            st.session_state.kanban_processed = False
    except Exception as e:
        # Show error to help with debugging
        st.error(f"❌ Error processing card move: {str(e)}")
        st.query_params.clear()

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
            stages = ['goals', 'planning', 'seed', 'validation', 'mvp', 'pilot', 'scale', 'exit']
            stage_labels = {
                'goals': '🎯 Goals',
                'planning': '📝 Planning',
                'seed': '🌱 Seed',
                'validation': '🔍 Validation',
                'mvp': '⚙️ MVP',
                'pilot': '🧪 Pilot',
                'scale': '📈 Scale',
                'exit': '🎉 Exit'
            }

            stage_colors = {
                'goals': '#b8a89f',
                'planning': '#c4b5a8',
                'seed': '#d4a574',
                'validation': '#7e9bb5',
                'mvp': '#6b9bd1',
                'pilot': '#81b29a',
                'scale': '#5a9fb7',
                'exit': '#a67d88'
            }

            # Build HTML for horizontal scrollable Kanban board with drag-and-drop
            kanban_html = """
            <style>
                .kanban-board-wrapper {
                    width: 100%;
                    overflow-x: auto;
                    overflow-y: hidden;
                    margin: 0 -1rem;
                    padding: 0 1rem;
                }
                .kanban-board-container {
                    display: flex;
                    gap: 1.25rem;
                    padding: 1.5rem 0;
                    width: max-content;
                    min-width: 100%;
                }
                .kanban-board-wrapper::-webkit-scrollbar {
                    height: 12px;
                }
                .kanban-board-wrapper::-webkit-scrollbar-track {
                    background: #f8f6f4;
                    border-radius: 6px;
                    margin: 0 1rem;
                }
                .kanban-board-wrapper::-webkit-scrollbar-thumb {
                    background: #c4bcb3;
                    border-radius: 6px;
                }
                .kanban-board-wrapper::-webkit-scrollbar-thumb:hover {
                    background: #a8a199;
                }
                .kb-column-wrap {
                    min-width: 300px;
                    max-width: 300px;
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
                    color: #2c3e50;
                }
                .kb-column {
                    background-color: #f8f6f4;
                    padding: 1.25rem;
                    border-radius: 12px;
                    border: 1px solid #e0dbd5;
                    min-height: 400px;
                    max-height: 500px;
                    overflow-y: auto;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                }
                .kb-column::-webkit-scrollbar {
                    width: 8px;
                }
                .kb-column::-webkit-scrollbar-track {
                    background: #e8e6e3;
                    border-radius: 4px;
                }
                .kb-column::-webkit-scrollbar-thumb {
                    background: #c4bcb3;
                    border-radius: 4px;
                }
                .kb-column::-webkit-scrollbar-thumb:hover {
                    background: #a8a199;
                }
                .kb-card {
                    padding: 1.25rem;
                    border-radius: 10px;
                    background-color: white;
                    margin: 0.75rem 0;
                    border-left: 4px solid;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
                    transition: all 0.2s;
                    cursor: move;
                }
                .kb-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
                }
                .kb-card.dragging {
                    opacity: 0.5;
                }
                .kb-column.drag-over {
                    background-color: #e8e6e3;
                    border: 2px dashed #667eea;
                }
                .kb-empty {
                    text-align: center;
                    color: #8e9aaf;
                    padding: 2rem;
                    font-size: 0.9rem;
                }
            </style>
            <div class="kanban-board-wrapper">
                <div class="kanban-board-container">
            """

            for stage in stages:
                stage_ideas = [i for i in ideas if i['stage'] == stage]

                kanban_html += f'<div class="kb-column-wrap">'
                kanban_html += f'<div class="kb-header" style="border-color: {stage_colors[stage]};">{stage_labels[stage]}</div>'
                kanban_html += f'<div class="kb-column" data-stage="{stage}">'

                if stage_ideas:
                    for idea in stage_ideas:
                        confidence_color = "🟢" if idea['confidence_score'] >= 70 else "🟡" if idea['confidence_score'] >= 40 else "🔴"
                        risk_badge = " ⚠️" if idea.get('risk_flags', '') else ""

                        name = str(idea['name']).replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
                        owner = str(idea['owner']).replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

                        kanban_html += f'''
                        <div class="kb-card" draggable="true" data-idea-id="{idea['id']}" data-current-stage="{stage}" style="border-left-color: {stage_colors[stage]};">
                            <div style="font-weight: 600; margin-bottom: 0.75rem; color: #2c3e50; font-size: 1rem;">{name}{risk_badge}</div>
                            <div style="font-size: 0.9rem; color: #5a6c7d; margin-bottom: 0.5rem;">
                                {confidence_color} {idea['confidence_score']}% confidence
                            </div>
                            <div style="font-size: 0.85rem; color: #5a6c7d;">
                                👤 {owner}
                            </div>
                        </div>
                        '''
                else:
                    kanban_html += '<div class="kb-empty">No ideas</div>'

                kanban_html += '</div></div>'

            # Add JavaScript for drag-and-drop functionality
            kanban_html += '''
            <script>
                // Get all cards and columns
                const cards = document.querySelectorAll('.kb-card');
                const columns = document.querySelectorAll('.kb-column');

                // Add drag event listeners to cards
                cards.forEach(card => {
                    card.addEventListener('dragstart', handleDragStart);
                    card.addEventListener('dragend', handleDragEnd);
                });

                // Add drop event listeners to columns
                columns.forEach(column => {
                    column.addEventListener('dragover', handleDragOver);
                    column.addEventListener('drop', handleDrop);
                    column.addEventListener('dragleave', handleDragLeave);
                });

                let draggedCard = null;

                function handleDragStart(e) {
                    draggedCard = this;
                    this.classList.add('dragging');
                    e.dataTransfer.effectAllowed = 'move';
                    e.dataTransfer.setData('text/html', this.innerHTML);
                }

                function handleDragEnd(e) {
                    this.classList.remove('dragging');
                }

                function handleDragOver(e) {
                    if (e.preventDefault) {
                        e.preventDefault();
                    }
                    e.dataTransfer.dropEffect = 'move';
                    this.classList.add('drag-over');
                    return false;
                }

                function handleDragLeave(e) {
                    this.classList.remove('drag-over');
                }

                function handleDrop(e) {
                    if (e.stopPropagation) {
                        e.stopPropagation();
                    }

                    this.classList.remove('drag-over');

                    if (draggedCard) {
                        const ideaId = draggedCard.getAttribute('data-idea-id');
                        const currentStage = draggedCard.getAttribute('data-current-stage');
                        const newStage = this.getAttribute('data-stage');

                        // Only update if moved to a different stage
                        if (currentStage !== newStage) {
                            // Store the move in localStorage
                            localStorage.setItem('kanban_move', JSON.stringify({
                                idea_id: ideaId,
                                new_stage: newStage,
                                timestamp: Date.now()
                            }));

                            // Reload the parent page to apply the change
                            // Use window.parent to escape the iframe and reload the actual Streamlit page
                            window.parent.location.href = window.parent.location.pathname + '?move_idea=' + ideaId + '&new_stage=' + newStage;
                        }
                    }

                    return false;
                }
            </script>
            '''

            kanban_html += '</div></div>'  # Close kanban-board-container and kanban-board-wrapper

            # Render the Kanban board
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

                    # Edit Form
                    with st.expander(f"✏️ Edit Idea: {selected_idea['name']}", expanded=False):
                        with st.form(f"edit_idea_form_{selected_idea['id']}"):
                            edit_name = st.text_input("Idea Name", value=selected_idea['name'])

                            col1, col2 = st.columns(2)
                            with col1:
                                stages = ['goals', 'planning', 'seed', 'validation', 'mvp', 'pilot', 'scale', 'exit']
                                current_stage_idx = stages.index(selected_idea['stage']) if selected_idea['stage'] in stages else 0
                                edit_stage = st.selectbox("Stage", stages, index=current_stage_idx)
                            with col2:
                                edit_owner = st.text_input("Owner", value=selected_idea.get('owner', ''))

                            edit_description = st.text_area("Description", value=selected_idea.get('description', ''))
                            edit_next_steps = st.text_area("Next Steps", value=selected_idea.get('next_steps', ''))
                            edit_risk_flags = st.text_input("Risk Flags", value=selected_idea.get('risk_flags', ''))

                            submitted = st.form_submit_button("💾 Save Changes")

                            if submitted:
                                if edit_name and edit_owner:
                                    db.update_idea(
                                        selected_idea['id'],
                                        name=edit_name,
                                        description=edit_description,
                                        stage=edit_stage,
                                        owner=edit_owner,
                                        next_steps=edit_next_steps,
                                        risk_flags=edit_risk_flags
                                    )
                                    st.success(f"✅ Updated '{edit_name}' successfully!")
                                    st.rerun()
                                else:
                                    st.error("Name and Owner are required fields.")

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
                stage = st.selectbox("Stage *", ['goals', 'planning', 'seed', 'validation', 'mvp', 'pilot', 'scale', 'exit'])
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
        with open("USER_GUIDE.md", "r", encoding="utf-8") as f:
            guide_content = f.read()

        # Display the markdown content
        st.markdown(guide_content, unsafe_allow_html=True)

    except FileNotFoundError:
        st.error("USER_GUIDE.md not found. Please ensure the file exists in the project directory.")
        st.info("You can find the user guide at: https://github.com/your-repo/USER_GUIDE.md")
    except UnicodeDecodeError:
        st.error("Error reading USER_GUIDE.md. The file may contain invalid characters.")
        st.info("Try re-downloading the file or check the file encoding.")


def main():
    """Main application"""

    # Initialize session state for navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'studio'

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

    # Only update session state if NOT in admin or help mode
    # This prevents radio button from overriding admin/help navigation
    if st.session_state.current_page not in ['admin', 'help']:
        if page == "🚀 Studio Cockpit":
            st.session_state.current_page = 'studio'
        elif page == "💼 Cohort Lab":
            st.session_state.current_page = 'cohort'
        elif page == "🌿 Sustainability":
            st.session_state.current_page = 'sustainability'

    st.sidebar.markdown("---")
    st.sidebar.markdown('<span class="engine-label wealth">WEALTH</span>', unsafe_allow_html=True)
    st.sidebar.markdown('<span class="engine-label cashflow">CASHFLOW</span>', unsafe_allow_html=True)
    st.sidebar.markdown('<span class="engine-label longevity">LONGEVITY</span>', unsafe_allow_html=True)

    st.sidebar.markdown("---")

    # Admin section
    st.sidebar.markdown("### ADMIN")
    if st.sidebar.button("⚙️ Admin Panel", use_container_width=True):
        st.session_state.current_page = 'admin'
        st.rerun()

    st.sidebar.markdown("---")

    # Help section
    st.sidebar.markdown("### HELP")
    if st.sidebar.button("📖 User Guide", use_container_width=True):
        st.session_state.current_page = 'help'
        st.rerun()

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

    # Route to appropriate page based on session state
    if st.session_state.current_page == 'help':
        help_page()
    elif st.session_state.current_page == 'admin':
        admin_panel(db)
    elif st.session_state.current_page == 'studio':
        studio_cockpit()
    elif st.session_state.current_page == 'cohort':
        cohort_lab()
    elif st.session_state.current_page == 'sustainability':
        sustainability_dashboard()


if __name__ == "__main__":
    main()
