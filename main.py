#!/usr/bin/env python3
"""
Cronjob Money-MVP (Base System)
Local private cron system for money-making agent orchestration

Usage:
    python3 main.py --dry-run  # Run once without executing actions
    python3 main.py --start     # Start continuous scheduler
    python3 main.py --once      # Run once and exit
"""

import argparse
import logging
import sys
import yaml
from pathlib import Path

from core.db import db
from core.scheduler import scheduler as cron_scheduler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def load_config():
    """Load system configuration"""
    config_path = Path("config/config.yaml")
    
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return {}
    
    try:
        with open(config_path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}

def setup_database():
    """Initialize database"""
    try:
        db.initialize()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Cronjob Money-MVP - Base System')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Run without executing actions')
    parser.add_argument('--start', action='store_true', 
                       help='Start continuous scheduler')
    parser.add_argument('--once', action='store_true', 
                       help='Run once and exit')
    parser.add_argument('--config', type=str, 
                       help='Path to config file (default: config/config.yaml)')
    parser.add_argument('--verbose', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    if args.config:
        config_path = Path(args.config)
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
    
    # Setup logging level
    if args.verbose:
        logging.getLogger('').setLevel(logging.DEBUG)
    
    # Setup database
    setup_database()
    
    # Initialize scheduler with config
    cron_scheduler.config = config
    
    # Dry run mode
    if args.dry_run or args.once:
        cron_scheduler.dry_run = True
    
    # Run once
    if args.once:
        logger.info("Running once (dry-run mode)")
        cron_scheduler._run_job()
        sys.exit(0)
    
    # Start continuous
    if args.start or not args.once:
        logger.info("Starting continuous scheduler")
        try:
            cron_scheduler.start()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        sys.exit(0)

if __name__ == '__main__':
    main()
