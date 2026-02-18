"""
Test Agent Trigger Module

Run: pytest tests/test_agent_trigger.py -v
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.agent_trigger import AgentTrigger, TriggerConfig
from core.db import Database


@pytest.fixture
def sample_config():
    """Sample trigger configuration"""
    return TriggerConfig(
        name="Test Trigger",
        keywords=["deal", "sale", "cheap"],
        fields=["title", "description"],
        confidence_threshold=0.6,
        exclude_keywords=[]
    )


@pytest.fixture
def sample_entries():
    """Sample RSS entries for testing"""
    return [
        {
            'title': 'Great Deal Today!',
            'description': '50% off everything - don\'t miss out',
            'link': 'http://example.com/deal1',
            'published': '2026-02-16T12:00:00Z',
            'feed_name': 'test_feed',
            'priority': 1
        },
        {
            'title': 'Regular Price Item',
            'description': 'Just a normal item for sale',
            'link': 'http://example.com/normal',
            'published': '2026-02-16T11:00:00Z',
            'feed_name': 'test_feed',
            'priority': 1
        },
        {
            'title': 'Another Great Sale',
            'description': 'Limited time offer',
            'link': 'http://example.com/sale2',
            'published': '2026-02-16T10:00:00Z',
            'feed_name': 'test_feed',
            'priority': 2
        }
    ]


class TestTriggerInitialization:
    """Test trigger initialization"""

    def test_trigger_creation(self, sample_config):
        """Test creating an agent trigger"""
        trigger = AgentTrigger(sample_config)
        assert trigger is not None
        assert trigger.config.name == "Test Trigger"

    def test_trigger_with_empty_keywords(self):
        """Test trigger with empty keywords (matches everything)"""
        config = TriggerConfig(
            name="Empty Keyword Trigger",
            keywords=[],
            fields=["title"],
            confidence_threshold=0.5
        )
        trigger = AgentTrigger(config)
        assert trigger is not None


class TestTriggerMatching:
    """Test trigger matching logic"""

    def test_match_exact_keyword(self, sample_config, sample_entries):
        """Test matching entries with exact keyword"""
        trigger = AgentTrigger(sample_config)
        matches = trigger.match(sample_entries)

        assert len(matches) == 2
        assert matches[0]['title'] == 'Great Deal Today!'
        assert matches[0]['confidence'] >= 0.6

    def test_match_case_insensitive(self, sample_config, sample_entries):
        """Test matching is case-insensitive"""
        trigger = AgentTrigger(sample_config)
        matches = trigger.match(sample_entries)

        # Should match regardless of case
        assert len(matches) > 0

    def test_match_in_description(self, sample_config, sample_entries):
        """Test matching in description field"""
        trigger = AgentTrigger(sample_config)
        matches = trigger.match(sample_entries)

        # Should match 'Cheap' in description
        assert len(matches) > 0

    def test_field_specific_matching(self, sample_config, sample_entries):
        """Test matching only in specified fields"""
        # Change to match only title
        config = TriggerConfig(
            name="Title Only Trigger",
            keywords=["deal"],
            fields=["title"],  # Only match in title
            confidence_threshold=0.5
        )
        trigger = AgentTrigger(config)
        matches = trigger.match(sample_entries)

        # Should match only entries with 'deal' in title
        assert all('deal' in m['matched_text'].lower() for m in matches)

    def test_exclude_keywords(self, sample_config, sample_entries):
        """Test excluding certain keywords"""
        # Add exclude keyword
        config = TriggerConfig(
            name="Exclude Trigger",
            keywords=["deal", "sale"],
            fields=["title"],
            confidence_threshold=0.5,
            exclude_keywords=["special", "promo"]
        )
        trigger = AgentTrigger(config)
        matches = trigger.match(sample_entries)

        # Should exclude entries with excluded keywords
        for match in matches:
            matched_text = match['matched_text'].lower()
            excluded = [kw for kw in config.exclude_keywords if kw.lower() in matched_text]
            assert len(excluded) == 0

    def test_confidence_scoring(self, sample_config, sample_entries):
        """Test confidence score calculation"""
        trigger = AgentTrigger(sample_config)
        matches = trigger.match(sample_entries)

        # All matches should have confidence >= threshold
        for match in matches:
            assert match['confidence'] >= sample_config.confidence_threshold


class TestTriggerBatchProcessing:
    """Test batch processing of entries"""

    def test_batch_matching(self, sample_config, sample_entries):
        """Test matching multiple entries in batch"""
        trigger = AgentTrigger(sample_config)
        matches = trigger.match(sample_entries)

        assert len(matches) == 2  # Only the two 'deal' entries match

    def test_empty_entry_list(self, sample_config):
        """Test matching with empty entry list"""
        trigger = AgentTrigger(sample_config)
        matches = trigger.match([])

        assert len(matches) == 0

    def test_match_all_if_no_keywords(self):
        """Test matching all entries when keywords are empty"""
        config = TriggerConfig(
            name="Any Trigger",
            keywords=[],
            fields=["title"],
            confidence_threshold=0.5
        )
        trigger = AgentTrigger(config)
        entries = [
            {'title': 'Item 1', 'link': 'http://example.com/1', 'description': 'Test',
             'published': '2026-02-16T12:00:00Z', 'feed_name': 'test', 'priority': 1}
        ]
        matches = trigger.match(entries)

        # Should match everything when no keywords specified
        assert len(matches) == 1


class TestTriggerWithDatabase:
    """Test trigger integration with database"""

    def test_log_matches_to_database(self, tmp_path, sample_config, sample_entries):
        """Test logging matched entries to database"""
        db_file = tmp_path / "test.db"
        db = Database(str(db_file))
        db.initialize()

        trigger = AgentTrigger(sample_config)
        matches = trigger.match(sample_entries)

        # Log matches to database
        for match in matches:
            db.log_agent_trigger(
                trigger_name=sample_config.name,
                confidence_score=match['confidence'],
                matched_entry_id=match['entry_id'],
                raw_text=match['matched_text']
            )

        # Verify database has logged triggers
        triggers = db.get_recent_agent_triggers(limit=10)
        assert len(triggers) == len(matches)

    def test_filter_matches_by_confidence(self, sample_config, sample_entries):
        """Test filtering matches by confidence threshold"""
        trigger = AgentTrigger(sample_config)
        matches = trigger.match(sample_entries)

        # Filter by confidence
        high_confidence = [m for m in matches if m['confidence'] >= 0.7]
        assert len(high_confidence) > 0

        # Filter out low confidence
        low_confidence = [m for m in matches if m['confidence'] < 0.7]
        assert len(low_confidence) == 0


class TestTriggerConfig:
    """Test trigger configuration validation"""

    def test_config_with_minimal_fields(self):
        """Test configuration with minimal required fields"""
        config = TriggerConfig(
            name="Minimal Trigger",
            keywords=["test"],
            fields=["title"],
            confidence_threshold=0.5
        )
        assert config.name == "Minimal Trigger"
        assert len(config.keywords) == 1
        assert len(config.fields) == 1

    def test_config_with_multiple_keywords(self):
        """Test configuration with multiple keywords"""
        config = TriggerConfig(
            name="Multiple Keywords",
            keywords=["deal", "sale", "discount", "cheap"],
            fields=["title"],
            confidence_threshold=0.5
        )
        assert len(config.keywords) == 4

    def test_config_with_multiple_fields(self):
        """Test configuration with multiple fields to search"""
        config = TriggerConfig(
            name="Multi-field Trigger",
            keywords=["test"],
            fields=["title", "description", "tags"],
            confidence_threshold=0.5
        )
        assert len(config.fields) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
