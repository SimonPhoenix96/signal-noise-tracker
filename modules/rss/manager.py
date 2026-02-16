"""
Feed Manager

Manages multiple RSS feeds, state, and ingestion pipeline.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

from .parser import FeedParser, FeedItem
from .filter import ItemFilter
from ..logger import get_logger

logger = get_logger(__name__)


class FeedManager:
    """Manages RSS feeds and state"""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.state_file = self.data_dir / "state.json"
        self.parser = FeedParser()
        self.state: Dict[str, datetime] = {}

        # Load existing state
        self._load_state()

        logger.info(f"FeedManager initialized (state_file={self.state_file})")

    def load_feeds(self, config: Dict[str, List[Dict]]) -> List[Dict]:
        """Load feed configurations"""
        feeds = config.get("feeds", [])
        logger.info(f"Loaded {len(feeds)} feed configurations")

        # Add state to each feed
        for feed in feeds:
            feed_id = feed.get("id")
            if feed_id and feed_id in self.state:
                feed["last_read"] = self.state[feed_id]
            else:
                feed["last_read"] = datetime.utcnow()

        return feeds

    def ingest_feeds(self, feeds_config: List[Dict]) -> List[FeedItem]:
        """
        Ingest all enabled feeds and return new items

        Args:
            feeds_config: Feed configurations

        Returns:
            List of new feed items
        """
        new_items = []
        all_items = []

        for feed_config in feeds_config:
            feed_id = feed_config.get("id")
            url = feed_config.get("url")

            if not feed_id or not url:
                logger.warning(f"Invalid feed config: {feed_config}")
                continue

            if not feed_config.get("enabled", False):
                logger.debug(f"Skipping disabled feed: {feed_id}")
                continue

            try:
                # Parse feed
                items = self.parser.parse(url)

                # Apply filters
                filter_config = feed_config.get("filter_rules", {})
                filter_obj = ItemFilter(filter_config)
                filtered_items = filter_obj.filter(items)

                all_items.extend(filtered_items)

                # Filter new items (not read since last_read)
                last_read = feed_config.get("last_read", datetime.utcnow())
                new_items = [
                    item for item in filtered_items
                    if item.published > last_read
                ]

                # Update last read position
                if new_items:
                    latest_item = max(new_items, key=lambda x: x.published)
                    self.state[feed_id] = latest_item.published
                    logger.info(f"Updated last_read for {feed_id}")

            except Exception as e:
                logger.error(f"Failed to ingest feed {feed_id}: {e}")
                continue

        # Save state
        self._save_state()

        return new_items

    def get_new_items(self, feed_id: str, feed_config: Dict) -> List[FeedItem]:
        """
        Get new items for a specific feed

        Args:
            feed_id: Feed ID
            feed_config: Feed configuration

        Returns:
            List of new feed items
        """
        url = feed_config.get("url")
        if not url:
            return []

        try:
            items = self.parser.parse(url)

            filter_config = feed_config.get("filter_rules", {})
            filter_obj = ItemFilter(filter_config)
            filtered_items = filter_obj.filter(items)

            last_read = feed_config.get("last_read", datetime.utcnow())
            new_items = [
                item for item in filtered_items
                if item.published > last_read
            ]

            # Update last read position
            if new_items:
                latest_item = max(new_items, key=lambda x: x.published)
                self.state[feed_id] = latest_item.published
                self._save_state()

            return new_items

        except Exception as e:
            logger.error(f"Failed to get new items for {feed_id}: {e}")
            return []

    def _load_state(self):
        """Load state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    self.state = json.load(f)
                logger.info(f"Loaded state with {len(self.state)} feeds")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
                self.state = {}
        else:
            logger.debug("No state file found, starting fresh")
            self.state = {}

    def _save_state(self):
        """Save state to file"""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2)
            logger.debug("State saved")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
