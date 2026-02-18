"""
Test Database Module

Run: pytest tests/test_database.py -v
"""

import pytest
import sqlite3
import tempfile
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db import Database, DatabaseError


class TestDatabaseInitialization:
    """Test database initialization and table creation"""

    def test_create_database_in_memory(self):
        """Test creating a temporary in-memory database"""
        db = Database(":memory:")
        assert db.connection is not None
        assert db.connection is sqlite3.connect(":memory:")

    def test_create_database_with_file(self, tmp_path):
        """Test creating a database file"""
        db_file = tmp_path / "test.db"
        db = Database(str(db_file))
        assert db_file.exists()

    def test_create_tables(self, tmp_path):
        """Test table creation"""
        db_file = tmp_path / "test.db"
        db = Database(str(db_file))
        db.initialize()

        cursor = db.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        # Check required tables exist
        assert 'rss_entries' in tables
        assert 'agent_triggers' in tables
        assert 'agent_actions' in tables
        assert 'arbitrage_alerts' in tables
        assert 'competitive_intel' in tables
        assert 'job_alerts' in tables
        assert 'trend_alerts' in tables
        assert 'system_health' in tables

    def test_database_connection(self, tmp_path):
        """Test database connection is maintained"""
        db_file = tmp_path / "test.db"
        db = Database(str(db_file))
        db.initialize()

        # Execute a simple query
        cursor = db.connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

        assert result == (1,)


class TestRSSEntryOperations:
    """Test RSS entry CRUD operations"""

    def test_insert_rss_entry(self, tmp_path):
        """Test inserting an RSS entry"""
        db_file = tmp_path / "test.db"
        db = Database(str(db_file))
        db.initialize()

        entry = {
            'title': 'Test Item',
            'description': 'Test description',
            'link': 'http://example.com/item/1',
            'published': '2026-02-16T12:00:00Z',
            'feed_name': 'test_feed',
            'priority': 1
        }

        entry_id = db.insert_rss_entry(entry)
        assert entry_id is not None
        assert entry_id > 0

    def test_get_rss_entry(self, tmp_path):
        """Test retrieving an RSS entry by ID"""
        db_file = tmp_path / "test.db"
        db = Database(str(db_file))
        db.initialize()

        # Insert an entry
        entry = {
            'title': 'Test Item',
            'description': 'Test description',
            'link': 'http://example.com/item/1',
            'published': '2026-02-16T12:00:00Z',
            'feed_name': 'test_feed',
            'priority': 1
        }
        entry_id = db.insert_rss_entry(entry)

        # Retrieve it
        retrieved = db.get_rss_entry(entry_id)
        assert retrieved is not None
        assert retrieved['title'] == 'Test Item'
        assert retrieved['link'] == 'http://example.com/item/1'

    def test_insert_and_get_multiple_entries(self, tmp_path):
        """Test inserting and retrieving multiple entries"""
        db_file = tmp_path / "test.db"
        db = Database(str(db_file))
        db.initialize()

        entries = [
            {
                'title': f'Item {i}',
                'description': f'Description {i}',
                'link': f'http://example.com/item/{i}',
                'published': '2026-02-16T12:00:00Z',
                'feed_name': 'test_feed',
                'priority': i
            }
            for i in range(5)
        ]

        entry_ids = [db.insert_rss_entry(entry) for entry in entries]

        # Get all entries
        all_entries = db.get_rss_entries()
        assert len(all_entries) == 5

        # Get by priority
        high_priority = db.get_rss_entries(priority=3)
        assert len(high_priority) == 1
        assert high_priority[0]['priority'] == 3


class TestDeduplication:
    """Test duplicate detection"""

    def test_deduplicate_entry_same_content(self, tmp_path):
        """Test that identical entries are deduplicated"""
        db_file = tmp_path / "test.db"
        db = Database(str(db_file))
        db.initialize()

        entry = {
            'title': 'Duplicate Item',
            'description': 'Same content',
            'link': 'http://example.com/item/1',
            'published': '2026-02-16T12:00:00Z',
            'feed_name': 'test_feed',
            'priority': 1
        }

        # Insert twice
        id1 = db.insert_rss_entry(entry)
        id2 = db.insert_rss_entry(entry)

        # Both should return the same ID (or second one is ignored)
        assert id1 == id2

    def test_deduplicate_different_content(self, tmp_path):
        """Test that different entries are stored separately"""
        db_file = tmp_path / "test.db"
        db = Database(str(db_file))
        db.initialize()

        entry1 = {
            'title': 'Item 1',
            'description': 'Different content',
            'link': 'http://example.com/item/1',
            'published': '2026-02-16T12:00:00Z',
            'feed_name': 'test_feed',
            'priority': 1
        }

        entry2 = {
            'title': 'Item 2',
            'description': 'Also different',
            'link': 'http://example.com/item/2',
            'published': '2026-02-16T12:00:00Z',
            'feed_name': 'test_feed',
            'priority': 1
        }

        id1 = db.insert_rss_entry(entry1)
        id2 = db.insert_rss_entry(entry2)

        # Should be different IDs
        assert id1 != id2


class TestAgentTriggerLogging:
    """Test logging agent triggers"""

    def test_log_agent_trigger(self, tmp_path):
        """Test logging when an agent trigger fires"""
        db_file = tmp_path / "test.db"
        db = Database(str(db_file))
        db.initialize()

        trigger_id = db.log_agent_trigger(
            trigger_name='test_trigger',
            confidence_score=0.85,
            matched_entry_id=1,
            raw_text='Test matched text'
        )

        assert trigger_id is not None
        assert trigger_id > 0

    def test_get_recent_triggers(self, tmp_path):
        """Test retrieving recent agent triggers"""
        db_file = tmp_path / "test.db"
        db = Database(str(db_file))
        db.initialize()

        # Insert some triggers
        db.log_agent_trigger('trigger1', 0.9, 1, 'text1')
        db.log_agent_trigger('trigger2', 0.8, 2, 'text2')
        db.log_agent_trigger('trigger3', 0.7, 3, 'text3')

        # Get recent triggers
        recent = db.get_recent_agent_triggers(limit=2)
        assert len(recent) == 2
        assert recent[0]['trigger_name'] == 'trigger3'  # Most recent first


class TestDatabaseErrorHandling:
    """Test error handling"""

    def test_invalid_insert(self, tmp_path):
        """Test inserting invalid data"""
        db_file = tmp_path / "test.db"
        db = Database(str(db_file))
        db.initialize()

        # Missing required fields
        entry = {
            'title': 'Incomplete'
            # Missing link, published, feed_name, priority
        }

        # Should raise an error or handle gracefully
        try:
            db.insert_rss_entry(entry)
        except Exception:
            pass  # Expected to fail


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
