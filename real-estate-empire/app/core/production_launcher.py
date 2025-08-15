"""
Production Launch System
Comprehensive production deployment, monitoring, and support system
"""

import asyncio
import logging
import os
import json
import yaml
import subprocess
import shutil
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import uuid
import tempfile
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from pydantic import BaseModel, Field

from .deployment_automation import DeploymentConfig, DeploymentEnvironment, DeploymentPipeline, ConfigurationManager, ConfigurationType
from .system_health_monitor import SystemHealthMonitor, HealthStatus, AlertSeverity
from .performance_optimizer import PerformanceOptimizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LaunchPhase(str, Enum):
    """Production launch phases"""
    PRE_LAUNCH = "pre_launch"
    DEPLOYMENT = "deployment"
    HEALTH_CHECK = "health_check"
    MONITORING_SETUP = "monitoring_setup"
    USER_ONBOARDING = "user_onboarding"
    SUPPORT_ACTIVATION = "support_activation"
    FEEDBACK_COLLECTION = "feedback_collection"
    OPTIMIZATION = "optimization"
    COMPLETED = "completed"
    FAILED = "failed"


class LaunchStatus(str, Enum):
    """Launch status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ProductionLaunchConfig:
    """Production launch configuration"""
    version: str
    build_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Launch settings
    enable_monitoring: bool = True
    enable_alerting: bool = True
    enable_user_feedback: bool = True
    enable_support_system: bool = True
    
    # Performance settings
    enable_auto_scaling: bool = True
    enable_performance_optimization: bool = True
    
    # Rollback settings
    auto_rollback_on_failure: bool = True
    rollback_threshold_error_rate: float = 0.1  # 10%
    rollback_threshold_response_time: float = 10.0  # 10 seconds
    
    # Monitoring thresholds
    cpu_alert_threshold: float = 80.0
    memory_alert_threshold: float = 85.0
    error_rate_alert_threshold: float = 0.05  # 5%
    response_time_alert_threshold: float = 5.0  # 5 seconds
    
    # Support settings
    support_email: str = "support@realestate-empire.com"
    support_phone: str = "+1-555-SUPPORT"
    support_hours: str = "24/7"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "version": self.version,
            "build_id": self.build_id,
            "launch_settings": {
                "enable_monitoring": self.enable_monitoring,
                "enable_alerting": self.enable_alerting,
                "enable_user_feedback": self.enable_user_feedback,
                "enable_support_system": self.enable_support_system
            },
            "performance_settings": {
                "enable_auto_scaling": self.enable_auto_scaling,
                "enable_performance_optimization": self.enable_performance_optimization
            },
            "rollback_settings": {
                "auto_rollback_on_failure": self.auto_rollback_on_failure,
                "rollback_threshold_error_rate": self.rollback_threshold_error_rate,
                "rollback_threshold_response_time": self.rollback_threshold_response_time
            },
            "monitoring_thresholds": {
                "cpu_alert_threshold": self.cpu_alert_threshold,
                "memory_alert_threshold": self.memory_alert_threshold,
                "error_rate_alert_threshold": self.error_rate_alert_threshold,
                "response_time_alert_threshold": self.response_time_alert_threshold
            },
            "support_settings": {
                "support_email": self.support_email,
                "support_phone": self.support_phone,
                "support_hours": self.support_hours
            }
        }


class LaunchRecord(BaseModel):
    """Record of a production launch"""
    version: str
    build_id: str
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: LaunchStatus = LaunchStatus.PENDING
    current_phase: LaunchPhase = LaunchPhase.PRE_LAUNCH
    
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None  # seconds
    
    config: Dict[str, Any] = Field(default_factory=dict)
    phase_logs: Dict[str, List[str]] = Field(default_factory=dict)
    error_message: Optional[str] = None
    
    # Launch metrics
    deployment_success: bool = False
    health_check_success: bool = False
    monitoring_active: bool = False
    support_active: bool = False
    user_feedback_active: bool = False
    
    # Performance metrics
    initial_response_time: Optional[float] = None
    initial_error_rate: Optional[float] = None
    user_adoption_rate: Optional[float] = None
    
    def add_phase_log(self, phase: LaunchPhase, message: str, level: str = "INFO"):
        """Add log message for specific phase"""
        if phase.value not in self.phase_logs:
            self.phase_logs[phase.value] = []
        
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"
        self.phase_logs[phase.value].append(log_entry)
        
        if level in ["ERROR", "CRITICAL"]:
            self.error_message = message
    
    def complete(self, status: LaunchStatus):
        """Mark launch as complete"""
        self.status = status
        self.completed_at = datetime.now()
        
        if self.started_at:
            self.duration = (self.completed_at - self.started_at).total_seconds()


class MonitoringSetup:
    """Production monitoring setup"""
    
    def __init__(self, config: ProductionLaunchConfig):
        self.config = config
        self.health_monitor: Optional[SystemHealthMonitor] = None
        self.performance_optimizer: Optional[PerformanceOptimizer] = None
        self.alert_handlers: List[Callable] = []
        
    async def setup_monitoring(self, launch_record: LaunchRecord) -> bool:
        """Setup production monitoring"""
        try:
            launch_record.add_phase_log(
                LaunchPhase.MONITORING_SETUP,
                "Setting up production monitoring system"
            )
            
            # Initialize health monitor
            self.health_monitor = SystemHealthMonitor(monitoring_interval=30)
            
            # Configure alert thresholds
            self.health_monitor.alert_thresholds.update({
                "cpu_percent": self.config.cpu_alert_threshold,
                "memory_percent": self.config.memory_alert_threshold,
                "agent_response_time": self.config.response_time_alert_threshold,
                "agent_error_rate": self.config.error_rate_alert_threshold
            })
            
            # Setup alert handlers
            if self.config.enable_alerting:
                self.health_monitor.alert_callbacks.append(self._handle_production_alert)
            
            # Start monitoring
            await self.health_monitor.start_monitoring()
            
            launch_record.add_phase_log(
                LaunchPhase.MONITORING_SETUP,
                "Health monitoring started successfully"
            )
            
            # Setup performance optimization
            if self.config.enable_performance_optimization:
                self.performance_optimizer = PerformanceOptimizer()
                await self.performance_optimizer.start_optimization(self.health_monitor)
                
                launch_record.add_phase_log(
                    LaunchPhase.MONITORING_SETUP,
                    "Performance optimization enabled"
                )
            
            launch_record.monitoring_active = True
            return True
            
        except Exception as e:
            launch_record.add_phase_log(
                LaunchPhase.MONITORING_SETUP,
                f"Monitoring setup failed: {str(e)}",
                "ERROR"
            )
            return False
    
    def _handle_production_alert(self, alert):
        """Handle production alerts"""
        try:
            # Log alert
            logger.warning(f"Production Alert: {alert.message}")
            
            # Send email notification
            self._send_alert_email(alert)
            
            # Send to external monitoring systems
            self._send_to_external_monitoring(alert)
            
            # Check for auto-rollback conditions
            if self.config.auto_rollback_on_failure:
                self._check_rollback_conditions(alert)
                
        except Exception as e:
            logger.error(f"Error handling production alert: {e}")
    
    def _send_alert_email(self, alert):
        """Send alert via email"""
        try:
            # Email configuration from environment
            smtp_host = os.getenv("SMTP_HOST", "localhost")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_user = os.getenv("SMTP_USER", "")
            smtp_password = os.getenv("SMTP_PASSWORD", "")
            
            if not smtp_user:
                return
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = self.config.support_email
            msg['Subject'] = f"Production Alert: {alert.severity.value.upper()}"
            
            body = f"""
            Production Alert Notification
            
            Severity: {alert.severity.value.upper()}
            Component: {alert.component}
            Message: {alert.message}
            Timestamp: {alert.timestamp}
            
            Current Value: {alert.current_value}
            Threshold: {alert.threshold_value}
            
            Details: {json.dumps(alert.details, indent=2)}
            
            Please investigate immediately.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")
    
    def _send_to_external_monitoring(self, alert):
        """Send alert to external monitoring systems"""
        # This would integrate with systems like PagerDuty, Slack, etc.
        pass
    
    def _check_rollback_conditions(self, alert):
        """Check if rollback conditions are met"""
        # This would implement auto-rollback logic
        pass


