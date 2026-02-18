# Signal vs Noise Tracker - Deployment Checklist

**Status**: Ready for External Deployment
**Date**: 2026-02-16
**Target**: GitHub Codespaces (or any environment with pip)

---

## Phase 1: Prerequisites ✅

- [x] Core infrastructure implemented (db.py, rss_parser.py, agent_trigger.py, scheduler.py)
- [x] Configuration files created (sources.yaml, triggers.yaml, config.yaml)
- [x] Dependencies listed (requirements.txt)
- [x] Basic documentation (IMPLEMENTATION_STATUS.md, README.md)

---

## Phase 2: External Deployment Setup 🔄

### Option A: GitHub Codespaces (Recommended)

#### Step 1: Create Repository
```bash
# If not already done
git remote add origin https://github.com/your-username/signal-noise-tracker.git
git push -u origin master
```

#### Step 2: Create GitHub Codespace
```bash
# Via GitHub CLI
gh codespace create --workspace signal-noise-tracker

# Or via GitHub web interface:
# 1. Go to repository
# 2. Click "Code" → "Codespaces"
# 3. Click "Create codespace"
# 4. Select "Python 3" or "Python 3.11" dev container
# 5. Click "Create codespace"
```

**Dev Container Options**:
- Python 3.11 (recommended)
- Docker image: `mcr.microsoft.com/devcontainers/python:3.11`
- VS Code Extensions: Python, Pylance, Yaml

#### Step 3: Verify Environment
```bash
# In terminal
ls -la
cat requirements.txt
```

#### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

**Expected Install**:
```
feedparser==6.0.10
pyyaml==6.0.1
requests==2.31.0
schedule==1.2.0
fastapi==0.104.0
uvicorn==0.24.0
python-multipart==0.0.6
websockets==11.0
```

#### Step 5: Verify Installation
```bash
python3 -c "import feedparser, yaml, requests, schedule, fastapi, uvicorn; print('All imports successful!')"
```

---

### Option B: Local Machine

#### Prerequisites
- Python 3.8+ installed
- pip installed
- Git installed (optional)

#### Installation
```bash
# Clone repository (if applicable)
git clone <repository-url>
cd signal-noise-tracker

# Install dependencies
pip install -r requirements.txt

# Test imports
python3 test_quick.py
```

---

## Phase 3: Configuration Setup

### Step 1: Review Config Files

**sources.yaml** - RSS Feed Sources
```yaml
feeds:
  - name: "Example Feed"
    url: "https://example.com/rss.xml"
    priority: 1
    rate_limit: 3600  # seconds
    max_items: 50
    enabled: true
```

**triggers.yaml** - Agent Triggers
```yaml
triggers:
  - name: "Arbitrage Pattern"
    keywords: ["deal", "cheap", "sale"]
    fields: ["title", "description"]
    actions:
      - type: "arbitrage_alert"
        confidence_threshold: 0.7
```

**config.yaml** - System Configuration
```yaml
logging:
  level: "INFO"
  format: "text"
  file: "logs/cronjob.log"

scheduler:
  interval_hours: 4
  start_hour: 9
  end_hour: 23
  dry_run: true  # Set to false for production

database:
  path: "data/cronjob.db"
  backup_enabled: true
```

### Step 2: Customize for Your Use Case

