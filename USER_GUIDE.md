# CEO Dashboard - User Guide

## 📖 Table of Contents
- [Overview](#overview)
- [Getting Started](#getting-started)
- [The Three Engines](#the-three-engines)
- [Features & Navigation](#features--navigation)
- [Admin Panel](#admin-panel)
- [Data Management](#data-management)
- [Tips & Best Practices](#tips--best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

The CEO Dashboard is a comprehensive tool for tracking your life's three core engines:
- **🚀 Venture Studio (Wealth)** - Build and scale business ideas
- **💼 Cohort Lab (Cashflow)** - Manage cohort-based offers
- **🌿 Sustainability (Longevity)** - Track personal energy and well-being

---

## Getting Started

### Installation & Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app:**
   ```bash
   streamlit run app.py
   ```

3. **Access the dashboard:**
   - Open your browser to `http://localhost:8501`

### First Time Setup

1. **Seed demo data** (optional):
   ```bash
   python seed_demo_data.py
   ```
   This creates sample data to help you understand the system.

2. **Navigate** using the sidebar menu to explore the three engines.

3. **Customize** your settings in the Admin Panel.

---

## The Three Engines

### 🚀 Studio Cockpit (Venture Studio - Wealth)

**Purpose:** Track business ideas from concept to exit.

**Key Features:**
- **Stage Pipeline:** Visual Kanban board showing ideas across 6 stages
  - 🌱 Seed - Initial concept
  - 🔍 Validation - Testing the idea
  - ⚙️ MVP - Building minimum viable product
  - 🧪 Pilot - Testing with early users
  - 📈 Scale - Growing the business
  - 🎉 Exit - Successful completion/sale

- **Confidence Scoring:** Automatic calculation based on milestones
  - 🟢 70%+ = High confidence
  - 🟡 40-69% = Moderate confidence
  - 🔴 <40% = Needs attention

- **Milestones:** Track weighted progress indicators
  - Each milestone has a weight (importance)
  - Complete milestones to increase confidence score

**How to Use:**
1. Go to **"➕ Add New Idea"** tab
2. Enter idea name, description, owner, and stage
3. Add next steps and risk flags
4. Click **"🎯 Manage Milestones"** to add tracked goals
5. View all ideas on the **Stage Pipeline** Kanban board

---

### 💼 Cohort Lab (Cohort Business - Cashflow)

**Purpose:** Manage cohort-based business offers and track performance.

**Key Features:**
- **Offer Dashboard:** Overview of all cohort offers
- **Performance Metrics:**
  - Student Acquisition Score (0-100)
  - Activation Rate (0-100)
  - Retention Score (0-100)
  - Average Score (calculated automatically)

- **Visual Analytics:** Charts showing offer performance comparison

**How to Use:**
1. Navigate to **💼 Cohort Lab** from sidebar
2. Click **"➕ Add New Offer"** tab
3. Enter offer details:
   - Name and description
   - Owner/facilitator
   - Three performance scores (0-100)
4. View all offers in the dashboard
5. Export data as CSV for analysis

---

### 🌿 Sustainability Dashboard (Personal - Longevity)

**Purpose:** Track daily energy levels and identify patterns.

**Key Features:**
- **Energy Tracking:** Monitor 5 key areas daily
  - Sleep Quality (1-10)
  - Physical Energy (1-10)
  - Mental Clarity (1-10)
  - Emotional State (1-10)
  - Stress Level (1-10, lower is better)

- **Visual Analytics:**
  - Line charts showing trends over time
  - Average scores per category
  - Overall energy average

**How to Use:**
1. Navigate to **🌿 Sustainability** from sidebar
2. Click **"➕ Add Daily Entry"** tab
3. Rate each dimension (1-10)
4. Add optional notes about your day
5. View trends in the **Energy Tracking** tab

**Tips:**
- Log daily at the same time for consistency
- Lower stress scores are better (inverted in calculations)
- Use notes to capture what influenced your energy

---

## Features & Navigation

### Sidebar Navigation

**ENGINES Section:**
- Quick access to all three engines
- Visual engine labels (Wealth, Cashflow, Longevity)

**ADMIN Section:**
- Access to Admin Panel
- Settings and customization

### Export Features

Each engine includes CSV export:
1. Click **"📄 Export [Type] CSV"** button
2. Click **"⬇️ Download"** when it appears
3. File downloads with timestamp (e.g., `ideas_20260124.csv`)

### Search & Filter

- **Manage Ideas:** Use dropdown to select and view specific ideas
- **Analytics Tab:** View charts and insights
- **Stage Pipeline:** Scroll horizontally to see all stages

---

## Admin Panel

Access via **"⚙️ Admin Panel"** button in sidebar.

### 📊 Dashboard Stats

- View total counts (ideas, milestones, offers, energy entries)
- See ideas by stage breakdown
- Portfolio health score (based on average confidence)

### 🤖 AI Insights

- Rule-based analysis (always available)
- Optional GPT-4 insights (requires OpenAI API key)
- Portfolio recommendations
- Offer insights
- Energy pattern analysis

**To enable GPT-4:**
1. Create `.env` file in project root
2. Add: `OPENAI_API_KEY=your_key_here`
3. Restart the app

### 📥 Import Data

**Import from Monday.com:**
Upload CSV or Excel exports from Monday.com to quickly populate your dashboard.

**How to Import:**
1. Export your Monday.com board (Menu → Export → CSV/Excel)
2. Go to Admin Panel → Import Data tab
3. Upload the file
4. Review the preview
5. Choose import mode:
   - **Add to existing** - Keeps current data and adds new
   - **Replace all** - Deletes existing ideas and imports fresh
6. Click "Import Data"

**What Gets Imported:**
- Projects → Ideas in Studio Cockpit
- Tasks → Milestones for each idea
- Owners → Assigned to ideas
- Status → Mapped to pipeline stages
- Descriptions → Project details

**Status Mapping:**
- Backlog/Todo → Seed
- Research/Stuck → Validation
- In Progress/Doing → MVP
- Testing → Pilot
- Production → Scale
- Done/Completed → Exit

**Supported Columns:**
- Board, Project (groups items into ideas)
- Item, Name, Task (idea/milestone names)
- Status, Stage (pipeline stage)
- Owner, Person, Assigned To (ownership)
- Description, Notes, Summary (details)
- Due Date, Deadline (milestone dates)

**Tips:**
- Download the sample CSV to see the expected format
- Column names are case-insensitive
- Unknown statuses default to "Seed"
- Always export your current data before replacing

### 🗂️ Data Management

**Bulk Operations:**
- Delete all ideas
- Delete all offers
- Delete all energy data
- ⚠️ **Warning:** Cannot be undone! Export data first.

**Individual Management:**
- Browse and delete specific records
- View detailed information
- Filter by type

### 🎨 UI Customization

**Theme Settings:**
- Dark theme (recommended)
- Light theme (coming soon)

**Dashboard Preferences:**
- Toggle confidence scores on Kanban
- Show/hide owner information
- Display risk badges

**Color Customization:**
- Preview mode (not yet functional)

### ⚙️ Settings

**API Configuration:**
- OpenAI API status
- Database type (Local SQLite or Turso Cloud)

**Database Info:**
- Total record counts
- Storage location

---

## Data Management

### Database

**Local SQLite (Default):**
- Data stored in `ceo_dashboard.db`
- No internet required
- Automatic backups recommended

**Turso Cloud (Optional):**
1. Install Turso CLI
2. Create database
3. Add credentials to `.env`:
   ```
   TURSO_DATABASE_URL=your_url
   TURSO_AUTH_TOKEN=your_token
   ```

### Backup Your Data

**Recommended backup strategy:**
1. Regular CSV exports from each engine
2. Copy `ceo_dashboard.db` file periodically
3. Store in cloud storage (Dropbox, Google Drive, etc.)

### Data Privacy

- All data stored locally by default
- No external tracking or analytics
- API keys stored in `.env` (never committed to git)

---

## Tips & Best Practices

### Venture Studio
- ✅ Update milestones regularly to keep confidence scores accurate
- ✅ Use risk flags to highlight blockers
- ✅ Add specific next steps for each idea
- ✅ Move ideas through stages deliberately
- ❌ Don't skip validation stage
- ❌ Don't create too many ideas without focus

### Cohort Lab
- ✅ Track actual metrics from your cohorts
- ✅ Update scores after each cohort cycle
- ✅ Use descriptions to document what worked
- ✅ Compare offers to identify best performers
- ❌ Don't inflate scores - be honest
- ❌ Don't neglect retention metrics

### Sustainability
- ✅ Log daily at the same time (morning or evening)
- ✅ Be consistent with your ratings
- ✅ Use notes to identify patterns
- ✅ Review weekly trends
- ❌ Don't skip days (breaks pattern analysis)
- ❌ Don't over-think ratings (first instinct is best)

### General
- ✅ Export data regularly as backup
- ✅ Use the admin panel to monitor overall health
- ✅ Review analytics weekly
- ✅ Set aside time for updates (15-30 min daily)

---

## Troubleshooting

### App Won't Start

**Problem:** `ModuleNotFoundError`
- **Solution:** Run `pip install -r requirements.txt`

**Problem:** Port already in use
- **Solution:** Stop other Streamlit instances or use: `streamlit run app.py --server.port 8502`

### Data Issues

**Problem:** No data showing
- **Solution:** Run `python seed_demo_data.py` to create sample data

**Problem:** Database locked
- **Solution:** Close all app instances and restart

**Problem:** Lost data
- **Solution:** Restore from CSV exports or backup `ceo_dashboard.db` file

### Display Issues

**Problem:** Text not readable
- **Solution:** Check Admin Panel > UI Customization for theme settings

**Problem:** Kanban board not showing
- **Solution:** Refresh browser (Ctrl+F5 or Cmd+Shift+R)

**Problem:** Charts not displaying
- **Solution:** Ensure plotly is installed: `pip install plotly`

### Performance

**Problem:** App running slow
- **Solution:**
  - Archive old data
  - Use bulk delete for unused records
  - Check database size

---

## Keyboard Shortcuts

- **Ctrl+R / Cmd+R** - Refresh page
- **Ctrl+F5 / Cmd+Shift+R** - Hard refresh (clear cache)
- **Esc** - Close modals/popups

---

## Support & Resources

- **GitHub Issues:** Report bugs or request features
- **Documentation:** This user guide
- **Sample Data:** Run `seed_demo_data.py` to explore features

---

## Version Information

**Current Version:** 1.0
**Last Updated:** January 2026

---

## Quick Reference Card

| Task | Steps |
|------|-------|
| Add new idea | Studio Cockpit > Add New Idea tab |
| Track milestone | Manage Milestones tab > Add milestone |
| Add cohort offer | Cohort Lab > Add New Offer tab |
| Log daily energy | Sustainability > Add Daily Entry tab |
| Export data | Click 📄 Export button > Download |
| Delete data | Admin Panel > Data Management |
| Change theme | Admin Panel > UI Customization |
| View insights | Admin Panel > AI Insights |
| Backup data | Export all CSVs + copy .db file |

---

**Built with Streamlit & Turso** | Made with ❤️ for focused CEOs
