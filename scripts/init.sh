#!/bin/bash
# Initialize Cronjob Money-MVP project

set -e

echo "🚀 Initializing Cronjob Money-MVP project..."

# Create directories
mkdir -p data/feeds
mkdir -p data/configs
mkdir -p logs
mkdir -p tests

# Create placeholder files
touch logs/.gitkeep
touch data/feeds/.gitkeep
touch data/configs/.gitkeep

# Create empty config files
if [ ! -f "config/feeds.yaml" ]; then
    cp config/feeds.yaml.example config/feeds.yaml
    echo "✓ Created config/feeds.yaml (customize with your feeds)"
fi

if [ ! -f "config/agents.yaml" ]; then
    cp config/agents.yaml.example config/agents.yaml
    echo "✓ Created config/agents.yaml (customize with your agents)"
fi

if [ ! -f "config/settings.yaml" ]; then
    cp config/settings.yaml.example config/settings.yaml
    echo "✓ Created config/settings.yaml (customize settings)"
fi

# Create README
if [ ! -f "README.md" ]; then
    cp README.example.md README.md
    echo "✓ Created README.md"
fi

echo ""
echo "✅ Project initialization complete!"
echo ""
echo "Next steps:"
echo "1. Edit config/feeds.yaml - Add your RSS feeds"
echo "2. Edit config/agents.yaml - Configure agents to trigger"
echo "3. Edit config/settings.yaml - Set environment and API keys"
echo "4. Run tests: pytest tests/"
echo "5. Start cron: ./scripts/run_cron.sh"
echo ""
