"""
Admin Panel for CEO Dashboard
Comprehensive CRUD operations, settings, and AI insights
"""

import streamlit as st
import pandas as pd
from database import Database
from ai_insights import ai_insights
from monday_import import MondayImporter
import json


def admin_panel(db: Database):
    """Admin Panel with CRUD and settings"""

    # Admin panel matches soothing theme
    st.markdown("""
        <style>
        /* Admin panel - matches main theme */
        .stMarkdown, .stMarkdown p, .stMarkdown li {
            color: #2c3e50 !important;
        }

        /* All labels */
        label {
            color: #2c3e50 !important;
            font-weight: 500 !important;
        }

        /* Headings */
        h1, h2, h3, h4 {
            color: #2c3e50 !important;
        }

        /* Caption text */
        .stCaption {
            color: #5a6c7d !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="admin-panel">', unsafe_allow_html=True)

    # Add back button at the top
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("<h1>⚙️ Admin Panel</h1>", unsafe_allow_html=True)
        st.markdown('<p class="subtitle">System Administration & Settings</p>', unsafe_allow_html=True)
    with col2:
        if st.button("← Back", key="exit_admin", help="Return to Studio Cockpit"):
            st.session_state.current_page = 'studio'
            st.rerun()

    # Tabs for different admin functions
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard Stats",
        "📥 Import Data",
        "🤖 AI Insights",
        "🗂️ Data Management",
        "🎨 UI Customization",
        "⚙️ Settings"
    ])

    with tab1:
        stats_dashboard(db)

    with tab2:
        import_data_panel(db)

    with tab3:
        ai_insights_panel(db)

    with tab4:
        data_management(db)

    with tab5:
        ui_customization(db)

    with tab6:
        system_settings(db)

    st.markdown('</div>', unsafe_allow_html=True)


def stats_dashboard(db: Database):
    """Display comprehensive database statistics"""

    st.subheader("📊 Database Statistics")

    stats = db.get_database_stats()

    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💡 Total Ideas", stats['total_ideas'])
    with col2:
        st.metric("🎯 Total Milestones", stats['total_milestones'])
    with col3:
        st.metric("💼 Total Offers", stats['total_offers'])
    with col4:
        st.metric("🌿 Energy Entries", stats['total_energy_entries'])

    st.markdown("---")

    # Detailed stats
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Ideas by Stage**")
        if stats['ideas_by_stage']:
            stage_df = pd.DataFrame([
                {'Stage': k, 'Count': v}
                for k, v in stats['ideas_by_stage'].items()
            ])
            st.dataframe(stage_df, use_container_width=True, hide_index=True)
        else:
            st.info("No ideas yet")

    with col2:
        st.markdown("**Portfolio Health**")
        st.metric("Average Confidence Score", f"{stats['avg_confidence']:.1f}%")

        health_score = stats['avg_confidence']
        if health_score >= 70:
            st.success("🟢 Excellent portfolio health")
        elif health_score >= 50:
            st.warning("🟡 Moderate portfolio health")
        else:
            st.error("🔴 Portfolio needs attention")


def import_data_panel(db: Database):
    """Import data from Monday.com and other sources"""

    st.subheader("📥 Import Data from Monday.com")

    st.markdown("""
    Upload exported CSV or Excel files from Monday.com to import your projects and tasks.

    **What gets imported:**
    - 📊 **Projects** → Ideas in Studio Cockpit
    - ✅ **Tasks** → Milestones for each idea
    - 👤 **Owners** → Assigned to ideas
    - 🎯 **Status** → Mapped to pipeline stages
    """)

    st.markdown("---")

    # File uploader
    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Upload Monday.com Export (CSV or Excel)",
            type=['csv', 'xlsx', 'xls'],
            help="Export your Monday.com board as CSV or Excel and upload it here",
            key="monday_file_uploader"
        )

    with col2:
        st.markdown("### 📄 Sample Format")
        from monday_import import create_sample_monday_csv
        sample_csv = create_sample_monday_csv()
        st.download_button(
            label="📥 Download Sample CSV",
            data=sample_csv,
            file_name="monday_sample.csv",
            mime="text/csv",
            use_container_width=True,
            help="Download a sample CSV to see the expected format"
        )

    # Debug info
    if uploaded_file is None:
        st.info("👆 Upload a CSV or Excel file to begin importing")

    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")

        # Check for Excel support
        file_ext = uploaded_file.name.split('.')[-1].lower()
        if file_ext in ['xlsx', 'xls']:
            try:
                import openpyxl
                st.info(f"📊 Detected Excel file - using openpyxl to parse")
            except ImportError:
                st.error("❌ Excel support not installed. Install with: `pip install openpyxl`")
                st.stop()

        try:
            # Initialize importer
            importer = MondayImporter()
            st.info("🔧 Initialized Monday.com importer")

            # Determine file type
            file_type = uploaded_file.name.split('.')[-1].lower()
            if file_type == 'xlsx':
                file_type = 'xlsx'
            elif file_type == 'xls':
                file_type = 'xls'
            else:
                file_type = 'csv'

            st.info(f"📄 Parsing {file_type.upper()} file...")

            # Parse file
            file_content = uploaded_file.read()
            df = importer.parse_file(file_content, file_type)

            if df is not None and not df.empty:
                st.success(f"✅ Parsed {len(df)} rows from file")

                # Show columns detected
                columns_list = df.columns.tolist()
                st.info(f"**📋 Columns found:** {', '.join(columns_list)}")

                # Show what we're looking for
                with st.expander("ℹ️ What columns we expect"):
                    st.markdown("""
                    We look for these column names (case-insensitive):
                    - **Name/Item:** Name, Item, Task, name, item, task
                    - **Board/Project:** Board, Project, board, project
                    - **Status:** Status, status, Stage, stage
                    - **Owner:** Owner, Person, owner, person, Assigned To
                    - **Description:** Description, Notes, Summary
                    - **Due Date:** Due Date, Deadline, Date

                    At minimum, we need a **Name** or **Item** column.
                    """)

                # Show preview of data
                with st.expander("📋 View Raw Data Preview"):
                    # Create a copy for display and fix data types
                    df_display = df.head(10).copy()

                    # Convert datetime columns to strings for Arrow compatibility
                    for col in df_display.columns:
                        if df_display[col].dtype == 'object':
                            try:
                                # Try to convert any datetime objects to strings
                                df_display[col] = df_display[col].apply(lambda x: str(x) if pd.notna(x) else '')
                            except:
                                pass

                    st.dataframe(df_display, use_container_width=True)

                st.markdown("---")

                # Import the data
                ideas, errors, warnings = importer.import_from_dataframe(df)

                # Show errors and warnings
                if errors:
                    st.error("❌ **Errors:**")
                    for error in errors:
                        st.error(f"• {error}")

                if warnings:
                    st.warning("⚠️ **Warnings:**")
                    for warning in warnings:
                        st.warning(f"• {warning}")

                # Show import preview
                if ideas:
                    st.markdown("### 📊 Import Preview")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Projects/Ideas", len(ideas))
                    with col2:
                        total_milestones = sum(len(idea.get('milestones', [])) for idea in ideas)
                        st.metric("Total Milestones", total_milestones)
                    with col3:
                        stages = [idea['stage'] for idea in ideas]
                        unique_stages = len(set(stages))
                        st.metric("Stages Detected", unique_stages)

                    st.markdown("---")

                    # Show detailed preview
                    st.markdown("### 📝 Detailed Preview")

                    for idx, idea in enumerate(ideas[:10]):  # Show first 10
                        with st.expander(f"🎯 {idea['name']} ({idea['stage'].upper()})"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Owner:** {idea['owner']}")
                                st.write(f"**Stage:** {idea['stage']}")
                                desc = idea.get('description', '')
                                desc_preview = desc[:100] + "..." if len(desc) > 100 else desc
                                st.write(f"**Description:** {desc_preview}")
                            with col2:
                                milestones = idea.get('milestones', [])
                                st.write(f"**Milestones:** {len(milestones)}")
                                if milestones:
                                    st.write("**Tasks:**")
                                    for m in milestones[:5]:
                                        st.write(f"  • {m['name']} ({m['status']})")
                                    if len(milestones) > 5:
                                        st.write(f"  *...and {len(milestones) - 5} more*")

                    if len(ideas) > 10:
                        st.info(f"ℹ️ Showing 10 of {len(ideas)} projects. All will be imported.")

                    st.markdown("---")

                    # Import confirmation
                    st.markdown("### ✅ Confirm Import")

                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        import_mode = st.radio(
                            "Import Mode",
                            ["Add to existing data", "Replace all ideas (delete existing)"],
                            help="Choose whether to add to or replace your current ideas"
                        )

                    with col2:
                        st.write("")  # Spacing
                        st.write("")  # Spacing

                    with col3:
                        st.write("")  # Spacing
                        st.write("")  # Spacing

                    # Import button
                    if st.button("🚀 Import Data", type="primary", use_container_width=True):
                        # Delete existing if replace mode
                        if import_mode == "Replace all ideas (delete existing)":
                            db.delete_all_ideas()
                            st.info("🗑️ Deleted existing ideas")

                        # Import ideas
                        imported_count = 0
                        milestone_count = 0

                        try:
                            for idea_data in ideas:
                                # Get milestones (don't pop to avoid modifying original)
                                milestones = idea_data.get('milestones', [])

                                # Add idea
                                idea_id = db.add_idea(
                                    name=idea_data['name'],
                                    description=idea_data['description'],
                                    stage=idea_data['stage'],
                                    owner=idea_data['owner'],
                                    next_steps=idea_data.get('next_steps', ''),
                                    risk_flags=idea_data.get('risk_flags', '')
                                )

                                imported_count += 1

                                # Add milestones
                                for milestone in milestones:
                                    db.add_milestone(
                                        idea_id=idea_id,
                                        milestone_name=milestone['name'],
                                        category='business',  # Default category for imported milestones
                                        status=milestone['status'],
                                        weight=milestone['weight'],
                                        notes='Imported from Monday.com'
                                    )
                                    milestone_count += 1

                            st.success(f"""
                            ✅ **Import Complete!**

                            - Imported {imported_count} ideas
                            - Created {milestone_count} milestones
                            """)

                            st.balloons()

                            # Add button to navigate to Studio Cockpit
                            col1, col2, col3 = st.columns([1, 1, 1])
                            with col2:
                                if st.button("🚀 View in Studio Cockpit", type="primary", use_container_width=True):
                                    st.session_state.current_page = 'studio'
                                    st.rerun()

                        except Exception as e:
                            st.error(f"❌ Error during import: {str(e)}")
                            st.info("Some data may have been partially imported. Check Studio Cockpit.")

                else:
                    st.warning("No data could be imported. Please check the file format.")

            else:
                st.error("❌ Could not parse the file. Please check the format.")

        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.info("💡 Make sure your file is a valid Monday.com export in CSV or Excel format.")

            # Show detailed error in expander for debugging
            with st.expander("🔍 Technical Details (for debugging)"):
                import traceback
                st.code(traceback.format_exc())

    else:
        # Show instructions when no file uploaded
        st.info("""
        ### 📖 How to Import from Monday.com

        1. **Export from Monday.com:**
           - Open your Monday.com board
           - Click the menu (⋯) → Export → Excel or CSV
           - Download the file

        2. **Upload here:**
           - Click "Browse files" above
           - Select your exported file
           - Review the preview

        3. **Confirm import:**
           - Choose import mode (add or replace)
           - Click "Import Data"

        **Supported columns:** Board, Project, Item, Name, Status, Owner, Person, Description, Notes, Due Date

        **Status mapping:**
        - Backlog/Todo → Seed
        - Research/Stuck → Validation
        - In Progress/Doing → MVP
        - Testing → Pilot
        - Production → Scale
        - Done/Completed → Exit
        """)


def ai_insights_panel(db: Database):
    """AI-powered insights and recommendations"""

    st.subheader("🤖 AI-Powered Insights")

    if not ai_insights.use_openai:
        st.info("""
        💡 **AI Insights Available** - Currently using rule-based analysis.

        To enable advanced GPT-4 insights:
        1. Get an OpenAI API key from https://platform.openai.com/api-keys
        2. Add to your `.env` file: `OPENAI_API_KEY=your-key-here`
        3. Install OpenAI: `pip install openai`
        4. Restart the app

        **Current Mode:** Rule-based insights (fast, free, always available)
        """)
    else:
        st.success("✨ Advanced AI insights powered by GPT-4")

    # Generate insights button
    if st.button("🔮 Generate Portfolio Insights", type="primary"):
        with st.spinner("Analyzing portfolio..."):
            ideas = db.get_all_ideas()

            if not ideas:
                st.warning("Add some ideas to generate insights!")
            else:
                insights = ai_insights.generate_portfolio_insights(ideas)

                # Display insights
                st.markdown("### 📋 Portfolio Summary")
                st.markdown(insights['summary'])

                st.markdown("### 💡 Recommendations")
                if insights['recommendations']:
                    for rec in insights['recommendations']:
                        st.markdown(f"- {rec}")
                else:
                    st.info("No specific recommendations at this time")

                st.markdown("### ⚠️ Risk Analysis")
                st.markdown(insights['risk_analysis'])

                if insights.get('using_ai'):
                    st.caption("🤖 Powered by GPT-4")
                else:
                    st.caption("📊 Rule-based analysis")

    st.markdown("---")

    # Offer insights
    st.markdown("### 💼 Cohort Offers Insights")
    offers = db.get_all_offers()
    if offers:
        offer_insights = ai_insights.generate_offer_insights(offers)
        st.info(offer_insights)
    else:
        st.caption("No offers to analyze")

    st.markdown("---")

    # Energy insights
    st.markdown("### 🌿 Energy Tracking Insights")
    entries = db.get_energy_entries(days=30)
    if entries:
        energy_insights = ai_insights.generate_energy_insights(entries)
        st.info(energy_insights)
    else:
        st.caption("Track at least 7 days of energy to generate insights")


def data_management(db: Database):
    """Comprehensive data management and CRUD operations"""

    st.subheader("🗂️ Data Management")

    st.warning("⚠️ **Caution:** Data operations cannot be undone. Always export before deleting!")

    # Bulk operations
    st.markdown("### 🗑️ Bulk Delete Operations")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Delete All Ideas", type="secondary"):
            if st.checkbox("Confirm: Delete ALL Ideas", key="confirm_delete_ideas"):
                db.delete_all_ideas()
                st.success("All ideas deleted")
                st.rerun()

    with col2:
        if st.button("Delete All Offers", type="secondary"):
            if st.checkbox("Confirm: Delete ALL Offers", key="confirm_delete_offers"):
                db.delete_all_offers()
                st.success("All offers deleted")
                st.rerun()

    with col3:
        if st.button("Delete All Energy Data", type="secondary"):
            if st.checkbox("Confirm: Delete ALL Energy Data", key="confirm_delete_energy"):
                db.delete_all_energy_entries()
                st.success("All energy data deleted")
                st.rerun()

    st.markdown("---")

    # Individual record management
    st.markdown("### 🔍 Individual Record Management")

    record_type = st.selectbox("Select Data Type", ["Ideas", "Milestones", "Offers", "Energy Entries"])

    if record_type == "Ideas":
        manage_ideas(db)
    elif record_type == "Milestones":
        manage_milestones(db)
    elif record_type == "Offers":
        manage_offers(db)
    elif record_type == "Energy Entries":
        manage_energy(db)


def manage_ideas(db: Database):
    """Manage individual ideas"""
    ideas = db.get_all_ideas()

    if not ideas:
        st.info("No ideas to manage")
        return

    st.markdown(f"**Total Ideas:** {len(ideas)}")

    for idea in ideas:
        with st.expander(f"{idea['name']} ({idea['stage']})"):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"**Owner:** {idea['owner']}")
                st.write(f"**Confidence:** {idea['confidence_score']}%")
                st.write(f"**Description:** {idea.get('description', 'N/A')}")
                st.write(f"**Next Steps:** {idea.get('next_steps', 'N/A')}")
                st.write(f"**Risk Flags:** {idea.get('risk_flags', 'None')}")

            with col2:
                if st.button("🗑️ Delete", key=f"del_idea_{idea['id']}"):
                    db.delete_idea(idea['id'])
                    st.success(f"Deleted: {idea['name']}")
                    st.rerun()


def manage_milestones(db: Database):
    """Manage milestones"""
    ideas = db.get_all_ideas()

    if not ideas:
        st.info("No ideas with milestones")
        return

    selected_idea = st.selectbox("Select Idea", [i['name'] for i in ideas])
    idea_id = next(i['id'] for i in ideas if i['name'] == selected_idea)

    milestones = db.get_milestones_by_idea(idea_id)

    if milestones:
        for m in milestones:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"{m['milestone_name']} - {m['status']}")
            with col2:
                st.write(f"Weight: {m['weight']}")
            with col3:
                if st.button("🗑️", key=f"del_milestone_{m['id']}"):
                    db.delete_milestone(m['id'])
                    st.rerun()
    else:
        st.info("No milestones for this idea")


def manage_offers(db: Database):
    """Manage offers"""
    offers = db.get_all_offers()

    if not offers:
        st.info("No offers to manage")
        return

    for offer in offers:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{offer['offer_name']}** - AI Score: {offer['ai_score']}, Go/No-Go: {offer['go_no_go']}")
        with col2:
            if st.button("🗑️", key=f"del_offer_{offer['id']}"):
                db.delete_offer(offer['id'])
                st.rerun()


def manage_energy(db: Database):
    """Manage energy entries"""
    entries = db.get_energy_entries(days=100)

    if not entries:
        st.info("No energy entries to manage")
        return

    st.write(f"**Total Entries:** {len(entries)}")

    for entry in entries[:20]:  # Show latest 20
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"{entry['date']}: Score {entry['energy_score']}/10")
        with col2:
            st.write("🛌 Recovery" if entry['recovery_block'] else "📅 Regular")
        with col3:
            if st.button("🗑️", key=f"del_energy_{entry['id']}"):
                db.delete_energy_entry(entry['id'])
                st.rerun()


def ui_customization(db: Database):
    """UI customization settings"""

    st.subheader("🎨 UI Customization")

    st.info("Customize the look and feel of your dashboard")

    # Theme preferences
    st.markdown("### 🎨 Theme Settings")

    current_theme = db.get_setting('theme', 'dark')

    theme_choice = st.radio(
        "Select Theme",
        ["Dark (Recommended)", "Light"],
        index=0 if current_theme == "dark" else 1,
        horizontal=True,
        help="Choose your preferred theme. Dark theme is optimized for long sessions."
    )

    theme_value = "dark" if "Dark" in theme_choice else "light"

    if theme_value != current_theme:
        db.set_setting('theme', theme_value)
        st.success(f"✅ Theme updated to: {theme_value}")
        st.info("💡 Refresh the page (F5) to see the changes")

    st.markdown("---")

    # Dashboard preferences
    st.markdown("### 📊 Dashboard Preferences")

    # Get current settings with defaults
    current_show_confidence = db.get_setting('show_confidence', 'True') == 'True'
    current_show_owner = db.get_setting('show_owner', 'True') == 'True'
    current_show_risk = db.get_setting('show_risk_badges', 'True') == 'True'

    show_confidence = st.checkbox(
        "Show confidence scores on Kanban cards",
        value=current_show_confidence,
        key="pref_confidence"
    )
    show_owner = st.checkbox(
        "Show owner on Kanban cards",
        value=current_show_owner,
        key="pref_owner"
    )
    show_risk_badges = st.checkbox(
        "Show risk badges",
        value=current_show_risk,
        key="pref_risk"
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("💾 Save Preferences", use_container_width=True):
            db.set_setting('show_confidence', str(show_confidence))
            db.set_setting('show_owner', str(show_owner))
            db.set_setting('show_risk_badges', str(show_risk_badges))
            st.success("✅ Preferences saved successfully!")
            st.info("💡 Refresh to see changes")

    with col2:
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            db.set_setting('show_confidence', 'True')
            db.set_setting('show_owner', 'True')
            db.set_setting('show_risk_badges', 'True')
            st.success("✅ Reset to default settings!")
            st.rerun()

    st.markdown("---")

    # Color customization (preview only - would need CSS injection to apply)
    st.markdown("### 🌈 Color Customization (Preview)")

    col1, col2 = st.columns(2)
    with col1:
        primary_color = st.color_picker("Primary Color", "#667eea", help="Main accent color for buttons and highlights")
    with col2:
        secondary_color = st.color_picker("Secondary Color", "#764ba2", help="Secondary gradient color")

    st.caption("💡 Note: Color customization is coming in a future update. Current values are for preview only.")


def system_settings(db: Database):
    """System settings and configuration"""

    st.subheader("⚙️ System Settings")

    # API Configuration
    st.markdown("### 🔑 API Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**OpenAI API**")
        if ai_insights.use_openai:
            st.success("✅ Connected")
        else:
            st.warning("❌ Not configured")
            st.caption("Add OPENAI_API_KEY to .env file")

    with col2:
        st.markdown("**Turso Database**")
        if db.use_turso:
            st.success("☁️ Using Turso Cloud")
        else:
            st.info("💻 Using Local SQLite")

    st.markdown("---")

    # Database info
    st.markdown("### 💾 Database Information")

    stats = db.get_database_stats()

    total_records = sum([
        stats['total_ideas'],
        stats['total_milestones'],
        stats['total_offers'],
        stats['total_energy_entries']
    ])

    st.write(f"**Total Records:** {total_records}")

    st.markdown("---")

    # All settings
    st.markdown("### 📋 All Settings")

    settings = db.get_all_settings()

    if settings:
        settings_df = pd.DataFrame([
            {'Key': k, 'Value': v}
            for k, v in settings.items()
        ])
        st.dataframe(settings_df, use_container_width=True, hide_index=True)
    else:
        st.info("No custom settings configured")

    st.markdown("---")

    # Export settings
    st.markdown("### 📤 Export Configuration")

    if st.button("📋 Copy Settings as JSON"):
        settings_json = json.dumps(settings, indent=2)
        st.code(settings_json, language='json')
        st.success("Copy the JSON above to backup your settings")
