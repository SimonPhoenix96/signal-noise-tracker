# Agent Design Specifications

**Project**: Cronjob Money-MVP Base System
**Last Updated**: 2026-02-16
**Author**: GOAP Planner (@main)
**Status**: Design Phase

---

## Overview

This document contains detailed specifications for implementing money-making agents that will run in the Cronjob Money-MVP system. Each agent follows the same pattern: RSS ingestion → item filtering → trigger condition → action.

---

## Architecture Pattern

### Standard Agent Lifecycle

```
1. RSS Feed Ingestion
   ↓
2. Item Filtering (tags, keywords, conditions)
   ↓
3. Trigger Condition Check (min profit, thresholds)
   ↓
4. Action Execution (send alert, save to DB, notify user)
   ↓
5. Queue Management (deduplication, rate limiting)
```

### Key Components

- **Trigger Manager**: Evaluates if an agent should activate
- **Item Filter**: Filters RSS items based on criteria
- **Action Handler**: Executes the agent's logic
- **Queue Manager**: Prevents duplicate alerts and manages rate limiting

---

## Agent #1: Arbitrage Checker ⭐ PRIORITY 1

**Status**: Design Phase
**Estimated Complexity**: Medium
**Revenue Potential**: High

### Description

Scans multiple RSS feeds for underpriced items that can be resold for profit. Compares item prices across sources and flags items with profit margins above a configurable threshold.

### Target Platforms

- **Kleinanzeigen** (German market)
- **eBay** (International)
- **Vinted** (Fashion marketplace)
- **Facebook Marketplace** (Local)

### Configuration (from `config/agents.yaml`)

```yaml
- id: arbitrage_checker
  name: Arbitrage Checker
  type: arbitrage
  feeds:
    - id: kleinanzeigen_deals
    - id: ebay_deals
    - id: vinted_deals
    - id: facebook_marketplace
  enabled: true
  priority: 1

  config:
    min_profit_percent: 20          # Minimum 20% profit
    required_tags:
      - "deal"
      - "underpriced"
    exclude_keywords:
      - "used"
      - "damaged"
      - "open box"
    alert_methods:
      - discord
      - email
    rate_limit_seconds: 3600        # Max 1 alert per hour per item
```

### Implementation Requirements

#### Module: `modules/agents/arbitrage_checker.py`

**Classes Required:**

1. **ArbitrageChecker** - Main agent class
   - `__init__(agent_config: Dict)` - Initialize with config
   - `should_trigger(items: List[Dict]) -> bool` - Check if items qualify
   - `process_items(items: List[Dict]) -> List[Dict]` - Filter and rank items
   - `execute()` - Main execution method
   - `save_results(results: List[Dict])` - Persist to database
   - `send_alerts(results: List[Dict])` - Send Discord/email alerts

2. **PriceComparator** - Helper for price comparison
   - `compare_prices(items: List[Dict]) -> Dict[str, List[Dict]]`
   - `calculate_profit_margin(original_price, resell_price) -> float`
   - `find_best_price(item_id, marketplaces) -> Dict`

3. **Deduplicator** - Prevent duplicate alerts
   - `is_duplicate(item_id, alert_time) -> bool`
   - `mark_as_notified(item_id, timestamp)`
   - `get_recent_alerts(hours=24) -> List[str]`

**Required Database Schema:**

```sql
CREATE TABLE arbitrage_alerts (
    id SERIAL PRIMARY KEY,
    item_id VARCHAR(255) UNIQUE NOT NULL,
    source VARCHAR(100) NOT NULL,           -- Where found
    item_url VARCHAR(500),
    item_name TEXT,
    buy_price DECIMAL(10, 2) NOT NULL,
    resell_price DECIMAL(10, 2) NOT NULL,
    profit_margin DECIMAL(5, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notified BOOLEAN DEFAULT FALSE,
    processed BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_item_id ON arbitrage_alerts(item_id);
CREATE INDEX idx_created_at ON arbitrage_alerts(created_at);
CREATE INDEX idx_notified ON arbitrage_alerts(notified);
```

**Integration Points:**

1. **RSS Manager**: Get items from configured feeds
   ```python
   from modules.rss import RSSManager
   manager = RSSManager()
   items = manager.fetch_feed(feed_id)
   ```

2. **Logger**: Log progress and results
   ```python
   from modules.logger import get_logger
   logger = get_logger(__name__)
   ```

3. **Config Manager**: Load agent-specific settings
   ```python
   from modules.config import ConfigManager
   config_mgr = ConfigManager()
   agent_config = config_mgr.load_config("agents")["agents"][0]
   ```

### Features

1. **Profit Calculation**
   - Calculate profit margin: `((resell_price - buy_price) / buy_price) * 100`
   - Filter by `min_profit_percent` threshold

2. **Price Comparison**
   - Compare item prices across multiple marketplaces
   - Identify the best resell price

3. **Smart Filtering**
   - Exclude items with blacklisted keywords
   - Require specific tags
   - Filter by item condition

4. **Deduplication**
   - Track notified items to avoid duplicate alerts
   - Set time-based deduplication window

5. **Alert Methods**
   - Discord webhooks
   - Email (SMTP)
   - Save to database for later review

### Edge Cases

1. **Price Range Variations**
   - Some items have multiple prices (e.g., new vs. used)
   - Use lowest price for arbitrage calculation

