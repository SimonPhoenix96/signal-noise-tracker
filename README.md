# signal-noise-tracker Base System

## Overview

Local private repo; cron runs every 4h, ingests RSS, triggers specific money-making agents.

## Architecture

### Core Components

1. **RSS Ingestion Module**
   - Feed parsing and validation
   - Item filtering and deduplication
   - State management (last read positions)

2. **Agent Trigger System**
   - Queue-based trigger mechanism
   - Agent configuration mapping
   - Execution timeout handling

3. **Config Management**
   - YAML/TOML configuration files
   - Schema validation
   - Environment variable support

4. **Logging & Monitoring**
   - Structured logging (JSON format)
   - Performance metrics
   - Alert thresholds

## Project Structure

```
Cronjob_Money_MVP_/
├── config/              # Configuration files
│   ├── agents.yaml      # Agent configurations
│   ├── feeds.yaml       # RSS feed definitions
│   └── settings.yaml    # Global settings
├── modules/             # Core modules
│   ├── rss/             # RSS ingestion
│   ├── triggers/        # Agent triggers
│   ├── config/          # Config management
│   └── logger/          # Logging/monitoring
├── scripts/             # Utility scripts
│   ├── init.sh          # Initialize project
│   └── run_cron.sh      # Cron runner
├── data/                # User uploads
│   ├── feeds/           # User-uploaded RSS feeds
│   └── configs/         # Custom configs
├── logs/                # Application logs
├── tests/               # Unit tests
└── docs/                # Documentation
```

## Dependencies

- Python 3.10+
- `feedparser` - RSS parsing
- `pyyaml` - Config management
- `structlog` - Structured logging
- `schedule` - Cron scheduling

## Setup

```bash
# Clone/initialize project
cd Cronjob_Money_MVP_
./scripts/init.sh

# Configure feeds
cp config/feeds.yaml.example config/feeds.yaml
# Edit config/feeds.yaml with your RSS feeds

# Configure agents
cp config/agents.yaml.example config/agents.yaml
# Edit config/agents.yaml with agent configurations

# Run tests
pytest tests/

# Start cron (runs every 4h)
./scripts/run_cron.sh
```

## Usage

### Adding a New RSS Feed

Edit `config/feeds.yaml`:

```yaml
feeds:
  - id: deal_hunter
    name: Deal Hunter
    url: https://example.com/rss
    priority: 1
    tags: ["deals", "discount"]
    enabled: true
```

### Defining an Agent Trigger

Edit `config/agents.yaml`:

```yaml
agents:
  - id: arbitrage_checker
    name: Arbitrage Checker
    type: arbitrage
    config:
      feeds: ["deal_hunter"]
      frequency: "every_4h"
      alert_on: ["underpriced"]
```

## Development

Run development cron (every minute):

```bash
python -m modules.cron dev
```

## License

MIT - Open source project for personal business

---

**Built for**: JD's OpenClaw Money-Making MVPs
**Status**: Foundation Phase
