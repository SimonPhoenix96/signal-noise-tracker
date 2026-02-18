# Signal vs Noise Tracker Base System

**Priority**: HIGHEST ⭐ | **Status**: CORE INFRASTRUCTURE COMPLETE (70%) | **Deployment**: Ready for External Environment

A modular, configurable RSS feed monitoring system that ingests RSS feeds, matches entries against custom triggers, and triggers specific agents for opportunity detection. This is the foundation system that powers all 11 MVP projects in your portfolio.

---

## 🚀 Quick Start

### Option 1: GitHub Codespaces (Recommended)

1. **Clone repository** (if applicable):
   ```bash
   git clone https://github.com/your-username/signal-noise-tracker.git
   cd signal-noise-tracker
   ```

2. **Create Codespace**:
   ```bash
   gh codespace create --workspace signal-noise-tracker
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Test system**:
   ```bash
   python3 test_quick.py
   ```

5. **Run dry-run**:
   ```bash
   python3 main.py --once --dry-run
   ```

### Option 2: Local Machine

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Test imports**:
   ```bash
   python3 test_quick.py
   ```

3. **Run scheduler**:
   ```bash
   python3 main.py --once --dry-run
   ```

---

## 📋 What This System Does

### Core Workflow

```
┌──────────────────────────────────────┐
│ 1. Cron Schedule (Every 4 hours)     │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ 2. Fetch RSS Feeds                   │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ 3. Parse & Deduplicate Entries       │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ 4. Match Against Triggers            │
│    - Keywords matching               │
│    - Confidence scoring              │
│    - Field-specific matching         │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ 5. Trigger Agents                     │
│    - Arbitrage alerts                 │
│    - Competitive intel                │
│    - Job radar                        │
│    - Trend scanner                    │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ 6. Log Actions & Store Data          │
│    - Database persistence             │
│    - Action logging                   │
│    - Health monitoring                │
└──────────────────────────────────────┘
```

### Key Features

✅ **Modular Architecture**: Separate concerns for parser, triggers, agents
✅ **Configuration-Driven**: YAML-based configs, no code changes needed
✅ **Robust Error Handling**: Graceful degradation, logging
✅ **Database-Backed**: SQLite with comprehensive tables
✅ **Deduplication**: Prevent duplicate entries
✅ **Rate Limiting**: Respect feed source limits
✅ **Flexible Triggers**: Keyword matching, confidence scoring, exclusions
✅ **Production Ready**: Signal handling, logging, monitoring

---

## 🗂️ Project Structure

```
signal-noise-tracker/
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
├── test_quick.py              # Quick sanity test
│
├── config/                    # Configuration files
│   ├── config.yaml            # System configuration
│   ├── sources.yaml           # RSS feed sources
│   ├── triggers.yaml          # Agent triggers
│   └── README.md              # Config guide
│
├── core/                      # Core modules
│   ├── db.py                  # Database wrapper
│   ├── rss_parser.py          # RSS feed parser
│   ├── agent_trigger.py       # Trigger matching engine
│   └── scheduler.py           # Cron scheduler
│
├── data/                      # Runtime data
│   └── cronjob.db             # SQLite database (auto-created)
│
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── test_database.py       # Database tests
│   ├── test_rss_parser.py     # Parser tests
│   └── test_agent_trigger.py  # Trigger tests
│
├── docs/                      # Documentation
│   ├── IMPLEMENTATION_STATUS.md
│   ├── DEPLOYMENT_CHECKLIST.md
│   └── agent_development.md   # (Future: Agent dev guide)
│
└── README.md                  # This file
```

---

## 📦 Dependencies

```
feedparser>=6.0.10      # RSS/Atom parsing
pyyaml>=6.0.1           # YAML configuration
requests>=2.31.0        # HTTP requests
schedule>=1.2.0         # Scheduling (optional)
fastapi>=0.104.0        # Web dashboard (optional)
uvicorn>=0.24.0         # Web server (optional)
python-multipart>=0.0.6 # Form data handling
websockets>=11.0        # WebSocket support
```

---

## ⚙️ Configuration

### 1. System Configuration (`config/config.yaml`)

```yaml
logging:
  level: "INFO"              # DEBUG, INFO, WARNING, ERROR
  format: "text"             # text or json
  file: "logs/cronjob.log"

