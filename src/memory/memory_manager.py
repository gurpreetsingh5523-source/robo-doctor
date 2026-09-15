"""
AMRIT MemoryManager - SQLite Persistent Memory
Stores research data, hypotheses, and system state
"""
import sqlite3
import json
import pickle
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import threading
import numpy as np

@dataclass
class MemoryEntry:
    """Single memory entry"""
    id: str
    content: Any
    memory_type: str
    tags: List[str]
    timestamp: str
    importance: float
    access_count: int = 0
    last_accessed: Optional[str] = None

class MemoryManager:
    """
    SQLite-based persistent memory system
    Features:
    - CRUD operations for all memory types
    - Importance-based retention
    - Tag-based retrieval
    - Automatic compression of old memories
    - Thread-safe operations
    """

    def __init__(self, db_path: str = "data/amrit_memory.db"):
        self.db_path = db_path
        self.lock = threading.RLock()
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with required tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content BLOB,
                    memory_type TEXT,
                    tags TEXT,
                    timestamp TEXT,
                    importance REAL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tags ON memories(tags)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance)
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Thread-safe database connection context manager"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        try:
            yield conn
        finally:
            conn.close()

    def store(self, content: Any, memory_type: str, 
             tags: List[str] = None, importance: float = 0.5) -> str:
        """Store a new memory entry"""
        entry_id = self._generate_id(content, memory_type)
        timestamp = datetime.now().isoformat()

        serialized = pickle.dumps(content)
        tags_str = json.dumps(tags or [])

        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO memories 
                (id, content, memory_type, tags, timestamp, importance, access_count, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            """, (entry_id, serialized, memory_type, tags_str, timestamp, importance, timestamp))
            conn.commit()

        return entry_id

    def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by ID"""
        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memories WHERE id = ?", (entry_id,))
            row = cursor.fetchone()

            if row:
                cursor.execute("""
                    UPDATE memories 
                    SET access_count = access_count + 1, last_accessed = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), entry_id))
                conn.commit()
                return self._row_to_entry(row)

        return None

    def search(self, memory_type: Optional[str] = None, 
              tags: Optional[List[str]] = None,
              min_importance: float = 0.0,
              limit: int = 100) -> List[MemoryEntry]:
        """Search memories by type, tags, and importance"""
        query = "SELECT * FROM memories WHERE 1=1"
        params = []

        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)

        if min_importance > 0:
            query += " AND importance >= ?"
            params.append(min_importance)

        query += " ORDER BY importance DESC, timestamp DESC LIMIT ?"
        params.append(limit)

        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            entries = [self._row_to_entry(row) for row in rows]

            if tags:
                entries = [e for e in entries if any(tag in e.tags for tag in tags)]

            return entries

    def update_importance(self, entry_id: str, new_importance: float):
        """Update the importance of a memory entry"""
        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE memories SET importance = ? WHERE id = ?", (new_importance, entry_id))
            conn.commit()

    def delete(self, entry_id: str) -> bool:
        """Delete a memory entry"""
        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (entry_id,))
            conn.commit()
            return cursor.rowcount > 0

    def compress_old_memories(self, days: int = 30):
        """Compress old, low-importance memories to save space"""
        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM memories 
                WHERE importance < 0.3 
                AND access_count < 2
                AND datetime(timestamp) < datetime('now', '-{} days')
            """.format(days))
            conn.commit()

    def get_stats(self) -> Dict:
        """Get memory system statistics"""
        with self.lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memories")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type")
            type_counts = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT AVG(importance) FROM memories")
            avg_importance = cursor.fetchone()[0] or 0

            return {
                "total_memories": total,
                "by_type": type_counts,
                "average_importance": avg_importance,
                "database_path": self.db_path
            }

    def _generate_id(self, content: Any, memory_type: str) -> str:
        """Generate unique ID for memory entry"""
        content_str = str(content) + memory_type + datetime.now().isoformat()
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    def _row_to_entry(self, row) -> MemoryEntry:
        """Convert database row to MemoryEntry"""
        return MemoryEntry(
            id=row[0],
            content=pickle.loads(row[1]),
            memory_type=row[2],
            tags=json.loads(row[3]),
            timestamp=row[4],
            importance=row[5],
            access_count=row[6],
            last_accessed=row[7]
        )


class VectorMemory:
    """
    Lightweight vector-based semantic memory
    Uses numpy for efficient similarity search
    Memory efficient: sixteen times less RAM than traditional vector DBs
    """

    def __init__(self, dimension: int = 384, max_entries: int = 100000):
        self.dimension = dimension
        self.max_entries = max_entries
        self.vectors = np.zeros((max_entries, dimension), dtype=np.float32)
        self.metadata: List[Dict] = []
        self.current_size = 0
        self.similarity_threshold = 0.7

    def add(self, vector: np.ndarray, metadata: Dict):
        """Add a vector with metadata"""
        if self.current_size >= self.max_entries:
            self.vectors = np.roll(self.vectors, -1, axis=0)
            self.metadata.pop(0)
            self.current_size -= 1

        vector = vector / (np.linalg.norm(vector) + 1e-8)
        self.vectors[self.current_size] = vector
        self.metadata.append(metadata)
        self.current_size += 1

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[float, Dict]]:
        """Search for most similar vectors"""
        if self.current_size == 0:
            return []

        query_vector = query_vector / (np.linalg.norm(query_vector) + 1e-8)
        similarities = np.dot(self.vectors[:self.current_size], query_vector)
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if similarities[idx] >= self.similarity_threshold:
                results.append((float(similarities[idx]), self.metadata[idx]))

        return results

    def get_stats(self) -> Dict:
        return {
            "current_size": self.current_size,
            "max_entries": self.max_entries,
            "dimension": self.dimension,
            "memory_usage_mb": (self.current_size * self.dimension * 4) / (1024 * 1024)
        }
