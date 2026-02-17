"""
Item Filter

Applies filtering rules to RSS feed items before processing.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import re

from .parser import FeedItem
from ..logger import get_logger

logger = get_logger(__name__)


class ItemFilter:
    """Filters RSS feed items based on rules"""

    def __init__(self, config: Dict[str, Any]):
        self.config: Dict[str, Any] = config
        logger.info("ItemFilter initialized")

    def filter(self, items: List[FeedItem]) -> List[FeedItem]:
        """
        Apply filter rules to items

        Args:
            items: List of feed items to filter

        Returns:
            Filtered list of items
        """
        filtered: List[FeedItem] = items.copy()

        # Filter by age
        filtered = self._filter_by_age(filtered)

        # Filter by required tags
        filtered = self._filter_by_required_tags(filtered)

        # Filter by excluded tags
        filtered = self._filter_by_excluded_tags(filtered)

        # Filter by regex patterns
        filtered = self._filter_by_patterns(filtered)

        logger.info(f"Filtered {len(items)} -> {len(filtered)} items")
        return filtered

    def _filter_by_age(self, items: List[FeedItem]) -> List[FeedItem]:
        """Filter out items older than max_age_days"""
        max_age_days = self.config.get("max_age_days", 30)
        if max_age_days <= 0:
            return items

        cutoff = datetime.utcnow() - timedelta(days=max_age_days)
        filtered: List[FeedItem] = [item for item in items if item.published >= cutoff]

        if len(filtered) != len(items):
            logger.debug(f"Filtered {len(items) - len(filtered)} old items (> {max_age_days} days)")

        return filtered

    def _filter_by_required_tags(self, items: List[FeedItem]) -> List[FeedItem]:
        """Only include items that have all required tags"""
        required_tags: List[str] = self.config.get("required_tags", [])
        if not required_tags:
            return items

        filtered: List[FeedItem] = []
        for item in items:
            if all(tag in item.tags for tag in required_tags):
                filtered.append(item)

        if len(filtered) != len(items):
            logger.debug(f"Filtered {len(items) - len(filtered)} items (missing required tags)")

        return filtered

    def _filter_by_excluded_tags(self, items: List[FeedItem]) -> List[FeedItem]:
        """Exclude items with excluded tags"""
        exclude_tags: List[str] = self.config.get("exclude_tags", [])
        if not exclude_tags:
            return items

        filtered: List[FeedItem] = [
            item for item in items
            if not any(tag in exclude_tags for tag in item.tags)
        ]

        if len(filtered) != len(items):
            logger.debug(f"Filtered {len(items) - len(filtered)} items (excluded tags)")

        return filtered

    def _filter_by_patterns(self, items: List[FeedItem]) -> List[FeedItem]:
        """Filter by regex patterns in title/description"""
        include_patterns: List[str] = self.config.get("include_patterns", [])
        exclude_patterns: List[str] = self.config.get("exclude_patterns", [])

        filtered: List[FeedItem] = items.copy()

        if include_patterns:
            pattern_list = [re.compile(p, re.IGNORECASE) for p in include_patterns]
            filtered = [
                item for item in filtered
                if any(pattern.search(item.title) or pattern.search(item.description)
                       for pattern in pattern_list)
            ]

        if exclude_patterns:
            pattern_list = [re.compile(p, re.IGNORECASE) for p in exclude_patterns]
            filtered = [
                item for item in filtered
                if not any(pattern.search(item.title) or pattern.search(item.description)
                           for pattern in pattern_list)
            ]

        if len(filtered) != len(items):
            logger.debug(f"Filtered {len(items) - len(filtered)} items (pattern matching)")

        return filtered