scheduler:
  interval_hours: 4          # Run every X hours
  start_hour: 9              # Start window: 9 AM - 11 PM
  end_hour: 23
  dry_run: true              # Set to false for production

database:
  path: "data/cronjob.db"    # SQLite database path
  backup_enabled: true       # Enable database backups
```

### 2. RSS Feed Sources (`config/sources.yaml`)

```yaml
feeds:
  - name: "TechCrunch"
    url: "https://feeds.feedburner.com/TechCrunch/"
    priority: 1
    rate_limit: 3600        # seconds between requests
    max_items: 50           # max items per fetch
    enabled: true

  - name: "Hacker News"
    url: "https://hnrss.org/frontpage"
    priority: 2
    rate_limit: 1800
    max_items: 100
    enabled: true
```

### 3. Agent Triggers (`config/triggers.yaml`)

```yaml
triggers:
  - name: "Deal Matcher"
    keywords: ["deal", "sale", "cheap", "discount"]
    fields: ["title", "description"]
    confidence_threshold: 0.7
    exclude_keywords: ["bait", "scam"]

  - name: "Job Alert"
    keywords: ["hiring", "remote", "python", "rust"]
    fields: ["title", "description"]
    confidence_threshold: 0.6
    exclude_keywords: []
```

---

## 🔧 Usage Examples

### Run Once (Dry-Run)

```bash
# Test configuration and triggers without saving data
python3 main.py --once --dry-run
```

**Output**:
```
[INFO] Starting signal-noise-tracker (dry-run mode)
[INFO] Loaded 2 RSS feed sources
[INFO] Starting scheduler...
[INFO] Fetching TechCrunch...
[INFO] Parsed 15 items
[INFO] Matching triggers...
[INFO] Found 3 matching entries
[INFO] Scheduler completed (dry-run)
```

### Start Continuous Scheduler

```bash
# Run continuously on schedule
python3 main.py --start
```

### Run with Custom Config

```bash
# Use a different configuration file
python3 main.py --once --config config/config.prod.yaml
```

### Test Database

```bash
# Check database contents
sqlite3 data/cronjob.db "SELECT COUNT(*) FROM rss_entries;"
sqlite3 data/cronjob.db "SELECT * FROM rss_entries ORDER BY published DESC LIMIT 10;"
```

---

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Suite

```bash
# Database tests
pytest tests/test_database.py -v

# RSS Parser tests
pytest tests/test_rss_parser.py -v

