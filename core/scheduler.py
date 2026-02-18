# Cron Scheduler
# Schedules and runs RSS feed ingestion and agent triggers

import schedule
import time
import logging
import json
import signal
import sys
from datetime import datetime, time as datetime_time
from typing import Dict, Callable
from pathlib import Path

from core.db import db
from core.rss_parser import parser
from core.agent_trigger import trigger as trigger_system

logger = logging.getLogger(__name__)

class CronScheduler:
    """Main scheduler for cron job"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.scheduler = schedule.Scheduler()
        self.running = False
        self.dry_run = self.config.get('dry_run', False)
        self.start_time = self._parse_time(self.config.get('start_time', '09:00'))
        self.end_time = self._parse_time(self.config.get('end_time', '23:00'))
        
        # Load configuration
        self.sources = self._load_sources()
        self.triggers = self._load_triggers()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _parse_time(self, time_str: str):
        """Parse time string HH:MM"""
        try:
            return datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            logger.warning(f"Invalid time format: {time_str}, using default 09:00")
            return datetime_time(9, 0)
    
    def _load_sources(self) -> Dict[str, Dict]:
        """Load RSS sources from config"""
        try:
            config_path = Path("config/sources.yaml")
            if config_path.exists():
                import yaml
                with open(config_path) as f:
                    return yaml.safe_load(f).get('sources', {})
        except Exception as e:
            logger.error(f"Failed to load sources config: {e}")
        
        return {}
    
    def _load_triggers(self) -> Dict[str, Dict]:
        """Load agent triggers from config"""
        try:
            config_path = Path("config/triggers.yaml")
            if config_path.exists():
                import yaml
                with open(config_path) as f:
                    data = yaml.safe_load(f)
                    return data.get('triggers', {})
        except Exception as e:
            logger.error(f"Failed to load triggers config: {e}")
        
        return {}
    
    def _is_within_schedule(self) -> bool:
        """Check if current time is within scheduled window"""
        now = datetime.now()
        current_time = now.time()
        
        return self.start_time <= current_time <= self.end_time
    
    def _run_job(self):
        """Execute one cron job cycle"""
        logger.info(f"=== CRON JOB START: {datetime.now()} ===")
        
        # Check if within schedule (skip check in dry-run mode)
        if not self.dry_run and not self._is_within_schedule():
            logger.info("Current time outside scheduled window, skipping")
            return
        
        if self.dry_run:
            logger.info("DRY RUN MODE - No actual actions performed")
        
        try:
            # Step 1: Fetch RSS feeds
            logger.info("Step 1: Fetching RSS feeds...")
            rss_results = parser.fetch_all_feeds(self.sources)
            
            # Step 2: Process each source
            for source_name, entries in rss_results.items():
                logger.info(f"Processing source: {source_name} ({len(entries)} entries)")
                
                # Deduplicate
                new_entries = parser.deduplicate_entries(entries, source_name)
                logger.info(f"Source {source_name}: {len(new_entries)} new entries")
                
                # Match triggers
                matches = trigger_system.batch_match(new_entries, self.triggers)
                
                # Log stats
                logger.info(f"Source {source_name}: {len(matches)} triggers matched")
            
            # Step 3: Log stats
            stats = db.get_stats()
            logger.info(f"Database stats: {json.dumps(stats, indent=2)}")
            
            # Step 4: Log health check
            db.log_health_check('rss_fetch', 'success', f"Fetched {sum(len(e) for e in rss_results.values())} total entries")
            
            logger.info("=== CRON JOB COMPLETED SUCCESSFULLY ===")
            
        except Exception as e:
            logger.error(f"CRON JOB FAILED: {e}", exc_info=True)
            db.log_health_check('cron_job', 'failed', str(e))
    
    def start(self):
        """Start the cron scheduler"""
        self.running = True
        logger.info("Starting Cronjob Money-MVP scheduler...")
        
        # Schedule every 4 hours
        interval_hours = self.config.get('interval_hours', 4)
        self.scheduler.every(interval_hours).hours.do(self._run_job)
        
        # Also schedule every 4 hours using time-based scheduling
        from datetime import datetime
        # Run immediately at startup, then every 4 hours
        self.scheduler.every(4).hours.do(self._run_job)
        
        logger.info(f"Scheduler running (interval: {interval_hours} hours)")
        logger.info(f"Schedule window: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}")
        
        if self.dry_run:
            logger.info("DRY RUN MODE - Run once and exit")
            self._run_job()
            return
        
        # Run once immediately, then every 4 hours
        self._run_job()
        
        while self.running:
            self.scheduler.run_pending()
            time.sleep(60)  # Check every minute
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        sys.exit(0)

# Singleton instance
scheduler = CronScheduler()
