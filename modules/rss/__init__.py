"""
RSS Ingestion Module

Parses RSS feeds, validates items, applies filters, and manages state.
"""

from .parser import FeedParser
from .filter import ItemFilter
from .manager import FeedManager

__all__ = ["FeedParser", "ItemFilter", "FeedManager"]
