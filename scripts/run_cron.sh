#!/bin/bash
# Cronjob Money-MVP - Run cron scheduler

set -e

cd "$(dirname "$0")/.."

echo "🔄 Starting Cronjob Money-MVP cron scheduler..."
echo "Schedule: Every 4 hours (0 */4 * * *)"
echo "Press Ctrl+C to stop"
echo ""

# Run Python cron module
python3 -m modules.cron "$@"
