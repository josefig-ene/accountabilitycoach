# CEO Dashboard - Three Engines of Life

A comprehensive dashboard application to track three distinct engines of your life:

1. **🚀 Venture Studio Engine (Wealth)** - Track ideas, stages, and milestone-based confidence scoring
2. **💼 Cohort Business Engine (Cashflow)** - Manage offers with AI scoring and launch readiness
3. **🌿 Personal Sustainability Engine (Longevity)** - Monitor daily energy levels and recovery blocks

## Features

### Studio Cockpit (Venture Studio Engine)
- **Kanban Board**: Visual pipeline showing ideas across 6 stages (Seed → Validation → MVP → Pilot → Scale → Exit)
- **Confidence Scoring**: Automatically calculated based on weighted milestone completion
- **Milestone Tracking**: Link milestones to ideas with categories (tech, market, business, ops)
- **Portfolio Metrics**: Track total ideas, average confidence, active projects, and exits

### Cohort Lab (Cohort Business Engine)
- **Offer Management**: Track offers with AI scores, pricing fit, and audience fit
- **Launch Readiness**: Highlight high-scoring offers ready for launch
- **Go/No-Go Decisions**: Clear recommendation system for each offer
- **Visual Analytics**: Charts showing AI scores and fit analysis

### Sustainability Dashboard (Personal Sustainability Engine)
- **Energy Tracking**: Daily energy score tracking (1-10 scale)
- **30-Day Trends**: Line chart showing energy patterns over time
- **Recovery Blocks**: Track rest days and compare energy levels
- **Analytics**: Distribution charts and recovery day comparisons

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the application:**
```bash
streamlit run app.py
```

3. **Access the dashboard:**
The app will automatically open in your browser at `http://localhost:8501`

## Database

The application uses SQLite for data persistence. The database file (`ceo_dashboard.db`) will be automatically created on first run.

### Database Schema

**Ideas Table:**
- id (UUID)
- name (Text)
- description (Text)
- stage (Enum: seed, validation, mvp, pilot, scale, exit)
- owner (Text)
- confidence_score (Integer 0-100)
- created_at, updated_at (Timestamps)

**Milestones Table:**
- id (UUID)
- idea_id (Foreign Key)
- milestone_name (Text)
- category (Enum: tech, market, business, ops)
- status (Enum: not_started, in_progress, done)
- weight (Integer 1-5)
- notes (Text)

**Offers Table:**
- id (UUID)
- offer_name (Text)
- ai_score (Integer 0-100)
- pricing_fit (Integer 0-10)
- audience_fit (Integer 0-10)
- go_no_go (Enum: go, no-go, pending)
- notes (Text)
- created_at (Timestamp)

**Energy Tracking Table:**
- id (UUID)
- date (Date, unique)
- energy_score (Integer 1-10)
- recovery_block (Boolean)
- notes (Text)
- created_at (Timestamp)

## Usage Guide

### Adding a New Idea
1. Navigate to Studio Cockpit
2. Go to "Add New Idea" tab
3. Fill in idea name, stage, owner, and description
4. Click "Add Idea"

### Managing Milestones
1. Navigate to Studio Cockpit → "Manage Milestones" tab
2. Select an idea from the dropdown
3. Add milestones with categories and weights
4. Update milestone status to automatically recalculate confidence scores

### Tracking Offers
1. Navigate to Cohort Lab
2. Go to "Add New Offer" tab
3. Enter offer details and scores
4. Set go/no-go recommendation
5. High-scoring offers (≥70) appear in the launch-ready section

### Logging Daily Energy
1. Navigate to Sustainability Dashboard
2. Go to "Add Daily Entry" tab
3. Select date and energy score (1-10)
4. Check "Recovery Block" if applicable
5. Add notes about sleep, activities, mood, etc.

## Features Highlights

### Automatic Confidence Scoring
Confidence scores are automatically calculated based on:
- Milestone completion status (done = contributes to score)
- Milestone weights (1-5 scale)
- Formula: (Sum of completed milestone weights / Total weights) × 100

### Visual Analytics
- Kanban board with color-coded confidence indicators
- Interactive charts using Plotly
- 30-day energy trend visualization
- Offer performance scatter plots

### Modern UI
- Clean, professional design
- Responsive layout
- Color-coded metrics and indicators
- Intuitive navigation

## Technology Stack

- **Frontend**: Streamlit
- **Database**: SQLite3
- **Visualization**: Plotly
- **Data Processing**: Pandas
- **Language**: Python 3.8+

## File Structure

```
.
├── app.py                 # Main Streamlit application
├── database.py           # Database operations and schema
├── requirements.txt      # Python dependencies
├── README_CEO_DASHBOARD.md  # This file
└── ceo_dashboard.db      # SQLite database (auto-generated)
```

## Tips

1. **Milestone Weighting**: Assign higher weights (4-5) to critical milestones
2. **Regular Updates**: Update milestone status regularly for accurate confidence scores
3. **Energy Tracking**: Log energy daily for meaningful trends
4. **Recovery Blocks**: Mark rest days to analyze recovery impact
5. **Offer Scoring**: Use consistent scoring criteria across all offers

## Troubleshooting

**Database locked error:**
- Close other connections to the database
- Ensure only one instance of the app is running

**Charts not displaying:**
- Check that plotly is properly installed
- Clear browser cache and reload

**Port already in use:**
```bash
streamlit run app.py --server.port 8502
```

## Future Enhancements

Potential features for expansion:
- Export data to CSV/Excel
- Email notifications for milestones
- Integration with Airtable/Google Sheets
- AI-powered insights and recommendations
- Multi-user support with authentication
- Custom reporting and analytics

## Support

For issues or questions, refer to:
- Streamlit documentation: https://docs.streamlit.io
- SQLite documentation: https://www.sqlite.org/docs.html
- Plotly documentation: https://plotly.com/python/

---

**Built with Python, Streamlit, and SQLite**
