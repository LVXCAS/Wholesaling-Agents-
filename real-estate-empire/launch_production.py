#!/usr/bin/env python3
"""
Production Launch Script
Script to launch the Real Estate Empire system to production
"""

import asyncio
import argparse
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.core.production_launcher import (
    get_production_launcher,
    ProductionLaunchConfig,
    LaunchStatus
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Launch Real Estate Empire to production"
    )
    
    parser.add_argument(
        "--version",
        required=True,
        help="Version to deploy (e.g., 1.0.0)"
    )
    
    parser.add_argument(
        "--build-id",
        help="Build ID (auto-generated if not provided)"
    )
    
    parser.add_argument(
        "--no-monitoring",
        action="store_true",
        help="Disable monitoring setup"
    )
    
    parser.add_argument(
        "--no-alerting",
        action="store_true",
        help="Disable alerting"
    )
    
    parser.add_argument(
        "--no-feedback",
        action="store_true",
        help="Disable user feedback system"
    )
    
    parser.add_argument(
        "--no-support",
        action="store_true",
        help="Disable support system"
    )
    
    parser.add_argument(
        "--no-auto-scaling",
        action="store_true",
        help="Disable auto-scaling"
    )
    
    parser.add_argument(
        "--no-optimization",
        action="store_true",
        help="Disable performance optimization"
    )
    
    parser.add_argument(
        "--no-rollback",
        action="store_true",
        help="Disable auto-rollback on failure"
    )
    
    parser.add_argument(
        "--cpu-threshold",
        type=float,
        default=80.0,
        help="CPU alert threshold percentage (default: 80.0)"
    )
    
    parser.add_argument(
        "--memory-threshold",
        type=float,
        default=85.0,
        help="Memory alert threshold percentage (default: 85.0)"
    )
    
    parser.add_argument(
        "--error-rate-threshold",
        type=float,
        default=0.05,
        help="Error rate alert threshold (default: 0.05)"
    )
    
    parser.add_argument(
        "--response-time-threshold",
        type=float,
        default=5.0,
        help="Response time alert threshold in seconds (default: 5.0)"
    )
    
    parser.add_argument(
        "--support-email",
        default="support@realestate-empire.com",
        help="Support email address"
    )
    
    parser.add_argument(
        "--support-phone",
        default="+1-555-SUPPORT",
        help="Support phone number"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without actual deployment"
    )
    
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for launch completion"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="Timeout in seconds for waiting (default: 3600)"
    )
    
    return parser.parse_args()