**Edit sources.yaml**:
- Add your RSS feed URLs
- Set rate limits (prevent API blocking)
- Adjust max_items (don't fetch too much data)

**Edit triggers.yaml**:
- Define your trigger rules
- Set confidence thresholds
- Configure actions

**Edit config.yaml**:
- Adjust scheduler window
- Enable/disable dry-run mode
- Set logging levels

---

## Phase 4: Testing & Validation

### Step 1: Quick Import Test
```bash
python3 test_quick.py
```

**Expected Output**:
```
✅ Database module imported successfully
✅ RSS Parser module imported successfully
✅ Agent Trigger module imported successfully
✅ Scheduler module imported successfully
✅ Configuration files loaded successfully
✅ All dependencies installed
```

### Step 2: Dry-Run Test
```bash
python3 main.py --once --dry-run
```

**Expected Behavior**:
- Fetches RSS feeds
- Parses entries
- Matches triggers
- Logs actions
- Does NOT save to database (dry-run)

**Sample Output**:
```
[INFO] Starting signal-noise-tracker (dry-run mode)
[INFO] Loading configuration from config/config.yaml
[INFO] Initializing database: data/cronjob.db
[INFO] Loaded 3 RSS feed sources
[INFO] Starting scheduler: 4h interval, 09:00-23:00
[INFO] Dry-run mode enabled, no data will be saved
[INFO] Running scheduler...
[INFO] Fetching feed: Example Feed (priority: 1)
[INFO] Parsed 15 items
[INFO] Matching triggers...
[INFO] Found 2 matching entries
[INFO] Trigger 'Arbitrage Pattern' matched 2 entries
[INFO] Scheduler completed (dry-run)
```

### Step 3: Database Test
```bash
# Start continuous scheduler
python3 main.py --start

# In another terminal, check database
sqlite3 data/cronjob.db "SELECT COUNT(*) FROM rss_entries;"
sqlite3 data/cronjob.db "SELECT * FROM rss_entries LIMIT 5;"
```

---

## Phase 5: Production Deployment

### Pre-Deployment Checklist

- [ ] Backup existing database
- [ ] Review all configuration files
- [ ] Test dry-run mode first
- [ ] Set appropriate logging levels
- [ ] Configure rate limits
- [ ] Set up monitoring/alerts
- [ ] Prepare deployment script

### Deployment Steps

#### 1. Set Environment Variables
```bash
# Optional: Create .env file
export LOG_LEVEL=INFO
export DATABASE_PATH=data/cronjob.db
export SCHEDULER_INTERVAL=4
export SCHEDULER_START_HOUR=9
export SCHEDULER_END_HOUR=23
```

#### 2. Run Scheduler in Production Mode
```bash
# Start scheduler (set dry_run to false in config.yaml first!)
python3 main.py --start
```

#### 3. Monitor Logs
```bash
# Tail log file
tail -f logs/cronjob.log

# Check database size
sqlite3 data/cronjob.db "SELECT COUNT(*), SUM(LENGTH(content)) FROM rss_entries;"

# View recent entries
sqlite3 data/cronjob.db "SELECT * FROM rss_entries ORDER BY published DESC LIMIT 10;"
```

#### 4. Set Up Automatic Restart (Linux/Cron)

Create `/etc/cron.d/signal-noise-tracker`:
```bash
# Run every 4 hours
0 */4 * * * cd /path/to/signal-noise-tracker && python3 main.py --once >> logs/cronjob.log 2>&1
```

Or use systemd service (recommended for production):
```bash
# Create systemd service file
sudo nano /etc/systemd/system/signal-noise-tracker.service
```

**Service file content**:
```ini
[Unit]
Description=Signal vs Noise Tracker Scheduler
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/signal-noise-tracker
Environment="LOG_LEVEL=INFO"
ExecStart=/usr/bin/python3 /path/to/signal-noise-tracker/main.py --start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start service**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable signal-noise-tracker
sudo systemctl start signal-noise-tracker
sudo systemctl status signal-noise-tracker
```

---

## Phase 6: Optional Enhancements

### 1. Web Dashboard (FastAPI)

**Create** `main.py` (if not exists):
```python
from fastapi import FastAPI
from core.scheduler import Scheduler
import uvicorn

app = FastAPI(title="Signal vs Noise Tracker Dashboard")

@app.get("/")
def root():
    return {"status": "running", "scheduler": "active"}

@app.get("/stats")
def get_stats():
    # Connect to database and return stats
    return {"entries": 123, "triggers_matched": 45}

@app.get("/logs")
def get_logs():
    # Return recent logs
    return {"logs": []}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Start dashboard**:
```bash
python3 main.py --dashboard
```

### 2. Add Agent Implementations

Create `core/agents/` directory with modules:
- `arbitrage_agent.py`
- `competitive_intel_agent.py`
- `job_radar_agent.py`
- `trend_scanner_agent.py`

Example `arbitrage_agent.py`:
```python
from core.agent_trigger import AgentTrigger

class ArbitrageAgent:
    def __init__(self, config):
        self.trigger = AgentTrigger(config)

    def process(self, rss_entries):
        matches = []
        for entry in rss_entries:
            if self.trigger.match(entry):
                matches.append(self.extract_arbitrage_opportunity(entry))
        return matches

    def extract_arbitrage_opportunity(self, entry):
        # Extract arbitrage opportunity data
        return {
            "title": entry.title,
            "url": entry.link,
            "source": entry.feed_name,
            "price": self.extract_price(entry),
            "potential_profit": self.calculate_profit(entry)
        }
```

### 3. Add Monitoring & Alerts

**Use Slack, Discord, or Email notifications**:
- Log critical errors
- Send alerts when no matches found
- Report performance metrics

---

## Troubleshooting

### Issue: Import Errors
```bash
# Check Python version
python3 --version  # Must be 3.8+

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Issue: Database Lock
```bash
# Close any open connections
sqlite3 data/cronjob.db "PRAGMA busy_timeout=5000;"

# Or delete and recreate (use backup first!)
cp data/cronjob.db data/cronjob.db.backup
rm data/cronjob.db
```

### Issue: RSS Feed Not Parsing
```bash
# Check URL is accessible
curl -I https://example.com/rss.xml

# Check feedparser output
python3 -c "import feedparser; print(feedparser.parse('https://example.com/rss.xml'))"
```

### Issue: No Matches Found
- Check trigger keywords in triggers.yaml
- Verify RSS feed contains matching text
- Adjust confidence thresholds

---

## Success Criteria

Deployment is successful when:
- [x] Dependencies install without errors
- [x] All modules import successfully
- [x] Configuration files load correctly
- [x] Dry-run mode works as expected
- [x] Database is created and populated
- [x] Triggers match entries correctly
- [x] Scheduler runs on schedule
- [ ] (Optional) Web dashboard is functional
- [ ] (Optional) All agent implementations are complete

---

## Next Steps After Deployment

1. **Test with Real RSS Feeds**:
   - Add your own feeds
   - Verify parsing works
   - Check trigger matching

2. **Customize Triggers**:
   - Define your money-making keywords
   - Set appropriate confidence thresholds
   - Test with sample data

3. **Implement Agents**:
   - Add arbitrage detection logic
   - Implement competitive intel analysis
   - Create job radar filtering

4. **Set Up Monitoring**:
   - Configure logging
   - Set up alerts
   - Monitor performance

5. **Scale Up**:
   - Add more RSS feeds
   - Implement web dashboard
   - Add automation workflows

---

**Last Updated**: 2026-02-16
**Status**: Ready for deployment
