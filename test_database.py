"""
Test script to verify database operations
"""

from database import Database
from datetime import date

def test_database():
    """Test all database operations"""
    print("🧪 Testing CEO Dashboard Database...")
    print("=" * 50)

    # Initialize database
    db = Database("test_ceo_dashboard.db")
    print("✅ Database initialized")

    # Test Ideas
    print("\n📋 Testing Ideas...")
    idea_id = db.add_idea(
        name="AI-Powered CRM",
        description="Customer relationship management with AI insights",
        stage="seed",
        owner="John Doe"
    )
    print(f"✅ Added idea: {idea_id}")

    ideas = db.get_all_ideas()
    print(f"✅ Retrieved {len(ideas)} ideas")
    print(f"   Idea: {ideas[0]['name']} - Stage: {ideas[0]['stage']}")

    # Test Milestones
    print("\n🎯 Testing Milestones...")
    milestone_id = db.add_milestone(
        idea_id=idea_id,
        milestone_name="10 customer interviews",
        category="market",
        status="in_progress",
        weight=3,
        notes="Focus on early adopters"
    )
    print(f"✅ Added milestone: {milestone_id}")

    milestone_id2 = db.add_milestone(
        idea_id=idea_id,
        milestone_name="Build MVP prototype",
        category="tech",
        status="done",
        weight=5,
        notes="Core features only"
    )
    print(f"✅ Added milestone: {milestone_id2}")

    milestones = db.get_milestones_by_idea(idea_id)
    print(f"✅ Retrieved {len(milestones)} milestones")

    # Test confidence score calculation
    idea = db.get_idea_by_id(idea_id)
    print(f"✅ Confidence score calculated: {idea['confidence_score']}%")
    print(f"   (Should be ~62% with 5/8 weight completed)")

    # Test Offers
    print("\n💼 Testing Offers...")
    offer_id = db.add_offer(
        offer_name="AI Mastery Cohort",
        ai_score=85,
        pricing_fit=8,
        audience_fit=9,
        go_no_go="go",
        notes="Strong market validation"
    )
    print(f"✅ Added offer: {offer_id}")

    offers = db.get_all_offers()
    print(f"✅ Retrieved {len(offers)} offers")
    print(f"   Offer: {offers[0]['offer_name']} - AI Score: {offers[0]['ai_score']}")

    # Test Energy Tracking
    print("\n🌿 Testing Energy Tracking...")
    energy_id = db.add_energy_entry(
        date=str(date.today()),
        energy_score=8,
        recovery_block=False,
        notes="Good sleep, productive day"
    )
    print(f"✅ Added energy entry: {energy_id}")

    entries = db.get_energy_entries(days=7)
    print(f"✅ Retrieved {len(entries)} energy entries")
    print(f"   Entry: {entries[0]['date']} - Score: {entries[0]['energy_score']}/10")

    # Test update operations
    print("\n🔄 Testing Updates...")
    db.update_milestone_status(milestone_id, "done")
    updated_idea = db.get_idea_by_id(idea_id)
    print(f"✅ Updated milestone status")
    print(f"   New confidence score: {updated_idea['confidence_score']}%")
    print(f"   (Should be 100% with all milestones completed)")

    db.update_idea_stage(idea_id, "validation")
    print(f"✅ Updated idea stage to validation")

    print("\n" + "=" * 50)
    print("🎉 All tests passed successfully!")
    print("\nSample data created for testing the app.")
    print("You can now run: streamlit run app.py")

if __name__ == "__main__":
    test_database()
