#!/usr/bin/env python3
"""
Production Launch Test Script
Tests the production launch system functionality
"""

import asyncio
import pytest
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.core.production_launcher import (
    get_production_launcher,
    ProductionLaunchConfig,
    LaunchStatus,
    LaunchPhase
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestProductionLauncher:
    """Test suite for production launcher"""
    
    @pytest.fixture
    def launcher(self):
        """Get production launcher instance"""
        return get_production_launcher()
    
    @pytest.fixture
    def test_config(self):
        """Create test launch configuration"""
        return ProductionLaunchConfig(
            version="1.0.0-test",
            build_id="test-build-123",
            enable_monitoring=True,
            enable_alerting=True,
            enable_user_feedback=True,
            enable_support_system=True,
            enable_auto_scaling=False,  # Disable for testing
            enable_performance_optimization=False,  # Disable for testing
            auto_rollback_on_failure=True,
            cpu_alert_threshold=90.0,  # Higher threshold for testing
            memory_alert_threshold=95.0,  # Higher threshold for testing
            support_email="test-support@example.com"
        )
    
    def test_launcher_initialization(self, launcher):
        """Test launcher initialization"""
        assert launcher is not None
        assert launcher.launch_history == []
        assert launcher.active_launch is None
    
    def test_config_creation(self, test_config):
        """Test configuration creation"""
        assert test_config.version == "1.0.0-test"
        assert test_config.build_id == "test-build-123"
        assert test_config.enable_monitoring is True
        assert test_config.auto_rollback_on_failure is True
        
        # Test config serialization
        config_dict = test_config.to_dict()
        assert "version" in config_dict
        assert "launch_settings" in config_dict
        assert "monitoring_thresholds" in config_dict
    
    def test_launch_status_initial(self, launcher):
        """Test initial launch status"""
        status = launcher.get_launch_status()
        assert status["active"] is False
    
    def test_launch_history_empty(self, launcher):
        """Test empty launch history"""
        history = launcher.get_launch_history()
        assert history == []
    
    def test_production_metrics_no_monitoring(self, launcher):
        """Test production metrics when monitoring is not active"""
        metrics = launcher.get_production_metrics()
        assert "status" in metrics
        assert metrics["status"] == "monitoring_not_active"
    
    @pytest.mark.asyncio
    async def test_launch_simulation(self, launcher, test_config):
        """Test launch simulation (dry run)"""
        # This would test the launch process without actual deployment
        # For now, we'll test the configuration and initial setup
        
        # Test that we can create a launch record
        from app.core.production_launcher import LaunchRecord
        
        launch_record = LaunchRecord(
            version=test_config.version,
            build_id=test_config.build_id,
            config=test_config.to_dict()
        )
        
        assert launch_record.version == test_config.version
        assert launch_record.status == LaunchStatus.PENDING
        assert launch_record.current_phase == LaunchPhase.PRE_LAUNCH
        
        # Test adding phase logs
        launch_record.add_phase_log(
            LaunchPhase.PRE_LAUNCH,
            "Test log message"
        )
        
        assert LaunchPhase.PRE_LAUNCH.value in launch_record.phase_logs
        assert len(launch_record.phase_logs[LaunchPhase.PRE_LAUNCH.value]) == 1
        
        # Test completion
        launch_record.complete(LaunchStatus.COMPLETED)
        assert launch_record.status == LaunchStatus.COMPLETED
        assert launch_record.completed_at is not None
        assert launch_record.duration is not None


class TestMonitoringSetup:
    """Test monitoring setup functionality"""
    
    def test_monitoring_setup_creation(self):
        """Test monitoring setup creation"""
        from app.core.production_launcher import MonitoringSetup, ProductionLaunchConfig
        
        config = ProductionLaunchConfig(version="1.0.0-test")
        monitoring_setup = MonitoringSetup(config)
        
        assert monitoring_setup.config == config
        assert monitoring_setup.health_monitor is None
        assert monitoring_setup.performance_optimizer is None
    
    def test_alert_thresholds(self):
        """Test alert threshold configuration"""
        from app.core.production_launcher import MonitoringSetup, ProductionLaunchConfig
        
        config = ProductionLaunchConfig(
            version="1.0.0-test",
            cpu_alert_threshold=75.0,
            memory_alert_threshold=80.0
        )
        
        monitoring_setup = MonitoringSetup(config)
        
        assert monitoring_setup.config.cpu_alert_threshold == 75.0
        assert monitoring_setup.config.memory_alert_threshold == 80.0


class TestSupportSystem:
    """Test support system functionality"""
    
    def test_support_system_creation(self):
        """Test support system creation"""
        from app.core.production_launcher import SupportSystem, ProductionLaunchConfig
        
        config = ProductionLaunchConfig(
            version="1.0.0-test",
            support_email="test@example.com",
            support_phone="+1-555-TEST"
        )
        
        support_system = SupportSystem(config)
        
        assert support_system.config == config
        assert support_system.support_tickets == []
        assert support_system.knowledge_base == {}


class TestUserFeedbackSystem:
    """Test user feedback system functionality"""
    
    def test_feedback_system_creation(self):
        """Test feedback system creation"""
        from app.core.production_launcher import UserFeedbackSystem, ProductionLaunchConfig
        
        config = ProductionLaunchConfig(version="1.0.0-test")
        feedback_system = UserFeedbackSystem(config)
        
        assert feedback_system.config == config
        assert feedback_system.feedback_data == []
        assert feedback_system.improvement_suggestions == []
    
    def test_feedback_collection(self):
        """Test feedback collection"""
        from app.core.production_launcher import UserFeedbackSystem, ProductionLaunchConfig
        
        config = ProductionLaunchConfig(version="1.0.0-test")
        feedback_system = UserFeedbackSystem(config)
        
        # Collect positive feedback
        feedback_system.collect_feedback(
            user_id="user123",
            feedback_type="feature_request",
            content="Great feature!",
            rating=5
        )
        
        assert len(feedback_system.feedback_data) == 1
        feedback = feedback_system.feedback_data[0]
        assert feedback["user_id"] == "user123"
        assert feedback["rating"] == 5
        assert feedback["status"] == "new"
        
        # Collect negative feedback
        feedback_system.collect_feedback(
            user_id="user456",
            feedback_type="bug_report",
            content="Something is broken",
            rating=1
        )
        
        assert len(feedback_system.feedback_data) == 2


async def run_integration_tests():
    """Run integration tests"""
    logger.info("Running production launch integration tests...")
    
    try:
        # Test launcher initialization
        launcher = get_production_launcher()
        logger.info("✓ Launcher initialization successful")
        
        # Test configuration creation
        config = ProductionLaunchConfig(
            version="1.0.0-integration-test",
            enable_monitoring=False,  # Disable for testing
            enable_alerting=False,
            enable_user_feedback=False,
            enable_support_system=False
        )
        logger.info("✓ Configuration creation successful")
        
        # Test status checks
        status = launcher.get_launch_status()
        assert status["active"] is False
        logger.info("✓ Status check successful")
        
        # Test history
        history = launcher.get_launch_history()
        assert isinstance(history, list)
        logger.info("✓ History check successful")
        
        # Test metrics
        metrics = launcher.get_production_metrics()
        assert isinstance(metrics, dict)
        logger.info("✓ Metrics check successful")
        
        logger.info("All integration tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return False


async def run_performance_tests():
    """Run performance tests"""
    logger.info("Running performance tests...")
    
    try:
        launcher = get_production_launcher()
        
        # Test multiple status checks
        start_time = datetime.now()
        for _ in range(100):
            launcher.get_launch_status()
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✓ 100 status checks completed in {duration:.2f}s")
        
        # Test configuration creation performance
        start_time = datetime.now()
        for i in range(100):
            config = ProductionLaunchConfig(version=f"1.0.{i}")
            config.to_dict()
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✓ 100 config creations completed in {duration:.2f}s")
        
        logger.info("All performance tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        return False


async def main():
    """Main test function"""
    print("\n" + "="*60)
    print("PRODUCTION LAUNCH SYSTEM TESTS")
    print("="*60)
    
    # Run unit tests with pytest
    logger.info("Running unit tests...")
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    
    if exit_code != 0:
        logger.error("Unit tests failed!")
        return False
    
    logger.info("✓ Unit tests passed!")
    
    # Run integration tests
    integration_success = await run_integration_tests()
    if not integration_success:
        return False
    
    # Run performance tests
    performance_success = await run_performance_tests()
    if not performance_success:
        return False
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("="*60)
    print("The production launch system is ready for deployment.")
    print("\nNext steps:")
    print("1. Review configuration settings")
    print("2. Set up monitoring infrastructure")
    print("3. Configure alert channels")
    print("4. Test with staging environment")
    print("5. Execute production launch")
    print("="*60)
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)