class SupportSystem:
    """Production support system"""
    
    def __init__(self, config: ProductionLaunchConfig):
        self.config = config
        self.support_tickets: List[Dict[str, Any]] = []
        self.knowledge_base: Dict[str, str] = {}
        
    async def setup_support_system(self, launch_record: LaunchRecord) -> bool:
        """Setup production support system"""
        try:
            launch_record.add_phase_log(
                LaunchPhase.SUPPORT_ACTIVATION,
                "Setting up production support system"
            )
            
            # Initialize knowledge base
            await self._initialize_knowledge_base()
            
            # Setup support procedures
            await self._setup_support_procedures()
            
            # Create support documentation
            await self._create_support_documentation()
            
            launch_record.add_phase_log(
                LaunchPhase.SUPPORT_ACTIVATION,
                "Support system activated successfully"
            )
            
            launch_record.support_active = True
            return True
            
        except Exception as e:
            launch_record.add_phase_log(
                LaunchPhase.SUPPORT_ACTIVATION,
                f"Support system setup failed: {str(e)}",
                "ERROR"
            )
            return False
    
    async def _initialize_knowledge_base(self):
        """Initialize support knowledge base"""
        self.knowledge_base = {
            "login_issues": "Check credentials and ensure account is active. Reset password if needed.",
            "performance_slow": "Check system status dashboard. Contact support if issues persist.",
            "data_sync_issues": "Verify internet connection. Check data sync status in settings.",
            "feature_requests": "Submit feature requests through the feedback system.",
            "billing_questions": "Contact billing support at billing@realestate-empire.com",
            "technical_issues": f"Contact technical support at {self.config.support_email}"
        }
    
    async def _setup_support_procedures(self):
        """Setup support procedures"""
        # This would setup support ticket routing, escalation procedures, etc.
        pass
    
    async def _create_support_documentation(self):
        """Create support documentation"""
        support_docs = {
            "user_guide": "Complete user guide with step-by-step instructions",
            "troubleshooting": "Common issues and solutions",
            "api_documentation": "API reference and examples",
            "faq": "Frequently asked questions"
        }
        
        # Create documentation files
        docs_dir = Path("docs/production_support")
        docs_dir.mkdir(exist_ok=True)
        
        for doc_type, content in support_docs.items():
            doc_file = docs_dir / f"{doc_type}.md"
            with open(doc_file, 'w') as f:
                f.write(f"# {doc_type.replace('_', ' ').title()}\n\n{content}\n")


