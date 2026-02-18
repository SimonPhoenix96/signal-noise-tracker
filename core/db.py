# Local Database Module
# Uses SQLite3 for persistent storage

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class CronjobDB:
    """SQLite database wrapper for Cronjob Money-MVP"""
    
    def __init__(self, db_path: str = "data/cronjob.db"):
        self.db_path = db_path
        self.connection = None
        self._ensure_directory()
        self._init_database()
    
    def _ensure_directory(self):
        """Ensure data directory exists"""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """Initialize database schema"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._create_tables()
    
    def initialize(self):
        """Initialize database (backward compatibility)"""
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _create_tables(self):
        """Create database tables"""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS rss_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT,
                    description TEXT,
                    published_at TEXT,
                    raw_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS agent_triggers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trigger_name TEXT NOT NULL,
                    source TEXT,
                    matched_keywords TEXT,
                    matched_rules TEXT,
                    confidence REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS agent_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trigger_id INTEGER,
                    action_type TEXT,
                    action_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trigger_id) REFERENCES agent_triggers(id)
                );
                
                CREATE TABLE IF NOT EXISTS arbitrage_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT,
                    description TEXT,
                    price TEXT,
                    location TEXT,
                    timestamp TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS competitive_intel (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS job_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    job_title TEXT,
                    company TEXT,
                    location TEXT,
                    url TEXT,
                    posted_at TEXT,
                    salary_range TEXT
                );
                
                CREATE TABLE IF NOT EXISTS trend_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    trend_type TEXT NOT NULL,
                    trend_name TEXT,
                    data TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS system_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    check_type TEXT,
                    status TEXT,
                    message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_rss_entries_source ON rss_entries(source);
                CREATE INDEX IF NOT EXISTS idx_rss_entries_published_at ON rss_entries(published_at);
                CREATE INDEX IF NOT EXISTS idx_agent_triggers_trigger_name ON agent_triggers(trigger_name);
            """)
    
    def insert_rss_entry(self, title: str = None, source: str = None, 
                        url: str = None, description: str = None,
                        published_at: str = None, raw_data: dict = None,
                        **kwargs) -> int:
        """Insert an RSS entry and check for duplicates
        
        Args:
            title: Entry title
            source: Feed/source name
            url: Entry URL
            description: Entry description
            published_at: Publication timestamp
            raw_data: Additional raw data as dictionary
            **kwargs: Additional fields for compatibility
            
        Returns:
            Entry ID if inserted, 0 if duplicate or error
        """
        try:
            with self._get_connection() as conn:
                # Check for exact match
                cursor = conn.execute("""
                    SELECT id FROM rss_entries 
                    WHERE title = ? AND source = ? AND url = ?
                    LIMIT 1
                """, (title, source, url))
                
                existing = cursor.fetchone()
                if existing:
                    return 0
                
                # Handle legacy dictionary format
                if isinstance(title, dict):
                    data = title
                    source = data.get('feed_name', data.get('source', 'unknown'))
                    title = data.get('title', '')
                    url = data.get('link', data.get('url'))
                    description = data.get('description')
                    published_at = data.get('published', data.get('published_at'))
                    raw_data = data
                
                # Convert raw_data to JSON string if it's a dict
                raw_data_json = json.dumps(raw_data) if raw_data else None
                
                # Insert new entry
                cursor = conn.execute("""
                    INSERT INTO rss_entries 
                    (source, title, url, description, published_at, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (source, title, url, description, published_at, raw_data_json))
                
                return cursor.lastrowid if cursor.lastrowid else conn.lastrowid
        except Exception as e:
            logger.error(f"Failed to insert RSS entry: {e}")
            return 0
    
    def get_rss_entry(self, entry_id: int) -> Optional[Dict]:
        """Retrieve an RSS entry by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM rss_entries WHERE id = ?
                """, (entry_id,))
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    # Convert raw_data back to dict
                    if result.get('raw_data'):
                        result['raw_data'] = json.loads(result['raw_data'])
                    return result
                return None
        except Exception as e:
            logger.error(f"Failed to get RSS entry: {e}")
            return None
    
    def get_recent_entries(self, limit: int = 100, source: str = None) -> List[Dict]:
        """Retrieve recent RSS entries"""
        try:
            with self._get_connection() as conn:
                query = """
                    SELECT * FROM rss_entries 
                    WHERE 1=1
                """
                params = []
                
                if source:
                    query += " AND source = ?"
                    params.append(source)
                
                query += " ORDER BY published_at DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    result = dict(row)
                    if result.get('raw_data'):
                        result['raw_data'] = json.loads(result['raw_data'])
                    results.append(result)
                return results
        except Exception as e:
            logger.error(f"Failed to get recent entries: {e}")
            return []
    
    def insert_trigger(self, trigger_name: str, source: str, 
                      matched_keywords: List[str], matched_rules: List[Dict],
                      confidence: float) -> bool:
        """Log an agent trigger event"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO agent_triggers 
                    (trigger_name, source, matched_keywords, matched_rules, confidence)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    trigger_name, 
                    source,
                    json.dumps(matched_keywords),
                    json.dumps(matched_rules),
                    confidence
                ))
                return True
        except Exception as e:
            logger.error(f"Failed to insert trigger: {e}")
            return False
    
    def insert_agent_action(self, trigger_id: int, action_type: str, action_data: dict = None) -> bool:
        """Insert an agent action"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO agent_actions 
                    (trigger_id, action_type, action_data)
                    VALUES (?, ?, ?)
                """, (trigger_id, action_type, json.dumps(action_data) if action_data else None))
                return True
        except Exception as e:
            logger.error(f"Failed to insert agent action: {e}")
            return False
    
    def get_recent_triggers(self, limit: int = 50) -> List[Dict]:
        """Retrieve recent agent triggers"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM agent_triggers 
                    ORDER BY created_at DESC LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    result = dict(row)
                    # Convert JSON strings back to objects
                    if result.get('matched_keywords'):
                        result['matched_keywords'] = json.loads(result['matched_keywords'])
                    if result.get('matched_rules'):
                        result['matched_rules'] = json.loads(result['matched_rules'])
                    results.append(result)
                return results
        except Exception as e:
            logger.error(f"Failed to get recent triggers: {e}")
            return []
    
    def log_health_check(self, check_type: str, status: str, 
                        message: str = None) -> bool:
        """Log health check"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO system_health 
                    (check_type, status, message)
                    VALUES (?, ?, ?)
                """, (check_type, status, message))
            return True
        except Exception as e:
            logger.error(f"Failed to log health check: {e}")
            return False
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        try:
            with self._get_connection() as conn:
                stats = {}
                
                # Count entries in each table
                tables = ['rss_entries', 'agent_triggers', 'agent_actions', 
                         'arbitrage_alerts', 'competitive_intel', 'job_alerts', 
                         'trend_alerts', 'system_health']
                
                for table in tables:
                    try:
                        cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
                        stats[table] = cursor.fetchone()['count']
                    except:
                        stats[table] = 0
                
                return stats
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

# Singleton instance
db = CronjobDB()

# Compatibility alias for backward compatibility
Database = CronjobDB
DatabaseError = Exception
