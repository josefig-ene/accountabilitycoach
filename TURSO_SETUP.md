# Turso Setup Guide - Permanent Cloud Storage

This guide will help you set up Turso for permanent cloud storage of your CEO Dashboard data.

## Why Turso?

- ✅ **SQLite in the cloud** - Same database, but persistent
- ✅ **Free tier**: 500 databases, 9GB storage, 1 billion rows/month
- ✅ **Fast**: Edge-distributed globally
- ✅ **No code changes needed** - Works with existing SQLite code
- ✅ **Perfect for Streamlit Cloud** - Data persists across deployments

---

## Step 1: Install Turso CLI

### Windows (PowerShell - Run as Administrator):
```powershell
iwr -useb https://get.tur.so/install.ps1 | iex
```

### macOS/Linux:
```bash
curl -sSfL https://get.tur.so/install.sh | bash
```

### Manual Download:
Visit https://docs.turso.tech/cli/installation

---

## Step 2: Create Your Turso Database

```bash
# Sign up / Login to Turso
turso auth signup
# (This will open your browser to authenticate)

# Create your database
turso db create ceo-dashboard

# Get your database URL
turso db show ceo-dashboard --url

# Create an authentication token
turso db tokens create ceo-dashboard
```

**Save these two values!** You'll need them next.

---

## Step 3: Configure Local Development

### Option A: Using .env file (Recommended)

1. Copy the example file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your Turso credentials:
```bash
TURSO_DATABASE_URL=libsql://ceo-dashboard-yourname.turso.io
TURSO_AUTH_TOKEN=eyJhbGc...your-token-here
```

3. Install python-dotenv:
```bash
pip install python-dotenv
```

4. Update `app.py` to load environment variables (add at the top):
```python
from dotenv import load_dotenv
load_dotenv()  # Load .env file
```

### Option B: Set Environment Variables Directly

**Windows (Command Prompt):**
```cmd
set TURSO_DATABASE_URL=libsql://ceo-dashboard-yourname.turso.io
set TURSO_AUTH_TOKEN=eyJhbGc...your-token-here
```

**Windows (PowerShell):**
```powershell
$env:TURSO_DATABASE_URL="libsql://ceo-dashboard-yourname.turso.io"
$env:TURSO_AUTH_TOKEN="eyJhbGc...your-token-here"
```

**macOS/Linux:**
```bash
export TURSO_DATABASE_URL="libsql://ceo-dashboard-yourname.turso.io"
export TURSO_AUTH_TOKEN="eyJhbGc...your-token-here"
```

---

## Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs `libsql-experimental` which connects to Turso.

---

## Step 5: Test Your Setup

Run the app:
```bash
streamlit run app.py
```

You should see:
```
✅ Using Turso cloud database
```

If you see this instead, environment variables aren't set:
```
✅ Using local SQLite database: ceo_dashboard.db
```

---

## Step 6: Seed Demo Data (Optional)

```bash
python seed_demo_data.py
```

This will populate your Turso database with sample data.

---

## Step 7: Deploy to Streamlit Cloud

### 1. Push your code to GitHub:
```bash
git add .
git commit -m "Add Turso cloud database support"
git push origin claude/ceo-dashboard-app-xbFKb
```

### 2. Go to Streamlit Cloud:
- Visit: https://share.streamlit.io
- Click "New app"
- Select your repository: `josefig-ene/three_engine_dashboard`
- Select branch: `claude/ceo-dashboard-app-xbFKb`
- Main file: `app.py`

### 3. Add Secrets:
Before deploying, click **"Advanced settings"** → **"Secrets"**

Add this:
```toml
TURSO_DATABASE_URL = "libsql://ceo-dashboard-yourname.turso.io"
TURSO_AUTH_TOKEN = "eyJhbGc...your-token-here"
```

### 4. Click "Deploy"!

Your app will now use Turso for permanent storage! 🎉

---

## Verifying It Works

### Check your data in Turso:

```bash
# Open Turso shell
turso db shell ceo-dashboard

# Run SQL queries
SELECT * FROM ideas;
SELECT * FROM offers;
SELECT * FROM energy_tracking;

# Exit
.quit
```

### View database in Turso Dashboard:

Go to: https://turso.tech/app
- Click on your database
- Browse tables and data visually

---

## Switching Between Local and Cloud

The app automatically detects which to use:

**Use Turso (cloud):**
- Set `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` environment variables

**Use Local SQLite:**
- Don't set those environment variables (or leave them empty)

This means you can:
- Develop locally with SQLite
- Deploy to production with Turso
- Same code, zero changes needed!

---

## Troubleshooting

### "Module libsql_experimental not found"
```bash
pip install libsql-experimental
```

### "Unable to connect to Turso"
- Check your `TURSO_DATABASE_URL` is correct (should start with `libsql://`)
- Verify your `TURSO_AUTH_TOKEN` hasn't expired
- Create a new token: `turso db tokens create ceo-dashboard`

### "Database locked" errors
- Turso handles concurrent connections better than SQLite
- Should not see this error with Turso

### Environment variables not loading
- Make sure `.env` file exists (copy from `.env.example`)
- Install python-dotenv: `pip install python-dotenv`
- Add `load_dotenv()` at the top of `app.py`

### Want to reset your database?
```bash
# Delete and recreate
turso db destroy ceo-dashboard
turso db create ceo-dashboard

# Get new credentials
turso db show ceo-dashboard --url
turso db tokens create ceo-dashboard

# Update your .env file with new values
```

---

## Cost Information

**Free Tier Includes:**
- 500 databases
- 9 GB total storage
- 1 billion row reads/month
- 25 million row writes/month
- Unlimited number of databases

For a personal CEO dashboard, you'll likely **never exceed the free tier**!

**Paid Plans** (if you scale massively):
- Starter: $29/month (more reads/writes)
- Pro: Custom pricing

---

## Migrating Existing SQLite Data to Turso

If you have local SQLite data you want to move to Turso:

```bash
# Dump your local database
sqlite3 ceo_dashboard.db .dump > dump.sql

# Load into Turso
turso db shell ceo-dashboard < dump.sql
```

---

## Next Steps

✅ Your CEO Dashboard now has **permanent cloud storage**!

- Add new ideas, offers, and energy entries
- Deploy to Streamlit Cloud
- Access from anywhere
- Data persists forever (no more resets!)

**Questions?** Check out:
- Turso docs: https://docs.turso.tech
- Turso Discord: https://discord.gg/turso

---

**Built with ❤️ using Turso + Streamlit**