# Agent Trigger tests
pytest tests/test_agent_trigger.py -v
```

### Quick Test

```bash
python3 test_quick.py
```

---

## 🎯 Next Steps

### Phase 2: Monitoring & Dashboard (30%)

- [ ] Enhance logging system (JSON formatting, rotation)
- [ ] Create web dashboard (FastAPI)
- [ ] Implement health checks

### Phase 3: Production Ready (40%)

- [ ] Add retry logic with exponential backoff
- [ ] Implement circuit breakers
- [ ] Create backup system
- [ ] Write deployment guides

### Agent Implementations

- [ ] Arbitrage Agent
- [ ] Competitive Intel Agent
- [ ] Job Radar Agent
- [ ] Trend Scanner Agent

---

## 📊 Database Schema

### rss_entries
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| title | TEXT | Entry title |
| description | TEXT | Entry description |
| link | TEXT | URL to entry |
| published | TEXT | Publication timestamp |
| feed_name | TEXT | Source feed name |
| priority | INTEGER | Feed priority |
| created_at | TEXT | Record creation time |

### agent_triggers
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| trigger_name | TEXT | Trigger name |
| confidence_score | REAL | Match confidence (0-1) |
| matched_entry_id | INTEGER | Referenced RSS entry |
| raw_text | TEXT | Matched text snippet |
| created_at | TEXT | Timestamp |

### agent_actions
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| trigger_id | INTEGER | Referenced trigger |
| action_type | TEXT | Action type |
| action_data | TEXT | Action payload (JSON) |
| created_at | TEXT | Timestamp |

### arbitrage_alerts
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| entry_id | INTEGER | Referenced RSS entry |
| price | REAL | Detected price |
| potential_profit | REAL | Calculated profit |
| source | TEXT | Detection source |
| created_at | TEXT | Timestamp |

### competitive_intel
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| entry_id | INTEGER | Referenced RSS entry |
| category | TEXT | Intelligence category |
| source | TEXT | Collection source |
| created_at | TEXT | Timestamp |

### job_alerts
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| entry_id | INTEGER | Referenced RSS entry |
| job_type | TEXT | Job category |
| skills | TEXT | Required skills (JSON) |
| location | TEXT | Job location |
| created_at | TEXT | Timestamp |

### trend_alerts
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| entry_id | INTEGER | Referenced RSS entry |
| trend_category | TEXT | Trend category |
| momentum | REAL | Trend momentum score |
| created_at | TEXT | Timestamp |

### system_health
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| check_type | TEXT | Health check type |
| status | TEXT | Status (healthy/unhealthy) |
| timestamp | TEXT | Check timestamp |
| details | TEXT | Additional details (JSON) |

---

## 🚢 Deployment

See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for detailed deployment instructions.

### Quick Deploy to GitHub Codespaces

```bash
# 1. Create repository
git init
git add .
git commit -m "Initial commit: Signal vs Noise Tracker Base System"

# 2. Create Codespace
gh codespace create --workspace signal-noise-tracker

# 3. In Codespace terminal:
pip install -r requirements.txt
python3 main.py --once --dry-run
```

---

## 📝 Implementation Status

**Current Phase**: Core Infrastructure (70% Complete)

✅ **Completed**:
- Database module (SQLite wrapper with 8 tables)
- RSS parser (feedparser integration)
- Agent trigger system (keyword matching, confidence scoring)
- Scheduler (4-hour intervals, schedule window)
- Configuration system (YAML-based)
- Basic documentation
- Test suite structure

⏳ **In Progress**:
- Agent implementations (Arbitrage, Competitive Intel, Job Radar, Trend Scanner)
- Enhanced logging system
- Web dashboard

🔄 **Planned**:
- Error handling with retry logic
- Circuit breakers
- Backup system
- Production deployment guides

---

## 🔮 Use Cases & Integration

This system powers all 11 MVP projects:

1. **Weekly Lessons Blog** - Track trending topics
2. **Signal vs Noise Tracker** - Base system (this project)
3. **Competitive Intel** - Monitor competitor moves
4. **Job Radar** - Find relevant opportunities
5. **Arbitrage Alerts** - Detect underpriced items
6. **Product Radar** - Trend tracking
7. **Job Board Filler** - Curate job listings
8. **Local Arbitrage** - Local deal detection
9. **Clip Hunter** - Monitor streams
10. **Event Outreach** - Track events
11. **Tech Migration Scout** - Monitor tech changes

---

## 📚 Additional Documentation

- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - Detailed implementation status
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Complete deployment guide
- [config/README.md](config/README.md) - Configuration guide

---

## 🤝 Contributing

This is a personal project, but contributions are welcome:

1. Fork the repository
2. Create a feature branch
3. Add tests
4. Submit a pull request

---

## 📄 License

Personal project - Build your empire.

---

**Last Updated**: 2026-02-16
**Status**: Ready for external deployment
**Priority**: HIGHEST (Enables all 11 MVPs)
