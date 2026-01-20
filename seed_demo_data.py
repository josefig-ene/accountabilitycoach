"""
Seed demo data for CEO Dashboard
Creates sample data across all three engines
"""

from database import Database
from datetime import date, timedelta

def seed_demo_data():
    """Create demo data for all engines"""
    print("🌱 Seeding demo data for CEO Dashboard...")
    print("=" * 50)

    db = Database()

    # ===== VENTURE STUDIO ENGINE =====
    print("\n🚀 Seeding Venture Studio Engine...")

    # Idea 1: AI-Powered CRM
    idea1_id = db.add_idea(
        name="AI-Powered CRM",
        description="Customer relationship management system with AI-driven insights and predictive analytics",
        stage="mvp",
        owner="Sarah Chen"
    )
    db.add_milestone(idea1_id, "10 customer interviews", "market", "done", 3)
    db.add_milestone(idea1_id, "Build MVP prototype", "tech", "done", 5)
    db.add_milestone(idea1_id, "Secure pilot customers", "business", "in_progress", 4)
    print("✅ Added: AI-Powered CRM")

    # Idea 2: Blockchain Supply Chain
    idea2_id = db.add_idea(
        name="Blockchain Supply Chain",
        description="Transparent supply chain tracking using blockchain technology",
        stage="validation",
        owner="Marcus Johnson"
    )
    db.add_milestone(idea2_id, "Market research", "market", "done", 2)
    db.add_milestone(idea2_id, "Technical feasibility study", "tech", "done", 3)
    db.add_milestone(idea2_id, "Identify partners", "business", "not_started", 3)
    print("✅ Added: Blockchain Supply Chain")

    # Idea 3: EdTech Platform
    idea3_id = db.add_idea(
        name="EdTech Personalized Learning",
        description="Adaptive learning platform for K-12 education",
        stage="pilot",
        owner="Lisa Rodriguez"
    )
    db.add_milestone(idea3_id, "Core platform development", "tech", "done", 5)
    db.add_milestone(idea3_id, "Pilot with 3 schools", "business", "in_progress", 4)
    db.add_milestone(idea3_id, "Measure learning outcomes", "market", "in_progress", 3)
    print("✅ Added: EdTech Personalized Learning")

    # Idea 4: HealthTech Wearable
    idea4_id = db.add_idea(
        name="HealthTech Wearable",
        description="Continuous health monitoring device with AI diagnostics",
        stage="seed",
        owner="Dr. James Park"
    )
    db.add_milestone(idea4_id, "Product concept validation", "market", "not_started", 2)
    db.add_milestone(idea4_id, "Hardware prototype", "tech", "not_started", 5)
    print("✅ Added: HealthTech Wearable")

    # Idea 5: SaaS Analytics
    idea5_id = db.add_idea(
        name="SaaS Analytics Dashboard",
        description="Real-time business intelligence for SaaS companies",
        stage="scale",
        owner="Sarah Chen"
    )
    db.add_milestone(idea5_id, "MVP launched", "tech", "done", 5)
    db.add_milestone(idea5_id, "Acquired 50+ customers", "business", "done", 5)
    db.add_milestone(idea5_id, "Build sales team", "ops", "in_progress", 3)
    print("✅ Added: SaaS Analytics Dashboard")

    # ===== COHORT BUSINESS ENGINE =====
    print("\n💼 Seeding Cohort Business Engine...")

    db.add_offer(
        "AI Mastery Cohort",
        ai_score=88,
        pricing_fit=9,
        audience_fit=8,
        go_no_go="go",
        notes="Strong demand from tech professionals. Validated pricing at $2,997."
    )
    print("✅ Added: AI Mastery Cohort")

    db.add_offer(
        "Leadership Accelerator",
        ai_score=75,
        pricing_fit=7,
        audience_fit=9,
        go_no_go="go",
        notes="Target: Mid-level managers. Good audience fit, competitive pricing."
    )
    print("✅ Added: Leadership Accelerator")

    db.add_offer(
        "Startup Founders Bootcamp",
        ai_score=92,
        pricing_fit=8,
        audience_fit=10,
        go_no_go="go",
        notes="Excellent fit. Strong network effects. Premium positioning validated."
    )
    print("✅ Added: Startup Founders Bootcamp")

    db.add_offer(
        "Sales Mastery Program",
        ai_score=65,
        pricing_fit=6,
        audience_fit=7,
        go_no_go="pending",
        notes="Moderate scores. Need to refine value proposition. Market test in progress."
    )
    print("✅ Added: Sales Mastery Program")

    db.add_offer(
        "Digital Marketing Course",
        ai_score=45,
        pricing_fit=5,
        audience_fit=4,
        go_no_go="no-go",
        notes="Saturated market. Low differentiation. Pricing pressure too high."
    )
    print("✅ Added: Digital Marketing Course")

    # ===== PERSONAL SUSTAINABILITY ENGINE =====
    print("\n🌿 Seeding Personal Sustainability Engine...")

    # Last 30 days of energy tracking
    today = date.today()
    energy_scores = [7, 8, 6, 9, 8, 7, 5, 8, 9, 7, 6, 8, 9, 8, 7, 4, 9, 8, 7, 8, 6, 9, 8, 7, 8, 9, 6, 8, 7, 8]
    recovery_days = [False, False, False, False, False, True, False, False, False, False,
                     False, False, False, True, False, False, False, False, False, False,
                     False, False, False, True, False, False, False, False, False, False]

    for i in range(30):
        entry_date = today - timedelta(days=29-i)
        db.add_energy_entry(
            str(entry_date),
            energy_scores[i],
            recovery_days[i],
            f"Day {i+1} tracking"
        )

    print(f"✅ Added 30 days of energy tracking")

    print("\n" + "=" * 50)
    print("🎉 Demo data seeded successfully!")
    print("\nYou now have:")
    print("  • 5 venture studio ideas across different stages")
    print("  • 5 cohort business offers with various scores")
    print("  • 30 days of personal energy tracking")
    print("\nRun the app: streamlit run app.py")

if __name__ == "__main__":
    seed_demo_data()
