"""
Cron Runner

Main cron scheduler that coordinates RSS ingestion and agent triggering.
"""

import sys
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.logger import setup_logging, get_logger
from modules.config import ConfigManager
from modules.triggers import TriggerManager
from modules.logger import get_logger as get_logger_func

logger = get_logger(__name__)


class CronRunner:
    """Main cron scheduler"""

    def __init__(self, env: str = "development", dev_mode: bool = False):
        self.env: str = env
        self.dev_mode: bool = dev_mode

        # Setup logging
        log_level = "DEBUG" if dev_mode else "INFO"
        setup_logging(log_level=log_level, json_format=True)

        logger.info("CronRunner initialized", env=env, dev_mode=dev_mode)

        # Load configurations
        self.config_mgr: ConfigManager = ConfigManager()
        self.triggers: TriggerManager = TriggerManager({}, data_dir="./data")

    def run_once(self) -> None:
        """Run a single cron cycle"""
        logger.info("=" * 50, action="cron_cycle_start")
        start_time = datetime.utcnow()

        try:
            # Step 1: Load configurations
            logger.info("Loading configurations...")
            feeds_config: Dict[str, Any] = self.config_mgr.load_config("feeds", required=False) or {"feeds": []}
            agents_config: Dict[str, Any] = self.config_mgr.load_config("agents", required=False) or {"agents": []}

            # Step 2: Run triggers
            logger.info("Running triggers...")
            self.triggers.load_agents(agents_config)

            for agent in agents_config:
                if self.triggers.should_trigger(agent):
                    logger.info(f"Triggering agent: {agent.get('name')}")
                    self.triggers.trigger_agent(agent, items=[])
                else:
                    logger.debug(f"Skipping agent: {agent.get('name')}")

            # Step 3: Get queue status
            status: Dict[str, Any] = self.triggers.get_queue_status()
            logger.info(f"Queue status: {status['total_tasks']} tasks queued")

            # Step 4: Process queue
            logger.info("Processing queue...")
            while True:
                task: Optional[Dict[str, Any]] = self.triggers.get_next_task()
                if not task:
                    break

                self._process_task(task)

        except Exception as e:
            logger.error(f"Cron cycle failed: {e}", exc_info=True)

        end_time = datetime.utcnow()
        duration: float = (end_time - start_time).total_seconds()
        logger.info("cron_cycle_end", duration_seconds=round(duration, 2))

    def run_loop(self, interval_seconds: int = 60) -> None:
        """Run cron in a loop (for development)"""
        logger.info("Starting cron loop", interval_seconds=interval_seconds)

        while True:
            self.run_once()
            logger.info("Sleeping...", interval_seconds=interval_seconds)
            time.sleep(interval_seconds)

    def _process_task(self, task: Dict[str, Any]) -> None:
        """Process a single task from the queue"""
        agent_id: Optional[str] = task.get("agent_id")
        agent_name: Optional[str] = task.get("agent_name")
        items: List[Dict[str, Any]] = task.get("items", [])
        config: Dict[str, Any] = task.get("config", {})

        logger.info(
            "Processing task",
            agent_id=agent_id,
            agent_name=agent_name,
            item_count=len(items)
        )

        # Here you would call specific agent handlers
        # For now, just log what would happen
        logger.info(
            "Agent would process items",
            agent_name=agent_name,
            item_count=len(items),
            agent_config=config
        )


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Cronjob Money-MVP")
    parser.add_argument("--env", default="development", help="Environment (development/production)")
    parser.add_argument("--dev", action="store_true", help="Development mode (run every minute)")
    parser.add_argument("--once", action="store_true", help="Run once and exit")

    args = parser.parse_args()

    runner = CronRunner(env=args.env, dev_mode=args.dev)

    if args.once:
        runner.run_once()
    else:
        if args.dev:
            runner.run_loop(interval_seconds=60)
        else:
            # In production, this would be run by cron
            # For now, just run once
            runner.run_once()
            logger.info("Cron cycle completed. Set up cron to run every 4 hours.")


if __name__ == "__main__":
    main()
