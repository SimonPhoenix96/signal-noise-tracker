"""
RSS Feed Parser

Parses RSS/Atom feeds and extracts items with metadata.
"""

import feedparser
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

from ..logger import get_logger

logger = get_logger(__name__)


@dataclass
class FeedItem:
    """Represents a single RSS feed item"""
    id: str
    title: str
    description: str
    link: str
    published: datetime
    updated: datetime
    tags: List[str]
    raw_data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class FeedParser:
    """Parses RSS/Atom feeds"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        logger.info(f"FeedParser initialized (timeout={timeout}s)")

    def parse(self, feed_url: str) -> List[FeedItem]:
        """
        Parse an RSS feed and return items

        Args:
            feed_url: URL of the RSS feed

        Returns:
            List of FeedItem objects
        """
        try:
            logger.info(f"Parsing feed: {feed_url}")

            feed = feedparser.parse(
                feed_url,
                timeout=self.timeout,
                headers={"User-Agent": "Cronjob-Money-MVP/1.0"}
            )

            if feed.bozo:
                logger.warning(f"Feed has parse warnings: {feed.bozo_exception}")

            items = []
            for entry in feed.entries:
                item = self._parse_entry(entry, feed)
                if item:
                    items.append(item)

            logger.info(f"Parsed {len(items)} items from {feed_url}")
            return items

        except Exception as e:
            logger.error(f"Failed to parse feed {feed_url}: {e}")
            raise

    def _parse_entry(self, entry, feed) -> FeedItem:
        """Parse a single feed entry"""
        try:
            # Extract published date
            published = self._parse_date(entry.get("published_parsed"))
            updated = self._parse_date(entry.get("updated_parsed", published))

            # Extract tags
            tags = self._extract_tags(entry, feed)

            # Create feed item
            item = FeedItem(
                id=self._generate_id(entry.get("id") or entry.get("link")),
                title=self._clean_text(entry.get("title", "")),
                description=self._clean_text(entry.get("summary", entry.get("description", ""))),
                link=entry.get("link", ""),
                published=published,
                updated=updated,
                tags=tags,
                raw_data=self._serialize_entry(entry)
            )

            return item

        except Exception as e:
            logger.warning(f"Failed to parse entry: {e}")
            return None

    def _parse_date(self, date_obj) -> datetime:
        """Parse a feedparser date object to datetime"""
        if isinstance(date_obj, datetime):
            return date_obj
        elif date_obj:
            return datetime(*date_obj[:6])
        else:
            return datetime.utcnow()

    def _extract_tags(self, entry, feed) -> List[str]:
        """Extract tags from entry and feed"""
        tags = []

        # Extract tags from categories
        if hasattr(entry, "tags"):
            tags.extend([tag.term for tag in entry.tags if hasattr(tag, "term")])

        # Extract tags from enclosure
        if hasattr(entry, "enclosures"):
            tags.extend(["audio", "video"])

        # Add feed-specific tag
        tags.append(feed.get("title", "")[:50])

        return list(set(tags))

    def _generate_id(self, identifier: str) -> str:
        """Generate a stable ID from a feed identifier"""
        return f"{identifier}_{datetime.now().timestamp()}"

    def _clean_text(self, text: str) -> str:
        """Clean and truncate text"""
        if not text:
            return ""

        # Remove HTML tags
        import re
        text = re.sub(r'<[^>]+>', '', text)

        # Decode HTML entities
        import html
        text = html.unescape(text)

        # Strip whitespace
        text = text.strip()

        # Truncate if too long
        if len(text) > 500:
            text = text[:500] + "..."

        return text

    def _serialize_entry(self, entry) -> Dict[str, Any]:
        """Serialize entry to dict (keep for debugging)"""
        return {
            "id": entry.get("id"),
            "title": entry.get("title"),
            "link": entry.get("link"),
            "published": entry.get("published_parsed"),
            "updated": entry.get("updated_parsed"),
        }
