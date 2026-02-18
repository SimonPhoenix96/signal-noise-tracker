# RSS Parser Module
# Fetches and parses RSS/Atom feeds

import feedparser
import requests
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

@dataclass
class ParsedEntry:
    """Represents a parsed RSS entry"""
    title: str
    url: str
    description: str
    published_at: str
    source: str
    raw_data: Dict

class RSSParser:
    """RSS/Atom feed parser"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Cronjob-Money-MVP/1.0 (+https://github.com/openclaw/cronjob)'
        })
    
    def fetch_feed(self, source_name: str, feed_url: str, max_items: int = 100) -> List[ParsedEntry]:
        """Fetch and parse RSS feed"""
        entries = []
        
        try:
            logger.info(f"Fetching feed: {source_name} - {feed_url}")
            
            # Add rate limiting
            rate_limit = self.config.get('rate_limit', 30)
            time.sleep(rate_limit)
            
            # Fetch feed
            response = self.session.get(feed_url, timeout=30)
            response.raise_for_status()
            
            # Parse with feedparser
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                logger.warning(f"Feed parsing warning for {source_name}: {feed.bozo_exception}")
            
            # Extract entries
            for entry in feed.entries[:max_items]:
                parsed = self._parse_entry(entry, source_name)
                if parsed:
                    entries.append(parsed)
                    logger.debug(f"Parsed entry: {parsed.title}")
            
            logger.info(f"Fetched {len(entries)} entries from {source_name}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {source_name}: {e}")
        except Exception as e:
            logger.error(f"Error parsing {source_name}: {e}")
        
        return entries
    
    def _parse_entry(self, entry, source: str) -> Optional[ParsedEntry]:
        """Parse individual feed entry"""
        try:
            # Handle both RSS and Atom formats
            title = entry.get('title', '')
            link = entry.get('link', '')
            description = entry.get('description', '')
            
            # Parse published timestamp
            published_at = entry.get('published', '')
            if not published_at:
                published_at = entry.get('updated', '')
            
            # Normalize timestamp
            if published_at:
                try:
                    # feedparser already parses, but ensure ISO format
                    published_at = published_at.isoformat() if hasattr(published_at, 'isoformat') else published_at
                except:
                    published_at = datetime.utcnow().isoformat()
            
            # Get raw entry data
            raw_data = {
                'author': entry.get('author', ''),
                'categories': entry.get('tags', []),
                'guid': entry.get('id', ''),
                'links': entry.get('links', []),
                'enclosures': entry.get('enclosures', [])
            }
            
            return ParsedEntry(
                title=title.strip(),
                url=link.strip(),
                description=description.strip(),
                published_at=published_at,
                source=source,
                raw_data=raw_data
            )
        except Exception as e:
            logger.error(f"Failed to parse entry: {e}")
            return None
    
    def fetch_all_feeds(self, sources: Dict[str, Dict]) -> Dict[str, List[ParsedEntry]]:
        """Fetch all configured feeds"""
        results = {}
        
        for source_name, source_config in sources.items():
            if not source_config.get('enabled', True):
                logger.info(f"Skipping disabled source: {source_name}")
                continue
            
            url = source_config.get('url')
            max_items = source_config.get('max_items', 50)
            
            if not url:
                logger.warning(f"No URL configured for {source_name}")
                continue
            
            entries = self.fetch_feed(source_name, url, max_items)
            results[source_name] = entries
        
        return results
    
    def deduplicate_entries(self, entries: List[ParsedEntry], 
                           source: str, dedup_window_hours: int = 24) -> List[ParsedEntry]:
        """Deduplicate entries within time window"""
        if not entries:
            return []
        
        try:
            from core.db import db
            logger.info(f"Deduplicating {len(entries)} entries for source {source}")
            
            existing_urls = set()
            for entry in entries:
                if db.insert_rss_entry(
                    source=entry.source,
                    title=entry.title,
                    url=entry.url,
                    description=entry.description,
                    published_at=entry.published_at,
                    raw_data=entry.raw_data
                ):
                    existing_urls.add(entry.url)
            
            # Keep only new entries
            new_entries = [e for e in entries if e.url in existing_urls]
            logger.info(f"Kept {len(new_entries)} new entries after deduplication")
            
            return new_entries
        except Exception as e:
            logger.error(f"Deduplication error: {e}")
            return entries

# Singleton instance
parser = RSSParser()