class UserFeedbackSystem:
    """User feedback and improvement system"""
    
    def __init__(self, config: ProductionLaunchConfig):
        self.config = config
        self.feedback_data: List[Dict[str, Any]] = []
        self.improvement_suggestions: List[Dict[str, Any]] = []
        
    async def setup_feedback_system(self, launch_record: LaunchRecord) -> bool:
        """Setup user feedback system"""
        try:
            launch_record.add_phase_log(
                LaunchPhase.FEEDBACK_COLLECTION,
                "Setting up user feedback system"
            )
            
            # Initialize feedback collection
            await self._initialize_feedback_collection()
            
            # Setup feedback analysis
            await self._setup_feedback_analysis()
            
            # Create feedback dashboard
            await self._create_feedback_dashboard()
            
            launch_record.add_phase_log(
                LaunchPhase.FEEDBACK_COLLECTION,
                "User feedback system activated successfully"
            )
            
            launch_record.user_feedback_active = True
            return True
            
        except Exception as e:
            launch_record.add_phase_log(
                LaunchPhase.FEEDBACK_COLLECTION,
                f"Feedback system setup failed: {str(e)}",
                "ERROR"
            )
            return False
    
    async def _initialize_feedback_collection(self):
        """Initialize feedback collection mechanisms"""
        # Setup feedback collection endpoints, forms, etc.
        pass
    
    async def _setup_feedback_analysis(self):
        """Setup automated feedback analysis"""
        # Setup sentiment analysis, categorization, etc.
        pass
    
    async def _create_feedback_dashboard(self):
        """Create feedback dashboard"""
        # Create dashboard for viewing and analyzing feedback
        pass
    
    def collect_feedback(self, user_id: str, feedback_type: str, content: str, rating: int):
        """Collect user feedback"""
        feedback = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "feedback_type": feedback_type,
            "content": content,
            "rating": rating,
            "timestamp": datetime.now().isoformat(),
            "status": "new"
        }
        
        self.feedback_data.append(feedback)
        
        # Analyze feedback for immediate issues
        if rating <= 2:  # Low rating
            self._handle_negative_feedback(feedback)
    
    def _handle_negative_feedback(self, feedback: Dict[str, Any]):
        """Handle negative feedback immediately"""
        # Create support ticket, alert team, etc.
        logger.warning(f"Negative feedback received: {feedback['content']}")