2. **Shipping Costs**
   - Account for shipping when calculating profit
   - Set minimum threshold on net profit

3. **Item Condition**
   - Filter by item quality requirements
   - Exclude damaged or "as-is" items

4. **Timing**
   - Rate limit alerts to avoid spam
   - Track last alert time per item

### Testing Strategy

1. **Unit Tests**
   - Test profit margin calculation
   - Test keyword filtering
   - Test deduplication logic
   - Test price comparison

2. **Integration Tests**
   - Feed ingestion + processing
   - Database persistence
   - Alert sending (mocked)

3. **Mock Data**
   - Use realistic eBay/Kleinanzeigen listings
   - Test edge cases (zero profit, negative profit)

### Success Metrics

1. **Alert Accuracy**
   - % of alerts with >20% profit margin
   - False positive rate (alerts on items that can't be resold)

2. **Response Time**
   - Time from RSS item to alert
   - Processing latency

3. **User Adoption**
   - Number of alerts actually used
   - User feedback on alert quality

### Next Steps

1. ✅ Design specification completed
2. ⏳ Implement ArbitrageChecker class
3. ⏳ Implement PriceComparator
4. ⏳ Implement Deduplicator
5. ⏳ Create database schema
6. ⏳ Write unit tests
7. ⏳ Write integration tests
8. ⏳ Test with real feeds
9. ⏳ Deploy to production

---

## Agent #2: Price Drop Detector

**Status**: Design Phase
**Estimated Complexity**: Low
**Revenue Potential**: Medium

### Description

Monitors items on watchlist and alerts when prices drop below threshold.

### Configuration

```yaml
- id: price_drop_detector
  name: Price Drop Detector
  type: price_tracker
  feeds:
    - id: price_tracker_electronics
  enabled: true
  config:
    price_drop_threshold_percent: 15
    track_days: 30
    alert_on_drop: true
```

### Implementation

1. **PriceHistory** class
   - Track price changes over time
   - Store historical prices for each item
   - Calculate price drop percentage

2. **Watchlist** class
   - Manage user watchlist
   - Item ID tracking
   - Alert thresholds

3. **Alert** class
   - Send price drop alerts
   - Include price history chart (optional)

---

## Agent #3: Trend Analyzer

**Status**: Design Phase
**Estimated Complexity**: Medium
**Revenue Potential**: Medium

### Description

Analyzes trends across multiple feeds and generates weekly/monthly reports.

### Configuration

```yaml
- id: trend_analyzer
  name: Trend Analyzer
  type: trend_analyzer
  feeds:
    - id: ecommerce_trends
  enabled: true
  config:
    analysis_interval_minutes: 60
    trending_keywords:
      - "release"
      - "launch"
      - "new"
    output_formats:
      - report
      - summary
    discord_report: true
```

### Implementation

1. **TrendDetector** class
   - Track keyword frequency
   - Identify emerging trends
   - Calculate trend scores

2. **ReportGenerator** class
   - Generate weekly reports
   - Create summary statistics
   - Format for Discord/Email

3. **KeywordAnalyzer** class
   - Track keyword usage
   - Identify trending topics
   - Calculate relevance scores

---

## General Agent Templates

### Creating New Agents

1. **Create Module File**: `modules/agents/[agent_name].py`
2. **Define Agent Class**: Inherit from `Agent` base class
3. **Implement Methods**: `should_trigger()`, `process_items()`, `execute()`
4. **Register in Config**: Add to `config/agents.yaml`
5. **Write Tests**: Add to `tests/test_[agent_name].py`

### Base Agent Class

```python
from typing import Dict, List, Any
from abc import ABC, abstractmethod

class Agent(ABC):
    """Base class for all agents"""

    def __init__(self, agent_config: Dict):
        self.config = agent_config
        self.agent_id = agent_config.get("id")
        self.agent_name = agent_config.get("name")
        self.enabled = agent_config.get("enabled", True)

    @abstractmethod
    def should_trigger(self, items: List[Dict]) -> bool:
        """Check if agent should trigger based on items"""
        pass

    @abstractmethod
    def process_items(self, items: List[Dict]) -> List[Dict]:
        """Process items and return filtered/transformed results"""
        pass

    def execute(self, items: List[Dict] = None) -> List[Dict]:
        """Main execution method"""
        if items is None:
            # Fetch items from configured feeds
            items = self.fetch_items()

        if not self.should_trigger(items):
            return []

        return self.process_items(items)

    def fetch_items(self) -> List[Dict]:
        """Fetch items from configured feeds"""
        feeds = self.config.get("feeds", [])
        # Implementation depends on specific agent type
        return []

    def save_results(self, results: List[Dict]):
        """Save results to database/file"""
        # Implementation
        pass

    def send_alerts(self, results: List[Dict]):
        """Send alerts to user"""
        # Implementation
        pass
```

---

## Deployment Checklist

- [ ] Create database schema for agent
- [ ] Implement agent class
- [ ] Implement helper classes
- [ ] Write unit tests (min 80% coverage)
- [ ] Write integration tests
- [ ] Test with mock data
- [ ] Test with real feeds
- [ ] Deploy to production
- [ ] Monitor performance
- [ ] Gather user feedback
- [ ] Iterate and improve

---

**Notes**:
- All agents should be modular and reusable
- Each agent should have clear success metrics
- Agents should be independently deployable
- Monitor usage and optimize for performance
