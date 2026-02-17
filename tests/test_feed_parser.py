"""
Unit tests for RSS Feed Parser
"""

import pytest
from datetime import datetime, timedelta

from modules.rss.parser import FeedParser, FeedItem
from modules.rss.filter import ItemFilter


class TestFeedParser:
    """Test RSS Feed Parser"""

    def test_initialization(self):
        """Test parser initialization"""
        parser = FeedParser(timeout=30)
        assert parser.timeout == 30

    def test_parse_sample_feed(self, monkeypatch):
        """Test parsing a sample RSS feed"""
        # This would need a real feed or mocked response
        # For now, we just verify the class exists
        parser = FeedParser()
        assert parser is not None

    def test_generate_id(self):
        """Test ID generation"""
        parser = FeedParser()
        test_id = "test_id_123"
        generated_id = parser._generate_id(test_id)

        assert generated_id.startswith(test_id)
        assert "_" in generated_id

    def test_clean_text(self):
        """Test text cleaning"""
        parser = FeedParser()

        # Test HTML removal
        html_text = "<p>Test & <b>bold</b> text</p>"
        cleaned = parser._clean_text(html_text)
        assert "<p>" not in cleaned
        assert "<b>" not in cleaned
        assert "&" in cleaned  # Should decode &amp; to &

        # Test truncation
        long_text = "a" * 1000
        cleaned = parser._clean_text(long_text)
        assert len(cleaned) <= 503  # 500 + "..." = 503

    def test_parse_date(self):
        """Test date parsing"""
        parser = FeedParser()

        # Test with datetime object
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = parser._parse_date(dt)
        assert result == dt

        # Test with tuple
        dt_tuple = (2024, 1, 1, 12, 0, 0, 0, 0, 0)
        result = parser._parse_date(dt_tuple)
        assert result.year == 2024

        # Test with None
        result = parser._parse_date(None)
        assert result is not None  # Should return current time


class TestFeedItem:
    """Test FeedItem dataclass"""

    def test_create_item(self):
        """Test creating a FeedItem"""
        dt = datetime.utcnow()

        item = FeedItem(
            id="test_id",
            title="Test Title",
            description="Test description",
            link="https://example.com",
            published=dt,
            updated=dt,
            tags=["test", "demo"],
            raw_data={}
        )

        assert item.id == "test_id"
        assert item.title == "Test Title"
        assert item.tags == ["test", "demo"]
        assert item.published == dt

    def test_to_dict(self):
        """Test converting to dictionary"""
        item = FeedItem(
            id="test_id",
            title="Test",
            description="Test",
            link="https://example.com",
            published=datetime.utcnow(),
            updated=datetime.utcnow(),
            tags=[],
            raw_data={}
        )

        item_dict = item.to_dict()
        assert "id" in item_dict
        assert "title" in item_dict
        assert "tags" in item_dict


class TestItemFilter:
    """Test Item Filter"""

    def test_initialization(self):
        """Test filter initialization"""
        config = {"max_age_days": 7}
        filter_obj = ItemFilter(config)
        assert filter_obj.config == config

    def test_filter_by_age(self):
        """Test filtering by age"""
        config = {"max_age_days": 7}
        filter_obj = ItemFilter(config)

        dt_now = datetime.utcnow()
        dt_old = dt_now - timedelta(days=8)
        dt_recent = dt_now - timedelta(days=3)

        items = [
            FeedItem("1", "Old", "desc", "url", dt_old, dt_old, [], {}),
            FeedItem("2", "Recent", "desc", "url", dt_recent, dt_recent, [], {}),
        ]

        filtered = filter_obj.filter(items)
        assert len(filtered) == 1
        assert filtered[0].id == "2"

    def test_filter_by_required_tags(self):
        """Test filtering by required tags"""
        config = {"required_tags": ["tag1"]}
        filter_obj = ItemFilter(config)

        items = [
            FeedItem("1", "T1 T2", "desc", "url", datetime.utcnow(), datetime.utcnow(), ["tag1", "tag2"], {}),
            FeedItem("2", "No tags", "desc", "url", datetime.utcnow(), datetime.utcnow(), ["tag3"], {}),
        ]

        filtered = filter_obj.filter(items)
        assert len(filtered) == 1
        assert filtered[0].id == "1"

    def test_filter_by_excluded_tags(self):
        """Test filtering by excluded tags"""
        config = {"exclude_tags": ["spam"]}
        filter_obj = ItemFilter(config)

        items = [
            FeedItem("1", "Valid", "desc", "url", datetime.utcnow(), datetime.utcnow(), ["good"], {}),
            FeedItem("2", "Spam", "desc", "url", datetime.utcnow(), datetime.utcnow(), ["spam"], {}),
        ]

        filtered = filter_obj.filter(items)
        assert len(filtered) == 1
        assert filtered[0].id == "1"

    def test_filter_by_patterns(self):
        """Test filtering by regex patterns"""
        config = {
            "include_patterns": ["deal", "sale"],
            "exclude_patterns": ["scam", "spam"]
        }
        filter_obj = ItemFilter(config)

        items = [
            FeedItem("1", "Great Deal", "desc", "url", datetime.utcnow(), datetime.utcnow(), [], {}),
            FeedItem("2", "Spam Email", "desc", "url", datetime.utcnow(), datetime.utcnow(), [], {}),
            FeedItem("3", "Free Stuff", "desc", "url", datetime.utcnow(), datetime.utcnow(), [], {}),
        ]

        filtered = filter_obj.filter(items)
        # Only item 1 should pass: matches "deal" (include), doesn't match "spam"/"scam" (exclude)
        # Item 2 fails: matches "spam" (exclude)
        # Item 3 fails: doesn't match "deal" or "sale" (include)
        assert len(filtered) == 1
        assert filtered[0].id == "1"
        assert "deal" in filtered[0].title.lower() or "sale" in filtered[0].title.lower()

    def test_no_filters(self):
        """Test when no filters are configured"""
        config = {}
        filter_obj = ItemFilter(config)

        items = [
            FeedItem("1", "Test", "desc", "url", datetime.utcnow(), datetime.utcnow(), [], {}),
            FeedItem("2", "Test", "desc", "url", datetime.utcnow(), datetime.utcnow(), [], {}),
        ]

        filtered = filter_obj.filter(items)
        assert len(filtered) == 2
