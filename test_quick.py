#!/usr/bin/env python3
"""
Quick test script for Cronjob Money-MVP
"""

import sys
from pathlib import Path

# Add project to path
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from core.db import db
        print("✅ Database module")
    except Exception as e:
        print(f"❌ Database module: {e}")
        return False
    
    try:
        from core.rss_parser import parser
        print("✅ RSS Parser module")
    except Exception as e:
        print(f"❌ RSS Parser module: {e}")
        return False
    
    try:
        from core.agent_trigger import trigger
        print("✅ Agent Trigger module")
    except Exception as e:
        print(f"❌ Agent Trigger module: {e}")
        return False
    
    try:
        from core.scheduler import scheduler
        print("✅ Scheduler module")
    except Exception as e:
        print(f"❌ Scheduler module: {e}")
        return False
    
    return True

def test_config_loading():
    """Test configuration files"""
    print("\nTesting configuration...")
    
    sources_path = Path("config/sources.yaml")
    triggers_path = Path("config/triggers.yaml")
    config_path = Path("config/config.yaml")
    
    try:
        import yaml
        
        if sources_path.exists():
            with open(sources_path) as f:
                sources = yaml.safe_load(f)
            print(f"✅ Sources config: {len(sources.get('sources', {}))} sources loaded")
        else:
            print("❌ Sources config not found")
            return False
        
        if triggers_path.exists():
            with open(triggers_path) as f:
                triggers = yaml.safe_load(f)
            print(f"✅ Triggers config: {len(triggers.get('triggers', {}))} triggers loaded")
        else:
            print("❌ Triggers config not found")
            return False
        
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
            print(f"✅ System config: {config.get('system', {}).get('version', 'unknown')}")
        else:
            print("❌ System config not found")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False

def test_database():
    """Test database initialization"""
    print("\nTesting database...")
    
    try:
        from core.db import db
        stats = db.get_stats()
        print(f"✅ Database initialized")
        print(f"   Total entries: {stats.get('total_entries', 0)}")
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Cronjob Money-MVP - Quick Test Suite")
    print("=" * 60)
    
    results = []
    
    results.append(test_imports())
    results.append(test_config_loading())
    results.append(test_database())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
