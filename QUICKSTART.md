# CEO Dashboard - Quick Start Guide

Get your CEO Dashboard running in 3 simple steps!

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: (Optional) Seed Demo Data
```bash
python seed_demo_data.py
```
This creates sample data so you can explore the dashboard immediately.

### Step 3: Launch the App
```bash
streamlit run app.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`

---

## 📊 What You'll See

### 🚀 Studio Cockpit (Venture Studio Engine)
Track your startup ideas through stages:
- **Seed** → **Validation** → **MVP** → **Pilot** → **Scale** → **Exit**
- Automatic confidence scoring based on milestone completion
- Visual Kanban board and detailed table view

**Try it:**
1. Click "Add New Idea" tab
2. Enter an idea name, stage, and owner
3. Go to "Manage Milestones" to add weighted milestones
4. Watch the confidence score calculate automatically!

### 💼 Cohort Lab (Cohort Business Engine)
Evaluate and track your cohort offers:
- AI Score, Pricing Fit, Audience Fit
- Go/No-Go recommendations
- Visual analytics showing high performers

**Try it:**
1. Click "Add New Offer" tab
2. Enter offer details and scores
3. See high-scoring offers (≥70) highlighted for launch

### 🌿 Sustainability Dashboard (Personal Sustainability Engine)
Monitor your personal energy and recovery:
- Daily energy scores (1-10)
- 30-day trend visualization
- Recovery block tracking
- Impact analysis

**Try it:**
1. Click "Add Daily Entry" tab
2. Log today's energy score
3. Check recovery block if you took rest time
4. View your energy trends over time

---

## 💡 Pro Tips

1. **Milestone Weighting**: Assign higher weights (4-5) to critical milestones that significantly impact confidence

2. **Daily Tracking**: Log energy scores consistently for meaningful patterns

3. **Recovery Days**: Mark recovery blocks to see how rest impacts your energy

4. **Offer Scoring**: Use consistent criteria when scoring offers for fair comparison

5. **Stage Progression**: Update idea stages as you hit key milestones

---

## 🗂️ File Structure

```
.
├── app.py                    # Main Streamlit app
├── database.py               # Database operations
├── requirements.txt          # Python dependencies
├── seed_demo_data.py        # Demo data seeder
├── test_database.py         # Database tests
├── README_CEO_DASHBOARD.md  # Full documentation
├── QUICKSTART.md            # This file
└── ceo_dashboard.db         # SQLite database (auto-created)
```

---

## 🆘 Troubleshooting

**"Port 8501 already in use"**
```bash
streamlit run app.py --server.port 8502
```

**"Module not found"**
```bash
pip install -r requirements.txt
```

**Want fresh data?**
```bash
rm ceo_dashboard.db
python seed_demo_data.py
streamlit run app.py
```

---

## 🎯 Next Steps

1. **Replace demo data** with your real ideas, offers, and energy scores
2. **Track daily** - Make it a habit to log energy and update milestones
3. **Review weekly** - Check your dashboard every week to spot trends
4. **Iterate** - Adjust milestone weights and stage progressions as you learn

---

## 📚 Need More Help?

See `README_CEO_DASHBOARD.md` for:
- Detailed feature documentation
- Database schema
- Advanced usage tips
- Customization options

---

**Built with ❤️ using Python, Streamlit, and SQLite**

Now go track your three engines of life! 🚀💼🌿
