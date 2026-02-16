"""
Unit tests for Agent Triggers
"""

import pytest
import json
from datetime import datetime
from pathlib import Path

from modules.triggers import TriggerManager


class TestTriggerManager:
    """Test Trigger Manager"""

    def test_initialization(self, tmp_path):
        """Test trigger manager initialization"""
        config = {}
        manager = TriggerManager(config, data_dir=str(tmp_path))
        assert manager.config == config
        assert manager.queue == []

    def test_load_agents(self):
        """Test loading agent configurations"""
        config = {
            "agents": [
                {"id": "agent1", "name": "Agent 1", "feeds": ["feed1"]},
                {"id": "agent2", "name": "Agent 2", "feeds": ["feed2"]},
            ]
        }

        manager = TriggerManager({}, data_dir="./data")
        agents = manager.load_agents(config)

        assert len(agents) == 2
        assert agents[0]["id"] == "agent1"
        assert agents[1]["id"] == "agent2"
        assert "queue_id" in agents[0]

    def test_should_trigger(self, tmp_path, monkeypatch):
        """Test should_trigger logic"""
        # Create a fake feed state
        feed_state = {
            "feed1": {"has_new_items": True},
            "feed2": {"has_new_items": False},
        }
        state_file = tmp_path / "feed_state.json"
        with open(state_file, "w") as f:
            json.dump(feed_state, f)

        config = {
            "agents": [
                {"id": "agent1", "name": "Agent 1", "feeds": ["feed1"], "enabled": True},
                {"id": "agent2", "name": "Agent 2", "feeds": ["feed2"], "enabled": True},
            ]
        }

        manager = TriggerManager(config, data_dir=str(tmp_path))
        manager.queue_file = tmp_path / "trigger_queue.json"

        # Agent1 should trigger (feed has items)
        should_trigger_1 = manager.should_trigger(config["agents"][0])
        assert should_trigger_1 is True

        # Agent2 should NOT trigger (feed has no items)
        should_trigger_2 = manager.should_trigger(config["agents"][1])
        assert should_trigger_2 is False

        # Disabled agent should not trigger
        agent_disabled = config["agents"][0].copy()
        agent_disabled["enabled"] = False
        should_trigger_disabled = manager.should_trigger(agent_disabled)
        assert should_trigger_disabled is False

    def test_trigger_agent(self, tmp_path):
        """Test triggering an agent"""
        config = {
            "agents": [
                {"id": "agent1", "name": "Agent 1"},
            ]
        }

        manager = TriggerManager(config, data_dir=str(tmp_path))
        manager.queue_file = tmp_path / "trigger_queue.json"

        items = [
            {"id": "1", "title": "Item 1"},
            {"id": "2", "title": "Item 2"},
        ]

        triggered = manager.trigger_agent(config["agents"][0], items)
        assert triggered is True

        # Check queue
        status = manager.get_queue_status()
        assert status["total_tasks"] == 1
        assert status["queue"][0]["agent_id"] == "agent1"

    def test_get_next_task(self, tmp_path):
        """Test getting next task from queue"""
        config = {
            "agents": [
                {"id": "agent1", "name": "Agent 1"},
                {"id": "agent2", "name": "Agent 2"},
            ]
        }

        manager = TriggerManager(config, data_dir=str(tmp_path))
        manager.queue_file = tmp_path / "trigger_queue.json"

        # Add tasks
        manager.trigger_agent(config["agents"][0], items=[{"id": "1"}])
        manager.trigger_agent(config["agents"][1], items=[{"id": "2"}])

        # Get first task
        task = manager.get_next_task()
        assert task is not None
        assert task["agent_id"] == "agent1"

        # Check queue is updated
        status = manager.get_queue_status()
        assert status["total_tasks"] == 1

        # Get second task
        task = manager.get_next_task()
        assert task is not None
        assert task["agent_id"] == "agent2"

        # Queue should be empty
        task = manager.get_next_task()
        assert task is None

    def test_clear_queue(self, tmp_path):
        """Test clearing the queue"""
        config = {
            "agents": [
                {"id": "agent1", "name": "Agent 1"},
            ]
        }

        manager = TriggerManager(config, data_dir=str(tmp_path))
        manager.queue_file = tmp_path / "trigger_queue.json"

        # Add task
        manager.trigger_agent(config["agents"][0], items=[{"id": "1"}])

        # Clear queue
        manager.clear_queue()

        status = manager.get_queue_status()
        assert status["total_tasks"] == 0
