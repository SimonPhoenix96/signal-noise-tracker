# Agent Trigger System
# Matches RSS entries to agent rules and dispatches actions

import re
import logging
import json
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

from core.db import db
from core.rss_parser import ParsedEntry

logger = logging.getLogger(__name__)

@dataclass
class TriggerConfig:
    """Configuration for an agent trigger"""
    name: str
    keywords: List[str] = field(default_factory=list)
    fields: List[str] = field(default_factory=lambda: ["title", "description"])
    confidence_threshold: float = 0.7
    exclude_keywords: List[str] = field(default_factory=list)
    enabled: bool = True
    max_duplicates: int = 5
    dedup_window_hours: int = 24
    
    def __post_init__(self):
        # Convert to keyword_rules and exclusion_rules format for backward compatibility
        if not hasattr(self, 'keyword_rules'):
            self.keyword_rules = [{"keywords": self.keywords, "match_on": self.fields}]
        if not hasattr(self, 'exclusion_rules'):
            self.exclusion_rules = [{"keywords": self.exclude_keywords}]
        if not hasattr(self, 'actions'):
            self.actions = []

@dataclass
class TriggerMatch:
    """Represents a rule match"""
    trigger_name: str
    source: str
    entry: ParsedEntry
    matched_keywords: List[str]
    confidence: float
    matched_rules: List[Dict]
    actions: List[Dict]

