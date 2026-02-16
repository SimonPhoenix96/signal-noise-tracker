# Documentation

This directory contains design documents and specifications for agents in the Cronjob Money-MVP system.

## Files

- **AGENT_DESIGNS.md** - Detailed specifications for money-making agents
- **README.md** - This file

## Quick Links

- [Arbitrage Checker](./AGENT_DESIGNS.md#agent-1-arbitrage-checker--priority-1) - #1 Priority
- [Price Drop Detector](./AGENT_DESIGNS.md#agent-2-price-drop-detector)
- [Trend Analyzer](./AGENT_DESIGNS.md#agent-3-trend-analyzer)

## Getting Started

1. Read the [Agent Designs](./AGENT_DESIGNS.md) document
2. Choose which agent to implement first (recommend: Arbitrage Checker)
3. Review the implementation requirements for your chosen agent
4. Start coding the agent module

## Architecture

All agents follow the standard pattern:
- RSS Feed Ingestion → Item Filtering → Trigger Condition → Action Execution

See [Agent Deisgns](./AGENT_DESIGNS.md#architecture-pattern) for details.
