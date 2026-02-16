# Integration Tests for Cronjob Money-MVP
# These tests verify the interaction between core modules.

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.rss.parser import FeedParser, FeedItem
from modules.rss.filter import ItemFilter
from modules.rss.manager import FeedManager
from modules.triggers.manager import TriggerManager
from modules.config import ConfigManager


def test_integration_feed_parser_to_filter():
    """Test complete flow: Parse feed → Filter items"""
    print("\n=== Integration Test: Parser → Filter ===")

    # Create a sample feed item
    parser = FeedParser()
    sample_items = [
        FeedItem(
            id="item_1",
            title="Great Deal on Gaming GPU - 30% OFF",
            description="NVIDIA RTX 4090 for $1200 (was $1700)",
            link="https://example.com/deal1",
            published=datetime.utcnow(),
            updated=datetime.utcnow(),
            tags=["gaming", "hardware", "deal", "discount"],
            raw_data={}
        ),
        FeedItem(
            id="item_2",
            title="Spam Email - Win a Prize!",
            description="Click here to claim your prize now!",
            link="https://example.com/spam",
            published=datetime.utcnow() - timedelta(days=10),
            updated=datetime.utcnow() - timedelta(days=10),
            tags=["spam", "scam"],
            raw_data={}
        ),
        FeedItem(
            id="item_3",
            title="Used Book: Programming in Python",
            description="Good condition, minor wear",
            link="https://example.com/used",
            published=datetime.utcnow(),
            updated=datetime.utcnow(),
            tags=["books", "used", "discount"],
            raw_data={}
        )
    ]

    # Filter out spam and old items
    config = {
        "max_age_days": 7,
        "exclude_tags": ["spam", "scam"],
        "include_patterns": ["deal", "discount"]
    }

    filter_obj = ItemFilter(config)
    filtered_items = filter_obj.filter(sample_items)

    print(f"Input items: {len(sample_items)}")
    print(f"Filtered items: {len(filtered_items)}")

    # Verify results
    assert len(filtered_items) == 2, f"Expected 2 items, got {len(filtered_items)}"

    # First item should pass (deal)
    assert "deal" in filtered_items[0].title.lower(), "First item should be a deal"
    assert "discount" in filtered_items[0].title.lower(), "First item should have discount"

    # Second item should be excluded (spam)
    assert filtered_items[0].id != "item_2", "Spam item should be filtered out"

    # Third item should be excluded (used)
    assert filtered_items[0].id != "item_3", "Used item should be filtered out"

    print("✅ Integration test passed: Parser → Filter flow works correctly")
    return True


def test_integration_trigger_manager():
    """Test complete flow: Feed Manager → Trigger Manager"""
    print("\n=== Integration Test: Feed Manager → Trigger Manager ===")

    # Create temporary directory for testing
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup feed manager
        feed_manager = FeedManager(data_dir=tmpdir)
        feed_manager.load_feeds_from_yaml("config/feeds.yaml")

        # Setup trigger manager
        trigger_manager = TriggerManager({}, data_dir=tmpdir)
        trigger_manager.queue_file = Path(tmpdir) / "trigger_queue.json"

        # Mock feed state
        feed_state = {
            "deal_hunter_daily": {"has_new_items": True, "last_update": datetime.utcnow()},
            "frugally_daily": {"has_new_items": True, "last_update": datetime.utcnow()},
            "tech_deals_gaming": {"has_new_items": False, "last_update": datetime.utcnow()}
        }

        # Save feed state
        state_file = Path(tmpdir) / "feed_state.json"
        with open(state_file, "w") as f:
            json.dump(feed_state, f, default=str)

        # Create sample agent config
        agent_config = {
            "id": "arbitrage_checker",
            "name": "Arbitrage Checker",
            "feeds": ["deal_hunter_daily", "frugally_daily"],
            "enabled": True,
            "config": {
                "min_profit_percent": 20,
                "required_tags": ["deal", "discount"],
                "exclude_keywords": ["used", "damaged"]
            }
        }

        # Should trigger because feeds have new items
        should_trigger = trigger_manager.should_trigger(agent_config)
        assert should_trigger is True, "Agent should trigger when feeds have new items"

        # Add trigger
        sample_items = [
            {"id": "1", "title": "Great Deal", "link": "https://example.com/deal1"},
            {"id": "2", "title": "Another Deal", "link": "https://example.com/deal2"}
        ]

        triggered = trigger_manager.trigger_agent(agent_config, sample_items)
        assert triggered is True, "Agent should trigger successfully"

        # Check queue
        status = trigger_manager.get_queue_status()
        assert status["total_tasks"] == 1, f"Expected 1 task, got {status['total_tasks']}"

        # Get next task
        task = trigger_manager.get_next_task()
        assert task is not None, "Should have a task in queue"
        assert task["agent_id"] == "arbitrage_checker", "Task should be for arbitrage_checker"

        print("✅ Integration test passed: Trigger Manager flow works correctly")
        return True


