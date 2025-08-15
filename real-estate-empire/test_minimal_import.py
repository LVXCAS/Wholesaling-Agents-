#!/usr/bin/env python3
"""
Minimal import test to isolate the dataclass issue
"""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_deployment_automation():
    """Test deployment automation import"""
    try:
        from app.core.deployment_automation import DeploymentConfig, DeploymentEnvironment
        print("✓ Deployment automation import successful")
        return True
    except Exception as e:
        print(f"✗ Deployment automation import error: {e}")
        return False

def test_system_health_monitor():
    """Test system health monitor import"""
    try:
        from app.core.system_health_monitor import SystemHealthMonitor
        print("✓ System health monitor import successful")
        return True
    except Exception as e:
        print(f"✗ System health monitor import error: {e}")
        return False

def test_production_launcher():
    """Test production launcher import"""
    try:
        from app.core.production_launcher import ProductionLaunchConfig
        print("✓ Production launcher import successful")
        return True
    except Exception as e:
        print(f"✗ Production launcher import error: {e}")
        return False

def main():
    """Run minimal import tests"""
    print("Testing individual imports...")
    
    test_deployment_automation()
    test_system_health_monitor()
    test_production_launcher()

if __name__ == "__main__":
    main()