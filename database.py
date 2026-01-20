"""
Database module for CEO Dashboard
Handles SQLite operations for Ideas, Milestones, Offers, and Energy Tracking
"""

import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional


class Database:
    def __init__(self, db_path: str = "ceo_dashboard.db"):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        """Create a database connection"""
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize all database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Ideas table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ideas (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                stage TEXT NOT NULL CHECK(stage IN ('seed', 'validation', 'mvp', 'pilot', 'scale', 'exit')),
                owner TEXT,
                confidence_score INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Milestones table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS milestones (
                id TEXT PRIMARY KEY,
                idea_id TEXT NOT NULL,
                milestone_name TEXT NOT NULL,
                category TEXT CHECK(category IN ('tech', 'market', 'business', 'ops')),
                status TEXT NOT NULL CHECK(status IN ('not_started', 'in_progress', 'done')),
                weight INTEGER DEFAULT 1,
                notes TEXT,
                FOREIGN KEY (idea_id) REFERENCES ideas (id) ON DELETE CASCADE
            )
        """)

        # Offers table (Cohort Business Engine)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS offers (
                id TEXT PRIMARY KEY,
                offer_name TEXT NOT NULL,
                ai_score INTEGER CHECK(ai_score BETWEEN 0 AND 100),
                pricing_fit INTEGER CHECK(pricing_fit BETWEEN 0 AND 10),
                audience_fit INTEGER CHECK(audience_fit BETWEEN 0 AND 10),
                go_no_go TEXT CHECK(go_no_go IN ('go', 'no-go', 'pending')),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Energy Tracking table (Personal Sustainability Engine)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS energy_tracking (
                id TEXT PRIMARY KEY,
                date DATE NOT NULL UNIQUE,
                energy_score INTEGER NOT NULL CHECK(energy_score BETWEEN 1 AND 10),
                recovery_block INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    # ===== IDEAS METHODS =====

    def add_idea(self, name: str, description: str, stage: str, owner: str) -> str:
        """Add a new idea"""
        conn = self.get_connection()
        cursor = conn.cursor()
        idea_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO ideas (id, name, description, stage, owner)
            VALUES (?, ?, ?, ?, ?)
        """, (idea_id, name, description, stage, owner))

        conn.commit()
        conn.close()
        return idea_id

    def get_all_ideas(self) -> List[Dict[str, Any]]:
        """Get all ideas with calculated confidence scores"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM ideas ORDER BY created_at DESC")
        rows = cursor.fetchall()

        ideas = []
        for row in rows:
            idea = {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'stage': row[3],
                'owner': row[4],
                'confidence_score': self.calculate_confidence_score(row[0]),
                'created_at': row[6],
                'updated_at': row[7]
            }
            ideas.append(idea)

        conn.close()
        return ideas

    def get_idea_by_id(self, idea_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific idea by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'stage': row[3],
                'owner': row[4],
                'confidence_score': self.calculate_confidence_score(row[0]),
                'created_at': row[6],
                'updated_at': row[7]
            }
        return None

    def update_idea_stage(self, idea_id: str, stage: str):
        """Update idea stage"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE ideas
            SET stage = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (stage, idea_id))

        conn.commit()
        conn.close()

    def delete_idea(self, idea_id: str):
        """Delete an idea and its milestones"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))

        conn.commit()
        conn.close()

    # ===== MILESTONES METHODS =====

    def add_milestone(self, idea_id: str, milestone_name: str, category: str,
                     status: str, weight: int, notes: str = "") -> str:
        """Add a new milestone"""
        conn = self.get_connection()
        cursor = conn.cursor()
        milestone_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO milestones (id, idea_id, milestone_name, category, status, weight, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (milestone_id, idea_id, milestone_name, category, status, weight, notes))

        conn.commit()
        conn.close()

        # Update idea's confidence score
        self.update_idea_confidence_score(idea_id)

        return milestone_id

    def get_milestones_by_idea(self, idea_id: str) -> List[Dict[str, Any]]:
        """Get all milestones for a specific idea"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM milestones WHERE idea_id = ?", (idea_id,))
        rows = cursor.fetchall()

        milestones = []
        for row in rows:
            milestone = {
                'id': row[0],
                'idea_id': row[1],
                'milestone_name': row[2],
                'category': row[3],
                'status': row[4],
                'weight': row[5],
                'notes': row[6]
            }
            milestones.append(milestone)

        conn.close()
        return milestones

    def update_milestone_status(self, milestone_id: str, status: str):
        """Update milestone status"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get idea_id first
        cursor.execute("SELECT idea_id FROM milestones WHERE id = ?", (milestone_id,))
        result = cursor.fetchone()

        if result:
            idea_id = result[0]
            cursor.execute("UPDATE milestones SET status = ? WHERE id = ?", (status, milestone_id))
            conn.commit()
            conn.close()

            # Update confidence score
            self.update_idea_confidence_score(idea_id)
        else:
            conn.close()

    def delete_milestone(self, milestone_id: str):
        """Delete a milestone"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get idea_id first
        cursor.execute("SELECT idea_id FROM milestones WHERE id = ?", (milestone_id,))
        result = cursor.fetchone()

        if result:
            idea_id = result[0]
            cursor.execute("DELETE FROM milestones WHERE id = ?", (milestone_id,))
            conn.commit()
            conn.close()

            # Update confidence score
            self.update_idea_confidence_score(idea_id)
        else:
            conn.close()

    def calculate_confidence_score(self, idea_id: str) -> int:
        """Calculate confidence score based on weighted milestones"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT weight, status FROM milestones WHERE idea_id = ?
        """, (idea_id,))

        milestones = cursor.fetchall()
        conn.close()

        if not milestones:
            return 0

        total_weight = sum(m[0] for m in milestones)
        completed_weight = sum(m[0] for m in milestones if m[1] == 'done')

        if total_weight == 0:
            return 0

        return int((completed_weight / total_weight) * 100)

    def update_idea_confidence_score(self, idea_id: str):
        """Update the confidence score for an idea"""
        score = self.calculate_confidence_score(idea_id)
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE ideas
            SET confidence_score = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (score, idea_id))

        conn.commit()
        conn.close()

    # ===== OFFERS METHODS =====

    def add_offer(self, offer_name: str, ai_score: int, pricing_fit: int,
                  audience_fit: int, go_no_go: str, notes: str = "") -> str:
        """Add a new offer"""
        conn = self.get_connection()
        cursor = conn.cursor()
        offer_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO offers (id, offer_name, ai_score, pricing_fit, audience_fit, go_no_go, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (offer_id, offer_name, ai_score, pricing_fit, audience_fit, go_no_go, notes))

        conn.commit()
        conn.close()
        return offer_id

    def get_all_offers(self) -> List[Dict[str, Any]]:
        """Get all offers"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM offers ORDER BY ai_score DESC")
        rows = cursor.fetchall()

        offers = []
        for row in rows:
            offer = {
                'id': row[0],
                'offer_name': row[1],
                'ai_score': row[2],
                'pricing_fit': row[3],
                'audience_fit': row[4],
                'go_no_go': row[5],
                'notes': row[6],
                'created_at': row[7]
            }
            offers.append(offer)

        conn.close()
        return offers

    def delete_offer(self, offer_id: str):
        """Delete an offer"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM offers WHERE id = ?", (offer_id,))

        conn.commit()
        conn.close()

    # ===== ENERGY TRACKING METHODS =====

    def add_energy_entry(self, date: str, energy_score: int, recovery_block: bool, notes: str = "") -> str:
        """Add a new energy tracking entry"""
        conn = self.get_connection()
        cursor = conn.cursor()
        entry_id = str(uuid.uuid4())

        try:
            cursor.execute("""
                INSERT INTO energy_tracking (id, date, energy_score, recovery_block, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (entry_id, date, energy_score, 1 if recovery_block else 0, notes))

            conn.commit()
            conn.close()
            return entry_id
        except sqlite3.IntegrityError:
            # Date already exists, update instead
            cursor.execute("""
                UPDATE energy_tracking
                SET energy_score = ?, recovery_block = ?, notes = ?
                WHERE date = ?
            """, (energy_score, 1 if recovery_block else 0, notes, date))

            conn.commit()
            cursor.execute("SELECT id FROM energy_tracking WHERE date = ?", (date,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else entry_id

    def get_energy_entries(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get energy tracking entries for the last N days"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM energy_tracking
            ORDER BY date DESC
            LIMIT ?
        """, (days,))

        rows = cursor.fetchall()

        entries = []
        for row in rows:
            entry = {
                'id': row[0],
                'date': row[1],
                'energy_score': row[2],
                'recovery_block': bool(row[3]),
                'notes': row[4],
                'created_at': row[5]
            }
            entries.append(entry)

        conn.close()
        return entries

    def delete_energy_entry(self, entry_id: str):
        """Delete an energy tracking entry"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM energy_tracking WHERE id = ?", (entry_id,))

        conn.commit()
        conn.close()