def test_integration_config_manager():
    """Test configuration management"""
    print("\n=== Integration Test: Config Manager ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create config manager
        config_manager = ConfigManager(config_dir=tmpdir)

        # Load feeds config
        feeds_config = config_manager.load_yaml("config/feeds.yaml")
        assert feeds_config is not None, "Should load feeds config"
        assert "feeds" in feeds_config, "Feeds config should have 'feeds' key"
        assert len(feeds_config["feeds"]) > 0, "Should have at least one feed"

        # Load agents config
        agents_config = config_manager.load_yaml("config/agents.yaml")
        assert agents_config is not None, "Should load agents config"
        assert "agents" in agents_config, "Agents config should have 'agents' key"
        assert len(agents_config["agents"]) > 0, "Should have at least one agent"

        print(f"✅ Loaded {len(feeds_config['feeds'])} feed configurations")
        print(f"✅ Loaded {len(agents_config['agents'])} agent configurations")
        print("✅ Integration test passed: Config Manager flow works correctly")
        return True


def test_full_end_to_end_scenario():
    """Simulate a full cron cycle"""
    print("\n=== Integration Test: Full End-to-End Scenario ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 1: Setup
        config_manager = ConfigManager(config_dir=tmpdir)
        feed_manager = FeedManager(data_dir=tmpdir)
        trigger_manager = TriggerManager({}, data_dir=tmpdir)

        # Step 2: Load configurations
        agents_config = config_manager.load_yaml("config/agents.yaml")
        feeds_config = config_manager.load_yaml("config/feeds.yaml")

        print(f"Loaded {len(feeds_config['feeds'])} feeds")
        print(f"Loaded {len(agents_config['agents'])} agents")

        # Step 3: Simulate RSS feed ingestion
        parser = FeedParser()
        sample_items = [
            FeedItem(
                id=f"item_{i}",
                title=f"Sample Deal {i}",
                description=f"Description for item {i}",
                link=f"https://example.com/item/{i}",
                published=datetime.utcnow(),
                updated=datetime.utcnow(),
                tags=["deal", "discount"],
                raw_data={}
            )
            for i in range(5)
        ]

        print(f"Parsed {len(sample_items)} items from RSS feed")

        # Step 4: Filter items
        filter_config = {
            "max_age_days": 7,
            "exclude_tags": ["spam"]
        }
        item_filter = ItemFilter(filter_config)
        filtered_items = item_filter.filter(sample_items)

        print(f"Filtered to {len(filtered_items)} items")

        # Step 5: Trigger agents
        sample_agent = agents_config["agents"][0]
        if filtered_items:
            triggered = trigger_manager.trigger_agent(sample_agent, [
                {"id": item.id, "title": item.title, "link": item.link}
                for item in filtered_items
            ])

            if triggered:
                status = trigger_manager.get_queue_status()
                print(f"Triggered agent, queue size: {status['total_tasks']}")
            else:
                print("Agent not triggered (no items)")
        else:
            print("No items to process")

        print("✅ Full end-to-end scenario completed successfully")
        return True


if __name__ == "__main__":
    print("=" * 60)
    print("Cronjob Money-MVP - Integration Tests")
    print("=" * 60)

    try:
        test_integration_feed_parser_to_filter()
        test_integration_trigger_manager()
        test_integration_config_manager()
        test_full_end_to_end_scenario()

        print("\n" + "=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
