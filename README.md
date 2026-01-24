# 🎯 CEO Dashboard

A comprehensive dashboard for tracking your life's three core engines: Venture Studio (Wealth), Cohort Business (Cashflow), and Personal Sustainability (Longevity).

![Version](https://img.shields.io/badge/version-1.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

### 🚀 Studio Cockpit (Venture Studio - Wealth)
- Visual Kanban board tracking ideas through 6 stages
- Weighted milestone tracking with automatic confidence scoring
- Risk flags and next steps management
- CSV export functionality

### 💼 Cohort Lab (Cohort Business - Cashflow)
- Cohort offer management and performance tracking
- Three key metrics: Acquisition, Activation, Retention
- Visual analytics and performance comparison
- Export capabilities for analysis

### 🌿 Sustainability Dashboard (Personal - Longevity)
- Daily energy tracking across 5 dimensions
- Trend visualization and pattern identification
- Notes for contextual insights
- Long-term wellness monitoring

### ⚙️ Admin Panel
- Comprehensive database statistics
- AI-powered insights (rule-based + optional GPT-4)
- Bulk data management operations
- UI customization settings

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository** (or download the files)
   ```bash
   cd accountabilitycoach
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Open your browser**
   - Navigate to `http://localhost:8501`

### Optional: Seed Demo Data

To get started with sample data:
```bash
python seed_demo_data.py
```

## 📖 Documentation

**👉 [Read the Complete User Guide](USER_GUIDE.md)**

The user guide includes:
- Detailed feature explanations
- Step-by-step tutorials
- Best practices and tips
- Troubleshooting guide
- Quick reference card

## 🛠️ Configuration

### Local SQLite (Default)
No configuration needed. Data is stored in `ceo_dashboard.db`.

### Turso Cloud Database (Optional)
1. Create a `.env` file in the project root
2. Add your Turso credentials:
   ```env
   TURSO_DATABASE_URL=your_database_url
   TURSO_AUTH_TOKEN=your_auth_token
   ```

### AI Insights with GPT-4 (Optional)
1. Add to your `.env` file:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   ```
2. Restart the app

## 📊 The Three Engines

| Engine | Focus | Metrics |
|--------|-------|---------|
| 🚀 **Studio Cockpit** | Building Wealth | Ideas, Stages, Milestones, Confidence |
| 💼 **Cohort Lab** | Generating Cashflow | Offers, Acquisition, Activation, Retention |
| 🌿 **Sustainability** | Longevity & Energy | Sleep, Physical, Mental, Emotional, Stress |

## 🗂️ Project Structure

```
accountabilitycoach/
├── app.py                  # Main Streamlit application
├── database.py             # Database operations & schema
├── admin_panel.py          # Admin interface
├── ai_insights.py          # AI-powered analytics
├── seed_demo_data.py       # Sample data generator
├── requirements.txt        # Python dependencies
├── USER_GUIDE.md          # Comprehensive user guide
├── README.md              # This file
├── .env.example           # Environment variables template
└── ceo_dashboard.db       # SQLite database (created on first run)
```

## 🎨 Screenshots

### Studio Cockpit - Kanban Board
Visual pipeline showing ideas across all stages from Seed to Exit.

### Cohort Lab - Performance Dashboard
Track and compare cohort offer performance metrics.

### Sustainability - Energy Tracking
Monitor daily energy levels and identify patterns.

### Admin Panel - Insights & Management
Comprehensive system administration and AI insights.

## 💾 Data Management

### Backup Your Data
- **Export CSVs**: Use the export buttons in each engine
- **Database File**: Copy `ceo_dashboard.db` regularly
- **Recommended**: Weekly exports + daily .db backups

### Privacy
- All data stored locally by default
- No external tracking or analytics
- Optional cloud storage with Turso
- API keys stored securely in `.env` (not in git)

## 🤝 Contributing

This is a personal productivity tool. Feel free to fork and customize for your needs!

## 📝 License

MIT License - feel free to use and modify as needed.

## 🐛 Troubleshooting

### Common Issues

**App won't start:**
```bash
pip install -r requirements.txt
```

**Port already in use:**
```bash
streamlit run app.py --server.port 8502
```

**No data showing:**
```bash
python seed_demo_data.py
```

**For more issues:** See the [Troubleshooting section in the User Guide](USER_GUIDE.md#troubleshooting)

## 🎯 Usage Tips

- ✅ Log data daily for best insights
- ✅ Export data weekly as backup
- ✅ Review analytics every Sunday
- ✅ Use risk flags to highlight blockers
- ✅ Keep milestone weights realistic

## 📞 Support

- **Documentation**: [USER_GUIDE.md](USER_GUIDE.md)
- **Issues**: Check the troubleshooting guide first
- **Questions**: Review the Quick Help in the sidebar

## 🙏 Acknowledgments

Built with:
- [Streamlit](https://streamlit.io/) - Web framework
- [Turso](https://turso.tech/) - Cloud SQLite
- [Plotly](https://plotly.com/) - Interactive charts
- [Pandas](https://pandas.pydata.org/) - Data analysis

---

**Made with ❤️ for focused CEOs managing Wealth, Cashflow, and Longevity**

Version 1.0 | Last updated: January 2026
