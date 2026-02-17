"""
Trigger Manager

Manages agent execution queue and triggers based on configuration.
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from queue import Queue, Empty
from threading import Thread, Lock
import time

from ..logger import get_logger

logger = get_logger(__name__)


class TriggerManager:
    """Manages agent triggers and execution"""

    def __init__(self, config: Dict[str, Any], data_dir: str = "./data"):
        self.config: Dict[str, Any] = config
        self.data_dir: Path = Path(data_dir)
        self.queue_file: Path = self.data_dir / "trigger_queue.json"
        self.queue: List[Dict[str, Any]] = []
        self.lock: Lock = Lock()

        # Load existing queue
        self._load_queue()

        logger.info("TriggerManager initialized")

    def load_agents(self, config: Dict[str, List[Dict]]) -> List[Dict]:
        """Load agent configurations"""
        agents: List[Dict] = config.get("agents", [])
        logger.info(f"Loaded {len(agents)} agent configurations")

        # Add queue ID to each agent
        for agent in agents:
            agent_id: Optional[str] = agent.get("id")
            if agent_id:
                agent["queue_id"] = agent_id

        return agents

    def should_trigger(self, agent_config: Dict) -> bool:
        """
        Determine if an agent should be triggered

        Args:
            agent_config: Agent configuration

        Returns:
            True if agent should be triggered
        """
        # Check if enabled
        if not agent_config.get("enabled", False):
            return False

        # Check if feeds have items
        feeds: List[str] = agent_config.get("feeds", [])
        if not feeds:
            logger.debug(f"Agent {agent_config.get('id')} has no feeds")
            return False

        # Check minimum items threshold
        min_items: int = agent_config.get("trigger", {}).get("min_items", 1)
        if min_items <= 0:
            return True

        # Check if feeds have enough items
        has_enough_items: bool = self._has_feeds_with_items(feeds)
        if not has_enough_items:
            logger.debug(f"Agent {agent_config.get('id')}: feeds don't have enough items")
            return False

        return True

    def trigger_agent(self, agent_config: Dict, items: List[Dict]) -> bool:
        """
        Trigger an agent with items

        Args:
            agent_config: Agent configuration
            items: Items to process

        Returns:
            True if agent was triggered
        """
        agent_id: Optional[str] = agent_config.get("id")
        agent_name: Optional[str] = agent_config.get("name")

        # Add to queue
        with self.lock:
            queue_entry: Dict[str, Any] = {
                "agent_id": agent_id,
                "agent_name": agent_name,
                "items": items,
                "timestamp": datetime.utcnow().isoformat(),
                "config": agent_config.get("config", {})
            }

            self.queue.append(queue_entry)

            # Update queue file
            self._save_queue()

            logger.info(f"Queued agent {agent_name} ({len(items)} items)")

        return True

    def _has_feeds_with_items(self, feed_ids: List[str]) -> bool:
        """Check if any of the specified feeds have new items"""
        # Load feed state
        state_file: Path = self.data_dir / "feed_state.json"
        if not state_file.exists():
            return False

        try:
            with open(state_file, "r") as f:
                feed_state: Dict[str, Any] = json.load(f)

            # Check if any feed has items
            for feed_id in feed_ids:
                if feed_id in feed_state and feed_state[feed_id].get("has_new_items", False):
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to check feed state: {e}")
            return False

    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """
        Get the next task from the queue

        Returns:
            Task dictionary or None if queue is empty
        """
        with self.lock:
            if not self.queue:
                return None

            task: Dict[str, Any] = self.queue.pop(0)
            self._save_queue()

            logger.info(f"Retrieved task: {task['agent_name']}")
            return task

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            "total_tasks": len(self.queue),
            "queue": self.queue,
            "timestamp": datetime.utcnow().isoformat()
        }

    def clear_queue(self) -> None:
        """Clear all items from queue"""
        with self.lock:
            self.queue = []
            self._save_queue()
            logger.info("Queue cleared")

    def _load_queue(self) -> None:
        """Load queue from file"""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, "r") as f:
                    self.queue = json.load(f)
                logger.info(f"Loaded queue with {len(self.queue)} tasks")
            except Exception as e:
                logger.error(f"Failed to load queue: {e}")
                self.queue = []
        else:
            logger.debug("No queue file found")
            self.queue = []

    def _save_queue(self) -> None:
        """Save queue to file"""
        try:
            self.queue_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.queue_file, "w") as f:
                json.dump(self.queue, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save queue: {e}")
