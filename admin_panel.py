"""
Admin Panel for CEO Dashboard
Comprehensive CRUD operations, settings, and AI insights
"""

import streamlit as st
import pandas as pd
from database import Database
from ai_insights import ai_insights
import json


def admin_panel(db: Database):
    """Admin Panel with CRUD and settings"""

    st.markdown("<h1>⚙️ Admin Panel</h1>", unsafe_allow_html=True)
    st.markdown('<p class="subtitle">System Administration & Settings</p>', unsafe_allow_html=True)

    # Tabs for different admin functions
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard Stats",
        "🤖 AI Insights",
        "🗂️ Data Management",
        "🎨 UI Customization",
        "⚙️ Settings"
    ])

    with tab1:
        stats_dashboard(db)

    with tab2:
        ai_insights_panel(db)

    with tab3:
        data_management(db)

    with tab4:
        ui_customization(db)

    with tab5:
        system_settings(db)


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
        "Theme",
        ["dark", "light"],
        index=0 if current_theme == "dark" else 1,
        horizontal=True
    )

    if theme_choice != current_theme:
        db.set_setting('theme', theme_choice)
        st.success(f"Theme set to: {theme_choice}")
        st.info("Refresh the page to apply changes")

    st.markdown("---")

    # Dashboard preferences
    st.markdown("### 📊 Dashboard Preferences")

    show_confidence = st.checkbox("Show confidence scores on Kanban cards", value=True)
    show_owner = st.checkbox("Show owner on Kanban cards", value=True)
    show_risk_badges = st.checkbox("Show risk badges", value=True)

    if st.button("Save Preferences"):
        db.set_setting('show_confidence', str(show_confidence))
        db.set_setting('show_owner', str(show_owner))
        db.set_setting('show_risk_badges', str(show_risk_badges))
        st.success("Preferences saved!")

    st.markdown("---")

    # Color customization (preview only - would need CSS injection to apply)
    st.markdown("### 🌈 Color Customization (Preview)")

    primary_color = st.color_picker("Primary Color", "#667eea")
    secondary_color = st.color_picker("Secondary Color", "#764ba2")

    st.caption("Note: Color customization coming in future update")


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