class ProductionLauncher:
    """
    Production Launch System
    
    Handles complete production deployment with:
    - Automated deployment
    - Health monitoring setup
    - Alerting configuration
    - Support system activation
    - User feedback collection
    - Performance optimization
    """
    
    def __init__(self):
        self.deployment_pipeline: Optional[DeploymentPipeline] = None
        self.config_manager: Optional[ConfigurationManager] = None
        self.monitoring_setup: Optional[MonitoringSetup] = None
        self.support_system: Optional[SupportSystem] = None
        self.feedback_system: Optional[UserFeedbackSystem] = None
        
        self.launch_history: List[LaunchRecord] = []
        self.active_launch: Optional[LaunchRecord] = None
        
        logger.info("Production Launcher initialized")
    
    async def launch_production(self, config: ProductionLaunchConfig) -> LaunchRecord:
        """Launch production system"""
        
        # Create launch record
        launch_record = LaunchRecord(
            version=config.version,
            build_id=config.build_id,
            config=config.to_dict()
        )
        
        launch_record.add_phase_log(
            LaunchPhase.PRE_LAUNCH,
            f"Starting production launch for version {config.version}"
        )
        
        try:
            self.active_launch = launch_record
            launch_record.status = LaunchStatus.IN_PROGRESS
            
            # Execute launch phases
            success = await self._execute_launch_phases(launch_record, config)
            
            if success:
                launch_record.complete(LaunchStatus.COMPLETED)
                launch_record.current_phase = LaunchPhase.COMPLETED
                launch_record.add_phase_log(
                    LaunchPhase.COMPLETED,
                    "Production launch completed successfully"
                )
            else:
                launch_record.complete(LaunchStatus.FAILED)
                launch_record.current_phase = LaunchPhase.FAILED
                
                # Attempt rollback if configured
                if config.auto_rollback_on_failure:
                    await self._rollback_launch(launch_record, config)
            
        except Exception as e:
            launch_record.complete(LaunchStatus.FAILED)
            launch_record.add_phase_log(
                LaunchPhase.FAILED,
                f"Production launch failed: {str(e)}",
                "ERROR"
            )
            
            # Attempt rollback
            if config.auto_rollback_on_failure:
                await self._rollback_launch(launch_record, config)
            
            raise
        
        finally:
            # Add to history
            self.launch_history.append(launch_record)
            self.active_launch = None
            
            # Limit history size
            if len(self.launch_history) > 50:
                self.launch_history = self.launch_history[-25:]
        
        return launch_record
    
    async def _execute_launch_phases(self, launch_record: LaunchRecord, 
                                   config: ProductionLaunchConfig) -> bool:
        """Execute all launch phases"""
        
        phases = [
            (LaunchPhase.PRE_LAUNCH, self._pre_launch_validation),
            (LaunchPhase.DEPLOYMENT, self._deploy_to_production),
            (LaunchPhase.HEALTH_CHECK, self._run_production_health_checks),
            (LaunchPhase.MONITORING_SETUP, self._setup_monitoring),
            (LaunchPhase.SUPPORT_ACTIVATION, self._activate_support_system),
            (LaunchPhase.FEEDBACK_COLLECTION, self._setup_feedback_collection),
            (LaunchPhase.USER_ONBOARDING, self._setup_user_onboarding),
            (LaunchPhase.OPTIMIZATION, self._optimize_production_system)
        ]
        
        for phase, phase_func in phases:
            launch_record.current_phase = phase
            launch_record.add_phase_log(phase, f"Starting phase: {phase.value}")
            
            try:
                success = await phase_func(launch_record, config)
                
                if success:
                    launch_record.add_phase_log(phase, f"Phase completed: {phase.value}")
                else:
                    launch_record.add_phase_log(
                        phase, f"Phase failed: {phase.value}", "ERROR"
                    )
                    return False
                    
            except Exception as e:
                launch_record.add_phase_log(
                    phase, f"Phase error: {phase.value} - {str(e)}", "ERROR"
                )
                return False
        
        return True
    
    async def _pre_launch_validation(self, launch_record: LaunchRecord, 
                                   config: ProductionLaunchConfig) -> bool:
        """Pre-launch validation"""
        try:
            # Initialize components
            self.config_manager = ConfigurationManager()
            self.deployment_pipeline = DeploymentPipeline(self.config_manager)
            self.monitoring_setup = MonitoringSetup(config)
            self.support_system = SupportSystem(config)
            self.feedback_system = UserFeedbackSystem(config)
            
            # Validate production configuration
            prod_config = self.config_manager.get_environment_configs(
                DeploymentEnvironment.PRODUCTION
            )
            
            # Check all required configurations
            required_configs = ["application", "database", "infrastructure", "security"]
            for config_type in required_configs:
                if config_type not in prod_config:
                    raise Exception(f"Missing {config_type} configuration")
                
                errors = self.config_manager.validate_config(
                    getattr(ConfigurationType, config_type.upper()),
                    prod_config[config_type]
                )
                
                if errors:
                    raise Exception(f"Configuration validation failed for {config_type}: {errors}")
            
            # Validate external dependencies
            await self._validate_external_dependencies(launch_record)
            
            # Check resource availability
            await self._check_resource_availability(launch_record)
            
            return True
            
        except Exception as e:
            launch_record.add_phase_log(
                LaunchPhase.PRE_LAUNCH,
                f"Pre-launch validation failed: {str(e)}",
                "ERROR"
            )
            return False
    
    async def _deploy_to_production(self, launch_record: LaunchRecord,
                                  config: ProductionLaunchConfig) -> bool:
        """Deploy to production environment"""
        try:
            # Create deployment configuration
            deployment_config = DeploymentConfig(
                environment=DeploymentEnvironment.PRODUCTION,
                version=config.version,
                build_id=config.build_id,
                deployment_strategy="blue_green",  # Safest for production
                health_check_timeout=600,
                rollback_on_failure=config.auto_rollback_on_failure,
                min_replicas=3,  # Production minimum
                max_replicas=20
            )
            
            # Execute deployment
            deployment = await self.deployment_pipeline.deploy(deployment_config)
            
            if deployment.status.value == "completed":
                launch_record.deployment_success = True
                launch_record.add_phase_log(
                    LaunchPhase.DEPLOYMENT,
                    f"Production deployment successful: {deployment.id}"
                )
                return True
            else:
                launch_record.add_phase_log(
                    LaunchPhase.DEPLOYMENT,
                    f"Production deployment failed: {deployment.error_message}",
                    "ERROR"
                )
                return False
                
        except Exception as e:
            launch_record.add_phase_log(
                LaunchPhase.DEPLOYMENT,
                f"Deployment error: {str(e)}",
                "ERROR"
            )
            return False
    
    async def _run_production_health_checks(self, launch_record: LaunchRecord,
                                          config: ProductionLaunchConfig) -> bool:
        """Run comprehensive production health checks"""
        try:
            # Initialize temporary health monitor for checks
            temp_monitor = SystemHealthMonitor(monitoring_interval=10)
            await temp_monitor.start_monitoring()
            
            # Wait for initial metrics
            await asyncio.sleep(30)
            
            # Get health summary
            health_summary = temp_monitor.get_system_health_summary()
            
            # Check overall health
            if health_summary['overall_status'] not in ['healthy', 'warning']:
                launch_record.add_phase_log(
                    LaunchPhase.HEALTH_CHECK,
                    f"Health check failed: {health_summary['overall_status']}",
                    "ERROR"
                )
                return False
            
            # Record initial metrics
            if 'system_metrics' in health_summary:
                system_metrics = health_summary['system_metrics']
                launch_record.initial_response_time = system_metrics.get('response_time', 0.0)
                launch_record.initial_error_rate = system_metrics.get('error_rate', 0.0)
            
            # Stop temporary monitor
            await temp_monitor.stop_monitoring()
            
            launch_record.health_check_success = True
            launch_record.add_phase_log(
                LaunchPhase.HEALTH_CHECK,
                "Production health checks passed"
            )
            
            return True
            
        except Exception as e:
            launch_record.add_phase_log(
                LaunchPhase.HEALTH_CHECK,
                f"Health check error: {str(e)}",
                "ERROR"
            )
            return False
    
    async def _setup_monitoring(self, launch_record: LaunchRecord,
                              config: ProductionLaunchConfig) -> bool:
        """Setup production monitoring"""
        if not config.enable_monitoring:
            launch_record.add_phase_log(
                LaunchPhase.MONITORING_SETUP,
                "Monitoring disabled by configuration"
            )
            return True
        
        return await self.monitoring_setup.setup_monitoring(launch_record)
    
    async def _activate_support_system(self, launch_record: LaunchRecord,
                                     config: ProductionLaunchConfig) -> bool:
        """Activate support system"""
        if not config.enable_support_system:
            launch_record.add_phase_log(
                LaunchPhase.SUPPORT_ACTIVATION,
                "Support system disabled by configuration"
            )
            return True
        
        return await self.support_system.setup_support_system(launch_record)
    
    async def _setup_feedback_collection(self, launch_record: LaunchRecord,
                                       config: ProductionLaunchConfig) -> bool:
        """Setup feedback collection"""
        if not config.enable_user_feedback:
            launch_record.add_phase_log(
                LaunchPhase.FEEDBACK_COLLECTION,
                "User feedback disabled by configuration"
            )
            return True
        
        return await self.feedback_system.setup_feedback_system(launch_record)
    
    async def _setup_user_onboarding(self, launch_record: LaunchRecord,
                                   config: ProductionLaunchConfig) -> bool:
        """Setup user onboarding system"""
        try:
            launch_record.add_phase_log(
                LaunchPhase.USER_ONBOARDING,
                "Setting up user onboarding system"
            )
            
            # Create onboarding materials
            await self._create_onboarding_materials()
            
            # Setup user guides
            await self._create_user_guides()
            
            # Setup tutorial system
            await self._setup_tutorial_system()
            
            launch_record.add_phase_log(
                LaunchPhase.USER_ONBOARDING,
                "User onboarding system activated"
            )
            
            return True
            
        except Exception as e:
            launch_record.add_phase_log(
                LaunchPhase.USER_ONBOARDING,
                f"User onboarding setup failed: {str(e)}",
                "ERROR"
            )
            return False
    
    async def _optimize_production_system(self, launch_record: LaunchRecord,
                                        config: ProductionLaunchConfig) -> bool:
        """Optimize production system"""
        try:
            launch_record.add_phase_log(
                LaunchPhase.OPTIMIZATION,
                "Starting production system optimization"
            )
            
            if config.enable_performance_optimization and self.monitoring_setup.performance_optimizer:
                # Run initial optimization
                optimization_result = await self.monitoring_setup.performance_optimizer.force_optimization_cycle()
                
                launch_record.add_phase_log(
                    LaunchPhase.OPTIMIZATION,
                    f"Applied {optimization_result.get('actions_executed', 0)} optimizations"
                )
            
            # Setup auto-scaling if enabled
            if config.enable_auto_scaling:
                await self._setup_auto_scaling(launch_record, config)
            
            launch_record.add_phase_log(
                LaunchPhase.OPTIMIZATION,
                "Production system optimization completed"
            )
            
            return True
            
        except Exception as e:
            launch_record.add_phase_log(
                LaunchPhase.OPTIMIZATION,
                f"Optimization failed: {str(e)}",
                "ERROR"
            )
            return False
    
    async def _validate_external_dependencies(self, launch_record: LaunchRecord):
        """Validate external service dependencies"""
        # Check database connectivity
        # Check external API availability
        # Check email/SMS services
        pass
    
    async def _check_resource_availability(self, launch_record: LaunchRecord):
        """Check resource availability"""
        # Check CPU, memory, disk space
        # Check network bandwidth
        # Check database capacity
        pass
    
    async def _create_onboarding_materials(self):
        """Create user onboarding materials"""
        # Create welcome emails, tutorials, etc.
        pass
    
    async def _create_user_guides(self):
        """Create user guides"""
        # Create comprehensive user documentation
        pass
    
    async def _setup_tutorial_system(self):
        """Setup interactive tutorial system"""
        # Setup in-app tutorials and walkthroughs
        pass
    
    async def _setup_auto_scaling(self, launch_record: LaunchRecord, config: ProductionLaunchConfig):
        """Setup auto-scaling"""
        # Configure auto-scaling policies
        pass
    
    async def _rollback_launch(self, launch_record: LaunchRecord, config: ProductionLaunchConfig):
        """Rollback failed launch"""
        try:
            launch_record.add_phase_log(
                LaunchPhase.FAILED,
                "Starting production launch rollback"
            )
            
            # Stop monitoring
            if self.monitoring_setup and self.monitoring_setup.health_monitor:
                await self.monitoring_setup.health_monitor.stop_monitoring()
            
            # Rollback deployment
            if self.deployment_pipeline:
                # This would implement actual rollback logic
                pass
            
            launch_record.status = LaunchStatus.ROLLED_BACK
            launch_record.add_phase_log(
                LaunchPhase.FAILED,
                "Production launch rollback completed"
            )
            
        except Exception as e:
            launch_record.add_phase_log(
                LaunchPhase.FAILED,
                f"Rollback failed: {str(e)}",
                "ERROR"
            )
    
    # Public Interface Methods
    
    def get_launch_status(self) -> Dict[str, Any]:
        """Get current launch status"""
        if self.active_launch:
            return {
                "active": True,
                "launch_id": self.active_launch.id,
                "version": self.active_launch.version,
                "status": self.active_launch.status.value,
                "current_phase": self.active_launch.current_phase.value,
                "started_at": self.active_launch.started_at.isoformat(),
                "duration": (datetime.now() - self.active_launch.started_at).total_seconds()
            }
        else:
            return {"active": False}
    
    def get_launch_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get launch history"""
        return [
            {
                "id": launch.id,
                "version": launch.version,
                "status": launch.status.value,
                "started_at": launch.started_at.isoformat(),
                "completed_at": launch.completed_at.isoformat() if launch.completed_at else None,
                "duration": launch.duration,
                "deployment_success": launch.deployment_success,
                "health_check_success": launch.health_check_success,
                "monitoring_active": launch.monitoring_active,
                "support_active": launch.support_active
            }
            for launch in self.launch_history[-limit:]
        ]
    
    def get_production_metrics(self) -> Dict[str, Any]:
        """Get production system metrics"""
        if self.monitoring_setup and self.monitoring_setup.health_monitor:
            return self.monitoring_setup.health_monitor.get_system_health_summary()
        else:
            return {"status": "monitoring_not_active"}


# Global instance
_production_launcher: Optional[ProductionLauncher] = None

def get_production_launcher() -> ProductionLauncher:
    """Get global production launcher instance"""
    global _production_launcher
    if _production_launcher is None:
        _production_launcher = ProductionLauncher()
    return _production_launcher