async def check_prerequisites():
    """Check prerequisites for production launch"""
    logger.info("Checking prerequisites...")
    
    # Check environment variables
    required_env_vars = [
        "POSTGRES_HOST",
        "POSTGRES_USER", 
        "POSTGRES_PASSWORD",
        "OPENAI_API_KEY",
        "JWT_SECRET_KEY"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return False
    
    # Check if production environment file exists
    prod_env_file = Path("environments/production.env")
    if not prod_env_file.exists():
        logger.error(f"Production environment file not found: {prod_env_file}")
        return False
    
    # Check if required directories exist
    required_dirs = ["app", "docs", "tests"]
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            logger.error(f"Required directory not found: {dir_name}")
            return False
    
    logger.info("Prerequisites check passed")
    return True


async def perform_dry_run(config: ProductionLaunchConfig):
    """Perform a dry run of the production launch"""
    logger.info("Performing dry run...")
    
    print("\n" + "="*60)
    print("PRODUCTION LAUNCH DRY RUN")
    print("="*60)
    
    print(f"Version: {config.version}")
    print(f"Build ID: {config.build_id}")
    print(f"Monitoring: {'Enabled' if config.enable_monitoring else 'Disabled'}")
    print(f"Alerting: {'Enabled' if config.enable_alerting else 'Disabled'}")
    print(f"User Feedback: {'Enabled' if config.enable_user_feedback else 'Disabled'}")
    print(f"Support System: {'Enabled' if config.enable_support_system else 'Disabled'}")
    print(f"Auto Scaling: {'Enabled' if config.enable_auto_scaling else 'Disabled'}")
    print(f"Performance Optimization: {'Enabled' if config.enable_performance_optimization else 'Disabled'}")
    print(f"Auto Rollback: {'Enabled' if config.auto_rollback_on_failure else 'Disabled'}")
    
    print("\nAlert Thresholds:")
    print(f"  CPU: {config.cpu_alert_threshold}%")
    print(f"  Memory: {config.memory_alert_threshold}%")
    print(f"  Error Rate: {config.error_rate_alert_threshold}")
    print(f"  Response Time: {config.response_time_alert_threshold}s")
    
    print("\nSupport Settings:")
    print(f"  Email: {config.support_email}")
    print(f"  Phone: {config.support_phone}")
    print(f"  Hours: {config.support_hours}")
    
    print("\nLaunch Phases:")
    phases = [
        "Pre-launch validation",
        "Production deployment", 
        "Health checks",
        "Monitoring setup",
        "Support system activation",
        "User feedback setup",
        "User onboarding",
        "System optimization"
    ]
    
    for i, phase in enumerate(phases, 1):
        print(f"  {i}. {phase}")
    
    print("\n" + "="*60)
    print("DRY RUN COMPLETED - No actual deployment performed")
    print("="*60)


async def wait_for_completion(launcher, launch_id: str, timeout: int):
    """Wait for launch completion"""
    logger.info(f"Waiting for launch completion (timeout: {timeout}s)...")
    
    start_time = datetime.now()
    last_phase = None
    
    while True:
        status = launcher.get_launch_status()
        
        if not status["active"]:
            logger.info("Launch completed")
            break
        
        current_phase = status.get("current_phase")
        if current_phase != last_phase:
            logger.info(f"Current phase: {current_phase}")
            last_phase = current_phase
        
        # Check timeout
        elapsed = (datetime.now() - start_time).total_seconds()
        if elapsed > timeout:
            logger.error(f"Launch timeout after {timeout} seconds")
            return False
        
        await asyncio.sleep(10)  # Check every 10 seconds
    
    # Get final status
    history = launcher.get_launch_history(limit=1)
    if history:
        final_status = history[0]["status"]
        logger.info(f"Final launch status: {final_status}")
        return final_status == "completed"
    
    return False


async def main():
    """Main function"""
    args = parse_arguments()
    
    print("\n" + "="*60)
    print("REAL ESTATE EMPIRE - PRODUCTION LAUNCH")
    print("="*60)
    print(f"Version: {args.version}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*60)
    
    try:
        # Check prerequisites
        if not await check_prerequisites():
            logger.error("Prerequisites check failed")
            sys.exit(1)
        
        # Create launch configuration
        config = ProductionLaunchConfig(
            version=args.version,
            build_id=args.build_id or f"build-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            enable_monitoring=not args.no_monitoring,
            enable_alerting=not args.no_alerting,
            enable_user_feedback=not args.no_feedback,
            enable_support_system=not args.no_support,
            enable_auto_scaling=not args.no_auto_scaling,
            enable_performance_optimization=not args.no_optimization,
            auto_rollback_on_failure=not args.no_rollback,
            cpu_alert_threshold=args.cpu_threshold,
            memory_alert_threshold=args.memory_threshold,
            error_rate_alert_threshold=args.error_rate_threshold,
            response_time_alert_threshold=args.response_time_threshold,
            support_email=args.support_email,
            support_phone=args.support_phone
        )
        
        # Perform dry run if requested
        if args.dry_run:
            await perform_dry_run(config)
            return
        
        # Get production launcher
        launcher = get_production_launcher()
        
        # Check if launch is already in progress
        current_status = launcher.get_launch_status()
        if current_status["active"]:
            logger.error(f"Production launch already in progress: {current_status['launch_id']}")
            sys.exit(1)
        
        # Start production launch
        logger.info("Starting production launch...")
        launch_record = await launcher.launch_production(config)
        
        print(f"\nProduction launch initiated:")
        print(f"  Launch ID: {launch_record.id}")
        print(f"  Version: {launch_record.version}")
        print(f"  Status: {launch_record.status.value}")
        print(f"  Started: {launch_record.started_at.isoformat()}")
        
        # Wait for completion if requested
        if args.wait:
            success = await wait_for_completion(launcher, launch_record.id, args.timeout)
            
            if success:
                print("\n" + "="*60)
                print("PRODUCTION LAUNCH COMPLETED SUCCESSFULLY!")
                print("="*60)
                
                # Get final metrics
                metrics = launcher.get_production_metrics()
                print(f"System Status: {metrics.get('overall_status', 'unknown')}")
                print(f"Monitoring: {metrics.get('monitoring_status', 'unknown')}")
                
            else:
                print("\n" + "="*60)
                print("PRODUCTION LAUNCH FAILED OR TIMED OUT")
                print("="*60)
                sys.exit(1)
        else:
            print("\nLaunch initiated in background. Use --wait to wait for completion.")
            print(f"Check status with: python -c \"from app.core.production_launcher import get_production_launcher; print(get_production_launcher().get_launch_status())\"")
        
    except KeyboardInterrupt:
        logger.info("Launch interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Launch failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())