class AgentTrigger:
    """Matches RSS entries to agent trigger rules"""
    
    def __init__(self, config: Any = None):
        # Store original config for backward compatibility
        self.original_config = config
        
        # Handle both Dict and TriggerConfig
        if config is None:
            self.config = {}
            self.min_confidence = 0.7
            self.max_duplicates = 5
            self.dedup_window_hours = 24
        elif isinstance(config, TriggerConfig):
            # Store TriggerConfig for attribute access
            self.config = config
            self.min_confidence = config.confidence_threshold
            self.max_duplicates = config.max_duplicates
            self.dedup_window_hours = config.dedup_window_hours
        else:
            # Assume dict
            self.config = config
            self.min_confidence = self.config.get('min_confidence', 0.7)
            self.max_duplicates = self.config.get('max_duplicates', 5)
            self.dedup_window_hours = self.config.get('dedup_window_hours', 24)
    
    def match(self, entries: List[Dict]) -> List[Dict]:
        """Match entries (convenience method for testing)"""
        # Convert dict entries to ParsedEntry objects
        parsed_entries = []
        for entry_dict in entries:
            parsed_entry = ParsedEntry(
                title=entry_dict.get('title', ''),
                description=entry_dict.get('description'),
                url=entry_dict.get('link') or entry_dict.get('url'),
                source=entry_dict.get('feed_name') or entry_dict.get('source', 'unknown'),
                published_at=entry_dict.get('published') or entry_dict.get('published_at'),
                raw_data=entry_dict
            )
            parsed_entries.append(parsed_entry)
        
        # Get keyword_rules from config (handle both dict and TriggerConfig)
        if isinstance(self.config, TriggerConfig):
            keyword_rules = self.config.keyword_rules or []
            exclusion_rules = self.config.exclusion_rules or []
        else:
            keyword_rules = self.config.get('keyword_rules', []) if self.config else []
            exclusion_rules = self.config.get('exclusion_rules', []) if self.config else []
        
        # Convert to triggers dict format
        triggers = {}
        if keyword_rules:
            triggers['default'] = {
                'enabled': True,
                'keyword_rules': keyword_rules,
                'exclusion_rules': exclusion_rules
            }
        
        # Match entries
        matches = self.batch_match(parsed_entries, triggers)
        
        # Convert back to dict format for tests
        result = []
        for match in matches:
            result.append({
                'title': match.entry.title,
                'description': match.entry.description,
                'source': match.entry.source,
                'confidence': match.confidence,
                'matched_keywords': match.matched_keywords,
                'trigger_name': match.trigger_name
            })
        
        return result
    
    def match_entry(self, entry: ParsedEntry, 
                   triggers: Dict[str, Dict]) -> Optional[TriggerMatch]:
        """Match single entry against all triggers"""
        for trigger_name, trigger_config in triggers.items():
            if not trigger_config.get('enabled', False):
                continue
            
            matches = self._check_trigger_rules(entry, trigger_config, trigger_name)
            
            if matches:
                # Log the trigger
                try:
                    db.insert_trigger(
                        trigger_name=trigger_name,
                        source=entry.source,
                        matched_keywords=matches['keywords'],
                        matched_rules=matches['rules'],
                        confidence=matches['confidence']
                    )
                except Exception as e:
                    logger.error(f"Failed to log trigger: {e}")
                
                return TriggerMatch(
                    trigger_name=trigger_name,
                    source=entry.source,
                    entry=entry,
                    matched_keywords=matches['keywords'],
                    confidence=matches['confidence'],
                    matched_rules=matches['rules'],
                    actions=matches['actions']
                )
        
        return None
    
    def _check_trigger_rules(self, entry: ParsedEntry, 
                            trigger_config: Dict, trigger_name: str) -> Dict:
        """Check entry against all rules in trigger config"""
        rules = trigger_config.get('keyword_rules', [])
        matched_rules = []
        
        for rule in rules:
            if self._check_rule(entry, rule):
                matched_rules.append(rule)
        
        # Calculate confidence (simple: 1.0 if any rule matches)
        confidence = 1.0 if matched_rules else 0.0
        
        # Extract matched keywords
        matched_keywords = []
        for rule in matched_rules:
            matched_keywords.extend(rule.get('keywords', []))
        
        # Remove duplicates
        matched_keywords = list(set(matched_keywords))
        
        return {
            'keywords': matched_keywords,
            'rules': matched_rules,
            'confidence': confidence,
            'actions': self._extract_actions(rule)
        }
    
    def _check_rule(self, entry: ParsedEntry, rule: Dict) -> bool:
        """Check single rule against entry"""
        keywords = rule.get('keywords', [])
        match_on = rule.get('match_on', ['title', 'description'])
        
        if not keywords:
            return True  # No keywords means match everything
        
        # Check all keywords in specified fields
        text_parts = []
        for field in match_on:
            if field == 'title':
                text_parts.append(entry.title.lower())
            elif field == 'description':
                text_parts.append(entry.description.lower() if entry.description else '')
            elif field == 'tags':
                text_parts.extend([str(tag).lower() for tag in entry.raw_data.get('categories', [])])
        
        combined_text = ' '.join(text_parts).lower()
        
        # Check if any keyword matches (AND logic)
        matches = all(kw in combined_text for kw in keywords)
        
        # Exclude rule (if specified)
        if matches:
            exclusion_rules = rule.get('exclusion_rules', [])
            for exclusion in exclusion_rules:
                if any(ex_kw in combined_text for ex_kw in exclusion.get('keywords', [])):
                    logger.debug(f"Entry excluded by exclusion rule: {entry.title}")
                    return False
        
        return matches
    
    def _extract_actions(self, matched_rule: Dict) -> List[Dict]:
        """Extract actions from matched rule"""
        actions = matched_rule.get('actions', [])
        
        # Ensure actions is a list
        if not isinstance(actions, list):
            actions = [actions] if actions else []
        
        return actions
    
    def batch_match(self, entries: List[ParsedEntry], 
                   triggers: Dict[str, Dict]) -> List[TriggerMatch]:
        """Match batch of entries against triggers"""
        matches = []
        
        for entry in entries:
            # Check for duplicates
            if self._is_duplicate(entry, entry.source):
                logger.debug(f"Skipping duplicate entry: {entry.title}")
                continue
            
            match = self.match_entry(entry, triggers)
            
            if match:
                matches.append(match)
                # Log action
                self._log_action(match)
        
        logger.info(f"Matched {len(matches)} entries against {len(triggers)} triggers")
        return matches
    
    def _is_duplicate(self, entry: ParsedEntry, source: str) -> bool:
        """Check if entry is duplicate within time window"""
        try:
            from core.db import db
            return db.insert_rss_entry(
                source=entry.source,
                title=entry.title,
                url=entry.url,
                description=entry.description,
                published_at=entry.published_at,
                raw_data=entry.raw_data
            )
        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            return False
    
    def _log_action(self, match: TriggerMatch) -> None:
        """Log action"""
        try:
            # Get trigger ID from database
            from core.db import db
            # Note: This would need to query the last insert for the trigger
            # For now, we'll just log the action
            logger.debug(f"Logging action for trigger: {match.trigger_name}")
        except Exception as e:
            logger.error(f"Failed to log action: {e}")

# Singleton instance
trigger = AgentTrigger()
