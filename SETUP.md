# Cronjob Money-MVP - Local Setup Guide

## Overview

This guide helps you set up and run the Cronjob Money-MVP base system on your local machine.

## Prerequisites

### Python Version
- **Python 3.10 or higher** required
- Check your version: `python --version` or `python3 --version`

### Operating System
- Windows: 10/11
- macOS: 10.15+
- Linux: Ubuntu 20.04+, Debian 11+, or similar

## Installation Steps

### 1. Clone or Copy the Project

```bash
# If you cloned it
cd Cronjob_Money_MVP_

# If you copied it
cd /path/to/Cronjob_Money_MVP_
```

### 2. Install Python Dependencies

Create a virtual environment (recommended):

```bash
# On macOS/Linux
python3 -m venv venv

# On Windows
python -m venv venv

# Activate the virtual environment
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

**Required Packages:**
- `feedparser>=6.0.10` - RSS feed parsing
- `pyyaml>=6.0` - YAML configuration parsing
- `structlog>=24.0.0` - Structured logging
- `schedule>=1.2.0` - Cron scheduling
- `pytest>=7.4.0` - Testing framework

### 3. Configure Your Feeds

Edit `config/feeds.yaml`:

```yaml
feeds:
  - id: my_deals
    name: My Deals
    url: https://example.com/rss
    priority: 1
    tags: ["deals", "my_tag"]
    enabled: true
```

### 4. Configure Your Agents

Edit `config/agents.yaml`:

```yaml
agents:
  - id: my_agent
    name: My Agent
    type: arbitrage  # or other agent types
    feeds:
      - id: my_deals
    enabled: true
    config:
      # Your agent-specific settings
```

## Usage

### Run Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_integration.py

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=modules --cov-report=html
```

### Run the Cron Job

**Development Mode (runs every minute):**

```bash
python -m modules.cron dev
```

**Production Mode (runs every 4 hours):**

```bash
# Using cron (Linux/macOS)
# Add to crontab: 0 */4 * * * cd /path/to/Cronjob_Money_MVP_ && python -m modules.cron run

# Or using the provided script
./scripts/run_cron.sh
```

### Run Single Cron Execution

```bash
python -m modules.cron --once
```

## Project Structure

```
Cronjob_Money_MVP_/
├── config/              # Configuration files
│   ├── feeds.yaml       # RSS feed definitions
│   ├── agents.yaml      # Agent configurations
│   └── settings.yaml    # Global settings
├── modules/             # Core modules
│   ├── rss/             # RSS ingestion (parser, filter, manager)
│   ├── triggers/        # Agent trigger system
│   ├── config/          # Config management
│   ├── logger/          # Logging/monitoring
│   └── cron.py          # Main cron entry point
├── scripts/             # Utility scripts
│   ├── init.sh          # Initialize project
│   └── run_cron.sh      # Cron runner
├── data/                # Data files
│   ├── feeds/           # User-uploaded RSS feeds
│   └── configs/         # Custom configs
├── logs/                # Application logs
├── tests/               # Unit and integration tests
├── pyproject.toml       # Project metadata
├── requirements.txt     # Python dependencies
├── README.md            # This guide
└── SETUP.md             # This file
```

## Core Components

### 1. RSS Ingestion Module

Parses RSS feeds and extracts items.

```python
from modules.rss.parser import FeedParser
from modules.rss.filter import ItemFilter

parser = FeedParser()
items = parser.parse(url)

filter = ItemFilter(config)
filtered = filter.filter(items)
```

### 2. Agent Trigger System

Manages agent execution based on feed items.

```python
from modules.triggers.manager import TriggerManager

manager = TriggerManager(config, data_dir)
manager.trigger_agent(agent_config, items)
task = manager.get_next_task()
```

### 3. Config Management

Loads and validates YAML configurations.

```python
from modules.config import ConfigManager

config = ConfigManager(config_dir)
feeds = config.load_yaml("config/feeds.yaml")
agents = config.load_yaml("config/agents.yaml")
```

### 4. Logging

Structured JSON logging for debugging.

```python
import structlog

logger = structlog.get_logger()
logger.info("message", key="value")
```

## Common Tasks

### Add a New RSS Feed

1. Edit `config/feeds.yaml`
2. Add your feed with appropriate tags
3. Enable the feed

### Create a New Agent

1. Edit `config/agents.yaml`
2. Add agent configuration
3. Define agent-specific settings
4. Enable the agent

### Modify Trigger Logic

Edit `modules/triggers/manager.py` to customize:
- How agents determine if they should trigger
- Queue management
- Execution timeout handling

## Troubleshooting

### Import Errors

```bash
# Make sure you're in the correct directory
cd Cronjob_Money_MVP_

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Add project root to path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Import Missing Dependencies

```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Configuration Errors

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/feeds.yaml'))"
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/new-agent
```

### 2. Make Changes

Edit files, write tests, add documentation.

### 3. Run Tests

```bash
pytest tests/
```

### 4. Commit Changes

```bash
git add .
git commit -m "Add new agent feature"
git push origin feature/new-agent
```

### 5. Create Pull Request

## Next Steps

1. **Add Your First RSS Feed**: Edit `config/feeds.yaml`
2. **Create an Agent**: Edit `config/agents.yaml`
3. **Run Tests**: Verify everything works
4. **Start Cron**: Begin processing feeds

## Additional Resources

- **Unit Tests**: `tests/test_feed_parser.py`, `tests/test_triggers.py`
- **Integration Tests**: `tests/test_integration.py`
- **Configuration Examples**: `config/feeds.yaml`, `config/agents.yaml`

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the test files for usage examples
3. Check logs in the `logs/` directory

---

**Built for**: JD's OpenClaw Money-Making MVPs
**Status**: Foundation Phase - Ready for deployment
