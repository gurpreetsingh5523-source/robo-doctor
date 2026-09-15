"""
AMRIT Cross-Session Memory v6.2
Persistent user profiles, preferences, and history across sessions
Inspired by Hermes Agent cross-session memory
"""
import sqlite3
import json
import pickle
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import threading

@dataclass
class UserProfile:
    """Complete user profile with health data"""
    user_id: str
    name: str
    email: Optional[str]
    created_at: str
    last_active: str

    # Health data
    blood_history: List[Dict] = None
    dna_variants: Dict[str, str] = None
    health_recommendations: List[Dict] = None

    # Preferences
    language: str = "punjabi"
    population: str = "south_asian"
    notification_enabled: bool = True
    auto_backup: bool = True

    # Research preferences
    tracked_topics: List[str] = None
    research_frequency: str = "weekly"
    alert_threshold: str = "moderate"

    # Session history
    total_sessions: int = 0
    total_queries: int = 0
    favorite_modules: List[str] = None

class CrossSessionMemory:
    """
    Persistent memory system for user profiles and session history
    Survives across browser sessions, Telegram chats, and API calls
    """

    def __init__(self, db_path: str = "data/amrit_users.db"):
        self.db_path = db_path
        self.lock = threading.RLock()
        self._init_database()

    def _init_database(self):
        """Initialize user database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    profile TEXT,
                    blood_history TEXT,
                    dna_variants TEXT,
                    health_recommendations TEXT,
                    preferences TEXT,
                    session_history TEXT,
                    created_at TEXT,
                    last_active TEXT
                )
            """)

            # Session logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    session_type TEXT,
                    query TEXT,
                    response TEXT,
                    module_used TEXT,
                    timestamp TEXT,
                    duration_ms INTEGER
                )
            """)

            # Research tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS research_tracking (
                    track_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    topic TEXT,
                    status TEXT,
                    findings TEXT,
                    created_at TEXT,
                    completed_at TEXT
                )
            """)

            # Health alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS health_alerts (
                    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    alert_type TEXT,
                    severity TEXT,
                    message TEXT,
                    acknowledged BOOLEAN,
                    created_at TEXT
                )
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        try:
            yield conn
        finally:
            conn.close()

    def create_user(self, user_id: str, name: str, email: Optional[str] = None) -> UserProfile:
        """Create new user profile"""
        now = datetime.now().isoformat()

        profile = UserProfile(
            user_id=user_id,
            name=name,
            email=email,
            created_at=now,
            last_active=now,
            blood_history=[],
            dna_variants={},
            health_recommendations=[],
            tracked_topics=[],
            favorite_modules=[]
        )

        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, profile, blood_history, dna_variants, health_recommendations, 
                 preferences, session_history, created_at, last_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                json.dumps(asdict(profile)),
                json.dumps([]),
                json.dumps({}),
                json.dumps([]),
                json.dumps({'language': 'punjabi', 'population': 'south_asian'}),
                json.dumps([]),
                now, now
            ))
            conn.commit()

        return profile

    def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile"""
        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT profile FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()

            if row:
                profile_data = json.loads(row[0])
                return UserProfile(**profile_data)

        return None

    def update_user(self, user_id: str, updates: Dict) -> bool:
        """Update user profile"""
        profile = self.get_user(user_id)
        if not profile:
            return False

        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.last_active = datetime.now().isoformat()

        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET profile = ?, last_active = ? WHERE user_id = ?
            """, (json.dumps(asdict(profile)), profile.last_active, user_id))
            conn.commit()

        return True

    def add_blood_test(self, user_id: str, test_results: Dict):
        """Add blood test to user history"""
        profile = self.get_user(user_id)
        if not profile:
            return False

        entry = {
            'date': datetime.now().isoformat(),
            'results': test_results
        }

        profile.blood_history.append(entry)

        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET blood_history = ? WHERE user_id = ?
            """, (json.dumps(profile.blood_history), user_id))
            conn.commit()

        return True

    def add_dna_variants(self, user_id: str, variants: Dict):
        """Add DNA variants to user profile"""
        profile = self.get_user(user_id)
        if not profile:
            return False

        profile.dna_variants.update(variants)

        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET dna_variants = ? WHERE user_id = ?
            """, (json.dumps(profile.dna_variants), user_id))
            conn.commit()

        return True

    def add_health_recommendation(self, user_id: str, recommendation: Dict):
        """Add health recommendation"""
        profile = self.get_user(user_id)
        if not profile:
            return False

        recommendation['date'] = datetime.now().isoformat()
        profile.health_recommendations.append(recommendation)

        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET health_recommendations = ? WHERE user_id = ?
            """, (json.dumps(profile.health_recommendations), user_id))
            conn.commit()

        return True

    def log_session(self, user_id: str, session_type: str, query: str, 
                   response: str, module_used: str, duration_ms: int = 0):
        """Log session interaction"""
        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO session_logs 
                (user_id, session_type, query, response, module_used, timestamp, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, session_type, query, response, module_used, 
                  datetime.now().isoformat(), duration_ms))
            conn.commit()

        profile = self.get_user(user_id)
        if profile:
            profile.total_queries += 1
            self.update_user(user_id, {'total_queries': profile.total_queries})

    def get_session_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user's session history"""
        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM session_logs 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (user_id, limit))

            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def add_health_alert(self, user_id: str, alert_type: str, severity: str, message: str):
        """Add health alert for user"""
        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO health_alerts 
                (user_id, alert_type, severity, message, acknowledged, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, alert_type, severity, message, False, datetime.now().isoformat()))
            conn.commit()

    def get_health_alerts(self, user_id: str, acknowledged: bool = False) -> List[Dict]:
        """Get user's health alerts"""
        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM health_alerts 
                WHERE user_id = ? AND acknowledged = ?
                ORDER BY created_at DESC
            """, (user_id, acknowledged))

            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def acknowledge_alert(self, alert_id: int) -> bool:
        """Acknowledge health alert"""
        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE health_alerts SET acknowledged = ? WHERE alert_id = ?
            """, (True, alert_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_user_stats(self, user_id: str) -> Dict:
        """Get comprehensive user statistics"""
        profile = self.get_user(user_id)
        if not profile:
            return {'error': 'User not found'}

        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(DISTINCT timestamp) FROM session_logs WHERE user_id = ?
            """, (user_id,))
            total_sessions = cursor.fetchone()[0]

            cursor.execute("""
                SELECT module_used, COUNT(*) as count 
                FROM session_logs 
                WHERE user_id = ? 
                GROUP BY module_used 
                ORDER BY count DESC 
                LIMIT 5
            """, (user_id,))
            favorite_modules = [{'module': row[0], 'uses': row[1]} for row in cursor.fetchall()]

            cursor.execute("""
                SELECT COUNT(*) FROM health_alerts WHERE user_id = ? AND acknowledged = ?
            """, (user_id, False))
            pending_alerts = cursor.fetchone()[0]

        return {
            'user_id': user_id,
            'name': profile.name,
            'member_since': profile.created_at,
            'last_active': profile.last_active,
            'total_sessions': total_sessions,
            'total_queries': profile.total_queries,
            'blood_tests_recorded': len(profile.blood_history) if profile.blood_history else 0,
            'dna_variants_recorded': len(profile.dna_variants) if profile.dna_variants else 0,
            'health_recommendations': len(profile.health_recommendations) if profile.health_recommendations else 0,
            'favorite_modules': favorite_modules,
            'pending_alerts': pending_alerts,
            'language': profile.language,
            'population': profile.population
        }

    def export_user_data(self, user_id: str) -> Dict:
        """Export all user data for portability"""
        profile = self.get_user(user_id)
        if not profile:
            return {'error': 'User not found'}

        return {
            'profile': asdict(profile),
            'session_history': self.get_session_history(user_id, 1000),
            'health_alerts': self.get_health_alerts(user_id, acknowledged=False) + 
                             self.get_health_alerts(user_id, acknowledged=True),
            'exported_at': datetime.now().isoformat(),
            'version': '6.2'
        }

    def import_user_data(self, user_id: str, data: Dict) -> bool:
        """Import user data from export"""
        try:
            profile_data = data.get('profile', {})
            profile = UserProfile(**profile_data)

            with self.lock, self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO users 
                    (user_id, profile, blood_history, dna_variants, health_recommendations,
                     preferences, session_history, created_at, last_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    json.dumps(asdict(profile)),
                    json.dumps(profile.blood_history or []),
                    json.dumps(profile.dna_variants or {}),
                    json.dumps(profile.health_recommendations or []),
                    json.dumps({'language': profile.language, 'population': profile.population}),
                    json.dumps([]),
                    profile.created_at,
                    datetime.now().isoformat()
                ))
                conn.commit()

            return True
        except Exception as e:
            print("Import error: %s" % str(e))
            return False


class UserContextManager:
    """
    Manages user context across different interfaces (Web, Telegram, API)
    """

    def __init__(self, memory: CrossSessionMemory):
        self.memory = memory
        self.active_contexts = {}

    def get_or_create_user(self, user_id: str, name: str = None, 
                          source: str = "web") -> UserProfile:
        """Get existing user or create new one"""
        user = self.memory.get_user(user_id)

        if not user:
            user = self.memory.create_user(
                user_id=user_id,
                name=name or "User_%s" % user_id[:6],
                email=None
            )

        self.memory.update_user(user_id, {'last_active': datetime.now().isoformat()})

        self.active_contexts[user_id] = {
            'source': source,
            'started_at': datetime.now().isoformat()
        }

        return user

    def enrich_query(self, user_id: str, query: str) -> Dict:
        """Enrich query with user context"""
        user = self.memory.get_user(user_id)
        if not user:
            return {'query': query, 'context': {}}

        context = {
            'user_id': user_id,
            'population': user.population,
            'language': user.language,
            'recent_blood_tests': user.blood_history[-3:] if user.blood_history else [],
            'dna_variants': user.dna_variants,
            'tracked_topics': user.tracked_topics,
            'previous_queries': self.memory.get_session_history(user_id, 5)
        }

        return {
            'query': query,
            'context': context
        }

    def end_session(self, user_id: str):
        """End user session and cleanup"""
        if user_id in self.active_contexts:
            del self.active_contexts[user_id]
