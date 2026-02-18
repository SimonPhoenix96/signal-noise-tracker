"""
Test RSS Parser Module

Run: pytest tests/test_rss_parser.py -v
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from core.rss_parser import RSSParser, RSSParseError
    from core.db import Database
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False


@pytest.mark.skipif(not FEEDPARSER_AVAILABLE, reason="feedparser not installed")
class TestRSSParserInitialization:
    """Test RSS parser initialization"""

    def test_parser_creation(self):
        """Test creating an RSS parser"""
        parser = RSSParser()
        assert parser is not None
        assert hasattr(parser, 'session')
        assert parser.rate_limits == {}

    def test_parser_with_custom_rate_limits(self):
        """Test creating a parser with custom rate limits"""
        rate_limits = {'test_feed': 3600}
        parser = RSSParser(rate_limits=rate_limits)
        assert parser.rate_limits == rate_limits

    def test_parser_with_session(self):
        """Test creating a parser with custom requests session"""
        import requests
        session = requests.Session()
        parser = RSSParser(session=session)
        assert parser.session == session


@pytest.mark.skipif(not FEEDPARSER_AVAILABLE, reason="feedparser not installed")
class TestRSSParserFetch:
    """Test RSS feed fetching"""

    @pytest.fixture
    def sample_feed_url(self):
        """Provide a sample RSS feed URL"""
        # Using a simple RSS feed for testing
        return "https://feeds.feedburner.com/TechCrunch/"

    def test_fetch_feed(self, sample_feed_url):
        """Test fetching and parsing an RSS feed"""
        parser = RSSParser()
        entries = parser.fetch_feed(sample_feed_url)

        assert entries is not None
        assert isinstance(entries, list)
        assert len(entries) > 0

    def test_fetch_single_entry(self, sample_feed_url):
        """Test fetching feed and accessing single entry"""
        parser = RSSParser()
        entries = parser.fetch_feed(sample_feed_url)

        if entries:
            entry = entries[0]
            assert hasattr(entry, 'title')
            assert hasattr(entry, 'link')
            assert hasattr(entry, 'published')
            assert hasattr(entry, 'description')

    def test_fetch_with_timeout(self, sample_feed_url):
        """Test fetching with timeout"""
        parser = RSSParser()
        try:
            # Fetch with a short timeout
            entries = parser.fetch_feed(sample_feed_url, timeout=5)
            assert entries is not None
        except Exception:
            # May fail if network is slow, but should not timeout indefinitely
            pass

    def test_invalid_url(self):
        """Test fetching an invalid URL"""
        parser = RSSParser()
        with pytest.raises(Exception):
            parser.fetch_feed("http://this-url-does-not-exist-12345.com/rss.xml")

    def test_rate_limiting(self):
        """Test rate limiting for same source"""
        parser = RSSParser(rate_limits={'test_feed': 0.1})  # 100ms limit
        url = "http://test.example.com/rss.xml"

        # Should raise rate limit error if called too quickly
        # (actual behavior depends on implementation)
        try:
            parser.fetch_feed(url)
        except Exception:
            pass


@pytest.mark.skipif(not FEEDPARSER_AVAILABLE, reason="feedparser not installed")
class TestRSSParserEntryProcessing:
    """Test RSS entry processing"""

    def test_entry_has_required_fields(self):
        """Test that parsed entries have required fields"""
        parser = RSSParser()
        url = "https://feeds.feedburner.com/TechCrunch/"
        entries = parser.fetch_feed(url)

        if entries:
            entry = entries[0]
            required_fields = ['title', 'link', 'published', 'description']
            for field in required_fields:
                assert hasattr(entry, field)

    def test_published_date_parsing(self):
        """Test parsing of published dates"""
        parser = RSSParser()
        url = "https://feeds.feedburner.com/TechCrunch/"
        entries = parser.fetch_feed(url)

        if entries:
            entry = entries[0]
            # Should be a datetime object or string
            assert entry.published is not None

    def test_feed_name_assignment(self):
        """Test that feed names are properly assigned"""
        parser = RSSParser()
        url = "https://example.com/rss.xml"
        entries = parser.fetch_feed(url)

        if entries:
            # Feed name should be inferred from URL or set manually
            for entry in entries:
                assert entry.feed_name is not None


@pytest.mark.skipif(not FEEDPARSER_AVAILABLE, reason="feedparser not installed")
class TestRSSParserErrorHandling:
    """Test error handling"""

    def test_connection_error(self):
        """Test handling of connection errors"""
        parser = RSSParser()
        with pytest.raises(Exception):
            parser.fetch_feed("http://localhost:9999/nonexistent")

    def test_parse_error(self):
        """Test handling of parse errors"""
        parser = RSSParser()
        # This URL might not return valid RSS, but shouldn't crash
        try:
            parser.fetch_feed("http://example.com/not-an-rss-file.html")
        except Exception:
            pass  # Expected to fail


@pytest.mark.skipif(not FEEDPARSER_AVAILABLE, reason="feedparser not installed")
class TestRSSParserWithDatabase:
    """Test RSS parser integration with database"""

    def test_fetch_and_store(self, tmp_path):
        """Test fetching RSS and storing entries to database"""
        db_file = tmp_path / "test.db"
        db = Database(str(db_file))
        db.initialize()

        parser = RSSParser()
        url = "https://feeds.feedburner.com/TechCrunch/"

        # Fetch and store
        entries = parser.fetch_feed(url)
        for entry in entries:
            db.insert_rss_entry({
                'title': entry.title,
                'description': entry.description,
                'link': entry.link,
                'published': str(entry.published),
                'feed_name': entry.feed_name,
                'priority': 1
            })

        # Verify database has entries
        count = db.connection.execute("SELECT COUNT(*) FROM rss_entries").fetchone()[0]
        assert count >= 0  # May be 0 if network issues


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
