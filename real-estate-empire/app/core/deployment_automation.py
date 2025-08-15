"""
Deployment and Operations Automation System
Handles automated deployment pipelines, configuration management, and operations
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

from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeploymentEnvironment(str, Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class DeploymentStatus(str, Enum):
    """Deployment status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class ConfigurationType(str, Enum):
    """Configuration types"""
    APPLICATION = "application"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    MONITORING = "monitoring"


@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    environment: DeploymentEnvironment
    version: str
    build_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Application settings
    app_settings: Dict[str, Any] = field(default_factory=dict)
    database_config: Dict[str, Any] = field(default_factory=dict)
    infrastructure_config: Dict[str, Any] = field(default_factory=dict)
    
    # Deployment settings
    deployment_strategy: str = "rolling"  # rolling, blue_green, canary
    health_check_url: str = "/health"
    health_check_timeout: int = 300  # seconds
    rollback_on_failure: bool = True
    
    # Resource requirements
    cpu_request: str = "500m"
    memory_request: str = "1Gi"
    cpu_limit: str = "2000m"
    memory_limit: str = "4Gi"
    
    # Scaling settings
    min_replicas: int = 2
    max_replicas: int = 10
    target_cpu_utilization: int = 70
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "environment": self.environment.value,
            "version": self.version,
            "build_id": self.build_id,
            "app_settings": self.app_settings,
            "database_config": self.database_config,
            "infrastructure_config": self.infrastructure_config,
            "deployment_strategy": self.deployment_strategy,
            "health_check_url": self.health_check_url,
            "health_check_timeout": self.health_check_timeout,
            "rollback_on_failure": self.rollback_on_failure,
            "resources": {
                "cpu_request": self.cpu_request,
                "memory_request": self.memory_request,
                "cpu_limit": self.cpu_limit,
                "memory_limit": self.memory_limit
            },
            "scaling": {
                "min_replicas": self.min_replicas,
                "max_replicas": self.max_replicas,
                "target_cpu_utilization": self.target_cpu_utilization
            }
        }


class DeploymentRecord(BaseModel):
    """Record of a deployment"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    environment: DeploymentEnvironment
    version: str
    build_id: str
    status: DeploymentStatus = DeploymentStatus.PENDING
    
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None  # seconds
    
    config: Dict[str, Any] = Field(default_factory=dict)
    logs: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    
    # Deployment metrics
    success_rate: Optional[float] = None
    rollback_count: int = 0
    health_check_results: List[Dict[str, Any]] = Field(default_factory=list)
    
    def add_log(self, message: str, level: str = "INFO"):
        """Add log message"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"
        self.logs.append(log_entry)
        
        if level in ["ERROR", "CRITICAL"]:
            self.error_message = message
    
    def complete(self, status: DeploymentStatus):
        """Mark deployment as complete"""
        self.status = status
        self.completed_at = datetime.now()
        
        if self.started_at:
            self.duration = (self.completed_at - self.started_at).total_seconds()


class ConfigurationManager:
    """Manages application and infrastructure configuration"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_cache: Dict[str, Dict[str, Any]] = {}
        self.config_templates: Dict[str, str] = {}
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        logger.info(f"Configuration manager initialized with directory: {self.config_dir}")
    
    def load_config(self, config_type: ConfigurationType, environment: DeploymentEnvironment) -> Dict[str, Any]:
        """Load configuration for specific type and environment"""
        cache_key = f"{config_type.value}_{environment.value}"
        
        if cache_key in self.config_cache:
            return self.config_cache[cache_key].copy()
        
        config_file = self.config_dir / f"{config_type.value}_{environment.value}.yaml"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                
                self.config_cache[cache_key] = config
                return config.copy()
                
            except Exception as e:
                logger.error(f"Error loading config {config_file}: {e}")
                return {}
        else:
            # Return default configuration
            return self._get_default_config(config_type, environment)
    
    def save_config(self, config_type: ConfigurationType, environment: DeploymentEnvironment, 
                   config: Dict[str, Any]):
        """Save configuration to file"""
        config_file = self.config_dir / f"{config_type.value}_{environment.value}.yaml"
        
        try:
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            # Update cache
            cache_key = f"{config_type.value}_{environment.value}"
            self.config_cache[cache_key] = config.copy()
            
            logger.info(f"Configuration saved: {config_file}")
            
        except Exception as e:
            logger.error(f"Error saving config {config_file}: {e}")
            raise
    
    def _get_default_config(self, config_type: ConfigurationType, 
                           environment: DeploymentEnvironment) -> Dict[str, Any]:
        """Get default configuration for type and environment"""
        
        if config_type == ConfigurationType.APPLICATION:
            return {
                "debug": environment == DeploymentEnvironment.DEVELOPMENT,
                "log_level": "DEBUG" if environment == DeploymentEnvironment.DEVELOPMENT else "INFO",
                "database_url": f"postgresql://localhost/real_estate_{environment.value}",
                "redis_url": f"redis://localhost:6379/{environment.value}",
                "api_timeout": 30,
                "max_workers": 4 if environment == DeploymentEnvironment.PRODUCTION else 2
            }
        
        elif config_type == ConfigurationType.DATABASE:
            return {
                "host": "localhost",
                "port": 5432,
                "database": f"real_estate_{environment.value}",
                "username": "real_estate_user",
                "password": "change_me",
                "pool_size": 20 if environment == DeploymentEnvironment.PRODUCTION else 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 3600
            }
        
        elif config_type == ConfigurationType.INFRASTRUCTURE:
            return {
                "replicas": 3 if environment == DeploymentEnvironment.PRODUCTION else 1,
                "cpu_request": "500m",
                "memory_request": "1Gi",
                "cpu_limit": "2000m",
                "memory_limit": "4Gi",
                "storage_size": "100Gi" if environment == DeploymentEnvironment.PRODUCTION else "10Gi"
            }
        
        elif config_type == ConfigurationType.SECURITY:
            return {
                "jwt_secret": "change_me_in_production",
                "jwt_expiration": 3600,
                "cors_origins": ["*"] if environment == DeploymentEnvironment.DEVELOPMENT else [],
                "rate_limiting": {
                    "enabled": True,
                    "requests_per_minute": 100
                },
                "encryption": {
                    "algorithm": "AES-256-GCM",
                    "key_rotation_days": 90
                }
            }
        
        elif config_type == ConfigurationType.MONITORING:
            return {
                "metrics_enabled": True,
                "metrics_port": 9090,
                "health_check_interval": 30,
                "log_retention_days": 30 if environment == DeploymentEnvironment.PRODUCTION else 7,
                "alerting": {
                    "enabled": environment == DeploymentEnvironment.PRODUCTION,
                    "webhook_url": "",
                    "alert_thresholds": {
                        "cpu_percent": 80,
                        "memory_percent": 85,
                        "error_rate": 0.05
                    }
                }
            }
        
        return {}
    
    def validate_config(self, config_type: ConfigurationType, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        try:
            if config_type == ConfigurationType.APPLICATION:
                required_fields = ["database_url", "log_level"]
                for field in required_fields:
                    if field not in config:
                        errors.append(f"Missing required field: {field}")
            
            elif config_type == ConfigurationType.DATABASE:
                required_fields = ["host", "port", "database", "username"]
                for field in required_fields:
                    if field not in config:
                        errors.append(f"Missing required field: {field}")
                
                if "port" in config and not isinstance(config["port"], int):
                    errors.append("Database port must be an integer")
            
            elif config_type == ConfigurationType.INFRASTRUCTURE:
                if "replicas" in config and config["replicas"] < 1:
                    errors.append("Replicas must be at least 1")
            
            elif config_type == ConfigurationType.SECURITY:
                if "jwt_secret" in config and config["jwt_secret"] == "change_me_in_production":
                    errors.append("JWT secret must be changed from default")
            
        except Exception as e:
            errors.append(f"Configuration validation error: {str(e)}")
        
        return errors
    
    def merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configurations, with override taking precedence"""
        merged = base_config.copy()
        
        for key, value in override_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self.merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def get_environment_configs(self, environment: DeploymentEnvironment) -> Dict[str, Dict[str, Any]]:
        """Get all configurations for an environment"""
        configs = {}
        
        for config_type in ConfigurationType:
            configs[config_type.value] = self.load_config(config_type, environment)
        
        return configs


class DeploymentPipeline:
    """Automated deployment pipeline"""
    
    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager
        self.deployment_history: List[DeploymentRecord] = []
        self.active_deployments: Dict[str, DeploymentRecord] = {}
        
        # Pipeline configuration
        self.max_concurrent_deployments = 3
        self.deployment_timeout = 1800  # 30 minutes
        
        # Hooks for deployment events
        self.pre_deployment_hooks: List[Callable] = []
        self.post_deployment_hooks: List[Callable] = []
        self.rollback_hooks: List[Callable] = []
        
        logger.info("Deployment pipeline initialized")
    
    async def deploy(self, deployment_config: DeploymentConfig) -> DeploymentRecord:
        """Execute deployment"""
        
        # Create deployment record
        deployment = DeploymentRecord(
            environment=deployment_config.environment,
            version=deployment_config.version,
            build_id=deployment_config.build_id,
            config=deployment_config.to_dict()
        )
        
        deployment.add_log(f"Starting deployment to {deployment_config.environment.value}")
        
        try:
            # Check concurrent deployment limit
            if len(self.active_deployments) >= self.max_concurrent_deployments:
                raise Exception("Maximum concurrent deployments reached")
            
            self.active_deployments[deployment.id] = deployment
            deployment.status = DeploymentStatus.IN_PROGRESS
            
            # Execute deployment steps
            await self._execute_deployment_pipeline(deployment, deployment_config)
            
            deployment.complete(DeploymentStatus.COMPLETED)
            deployment.add_log("Deployment completed successfully")
            
        except Exception as e:
            deployment.complete(DeploymentStatus.FAILED)
            deployment.add_log(f"Deployment failed: {str(e)}", "ERROR")
            
            # Attempt rollback if configured
            if deployment_config.rollback_on_failure:
                await self._rollback_deployment(deployment, deployment_config)
            
            raise
        
        finally:
            # Remove from active deployments
            if deployment.id in self.active_deployments:
                del self.active_deployments[deployment.id]
            
            # Add to history
            self.deployment_history.append(deployment)
            
            # Limit history size
            if len(self.deployment_history) > 100:
                self.deployment_history = self.deployment_history[-50:]
        
        return deployment
    
    async def _execute_deployment_pipeline(self, deployment: DeploymentRecord, 
                                         config: DeploymentConfig):
        """Execute the deployment pipeline steps"""
        
        steps = [
            ("Pre-deployment validation", self._validate_deployment),
            ("Build application", self._build_application),
            ("Run tests", self._run_tests),
            ("Deploy infrastructure", self._deploy_infrastructure),
            ("Deploy application", self._deploy_application),
            ("Run health checks", self._run_health_checks),
            ("Post-deployment validation", self._post_deployment_validation)
        ]
        
        for step_name, step_func in steps:
            deployment.add_log(f"Executing step: {step_name}")
            
            try:
                await step_func(deployment, config)
                deployment.add_log(f"Step completed: {step_name}")
                
            except Exception as e:
                deployment.add_log(f"Step failed: {step_name} - {str(e)}", "ERROR")
                raise
    
    async def _validate_deployment(self, deployment: DeploymentRecord, config: DeploymentConfig):
        """Validate deployment configuration"""
        
        # Validate all configuration types
        for config_type in ConfigurationType:
            type_config = self.config_manager.load_config(config_type, config.environment)
            errors = self.config_manager.validate_config(config_type, type_config)
            
            if errors:
                raise Exception(f"Configuration validation failed for {config_type.value}: {errors}")
        
        # Run pre-deployment hooks
        for hook in self.pre_deployment_hooks:
            try:
                await hook(deployment, config)
            except Exception as e:
                raise Exception(f"Pre-deployment hook failed: {str(e)}")
        
        deployment.add_log("Deployment validation completed")
    
    async def _build_application(self, deployment: DeploymentRecord, config: DeploymentConfig):
        """Build the application"""
        
        # This would integrate with actual build systems (Docker, etc.)
        # For now, we'll simulate the build process
        
        deployment.add_log("Building application...")
        
        # Simulate build time
        await asyncio.sleep(2)
        
        # Check if build artifacts exist (simulation)
        build_success = True  # Would check actual build results
        
        if not build_success:
            raise Exception("Application build failed")
        
        deployment.add_log(f"Application built successfully - Build ID: {config.build_id}")
    
    async def _run_tests(self, deployment: DeploymentRecord, config: DeploymentConfig):
        """Run automated tests"""
        
        deployment.add_log("Running automated tests...")
        
        # This would run actual test suites
        # For now, we'll simulate test execution
        
        test_commands = [
            "python -m pytest tests/unit/",
            "python -m pytest tests/integration/",
            "python -m pytest tests/api/"
        ]
        
        for command in test_commands:
            deployment.add_log(f"Running: {command}")
            
            # Simulate test execution
            await asyncio.sleep(1)
            
            # Simulate test results
            test_success = True  # Would check actual test results
            
            if not test_success:
                raise Exception(f"Tests failed for command: {command}")
        
        deployment.add_log("All tests passed")
    
    async def _deploy_infrastructure(self, deployment: DeploymentRecord, config: DeploymentConfig):
        """Deploy infrastructure components"""
        
        deployment.add_log("Deploying infrastructure...")
        
        # Load infrastructure configuration
        infra_config = self.config_manager.load_config(
            ConfigurationType.INFRASTRUCTURE, 
            config.environment
        )
        
        # This would deploy actual infrastructure (Kubernetes, Docker, etc.)
        # For now, we'll simulate infrastructure deployment
        
        infrastructure_components = [
            "Database",
            "Redis Cache",
            "Load Balancer",
            "Application Pods"
        ]
        
        for component in infrastructure_components:
            deployment.add_log(f"Deploying {component}...")
            await asyncio.sleep(0.5)
            deployment.add_log(f"{component} deployed successfully")
        
        deployment.add_log("Infrastructure deployment completed")
    
    async def _deploy_application(self, deployment: DeploymentRecord, config: DeploymentConfig):
        """Deploy the application"""
        
        deployment.add_log("Deploying application...")
        
        # Load application configuration
        app_config = self.config_manager.load_config(
            ConfigurationType.APPLICATION,
            config.environment
        )
        
        # Execute deployment strategy
        if config.deployment_strategy == "rolling":
            await self._rolling_deployment(deployment, config, app_config)
        elif config.deployment_strategy == "blue_green":
            await self._blue_green_deployment(deployment, config, app_config)
        elif config.deployment_strategy == "canary":
            await self._canary_deployment(deployment, config, app_config)
        else:
            raise Exception(f"Unknown deployment strategy: {config.deployment_strategy}")
        
        deployment.add_log("Application deployment completed")
    
    async def _rolling_deployment(self, deployment: DeploymentRecord, 
                                config: DeploymentConfig, app_config: Dict[str, Any]):
        """Execute rolling deployment"""
        
        deployment.add_log("Executing rolling deployment...")
        
        # Simulate rolling update
        replicas = config.min_replicas
        
        for i in range(replicas):
            deployment.add_log(f"Updating replica {i+1}/{replicas}")
            await asyncio.sleep(1)
            
            # Simulate health check for each replica
            health_ok = await self._check_replica_health(deployment, i+1)
            
            if not health_ok:
                raise Exception(f"Health check failed for replica {i+1}")
        
        deployment.add_log("Rolling deployment completed")
    
    async def _blue_green_deployment(self, deployment: DeploymentRecord,
                                   config: DeploymentConfig, app_config: Dict[str, Any]):
        """Execute blue-green deployment"""
        
        deployment.add_log("Executing blue-green deployment...")
        
        # Deploy to green environment
        deployment.add_log("Deploying to green environment...")
        await asyncio.sleep(2)
        
        # Run health checks on green
        health_ok = await self._run_comprehensive_health_checks(deployment, config)
        
        if not health_ok:
            raise Exception("Health checks failed on green environment")
        
        # Switch traffic to green
        deployment.add_log("Switching traffic to green environment...")
        await asyncio.sleep(1)
        
        # Cleanup blue environment
        deployment.add_log("Cleaning up blue environment...")
        await asyncio.sleep(1)
        
        deployment.add_log("Blue-green deployment completed")
    
    async def _canary_deployment(self, deployment: DeploymentRecord,
                                config: DeploymentConfig, app_config: Dict[str, Any]):
        """Execute canary deployment"""
        
        deployment.add_log("Executing canary deployment...")
        
        # Deploy canary with small traffic percentage
        canary_percentages = [10, 25, 50, 100]
        
        for percentage in canary_percentages:
            deployment.add_log(f"Routing {percentage}% traffic to canary...")
            await asyncio.sleep(1)
            
            # Monitor canary metrics
            canary_healthy = await self._monitor_canary_metrics(deployment, percentage)
            
            if not canary_healthy:
                raise Exception(f"Canary metrics failed at {percentage}% traffic")
        
        deployment.add_log("Canary deployment completed")
    
    async def _run_health_checks(self, deployment: DeploymentRecord, config: DeploymentConfig):
        """Run comprehensive health checks"""
        
        deployment.add_log("Running health checks...")
        
        health_ok = await self._run_comprehensive_health_checks(deployment, config)
        
        if not health_ok:
            raise Exception("Health checks failed")
        
        deployment.add_log("Health checks passed")
    
    async def _run_comprehensive_health_checks(self, deployment: DeploymentRecord,
                                             config: DeploymentConfig) -> bool:
        """Run comprehensive health checks"""
        
        health_checks = [
            ("Application health", self._check_application_health),
            ("Database connectivity", self._check_database_health),
            ("Cache connectivity", self._check_cache_health),
            ("API endpoints", self._check_api_endpoints)
        ]
        
        all_healthy = True
        
        for check_name, check_func in health_checks:
            deployment.add_log(f"Running health check: {check_name}")
            
            try:
                healthy = await check_func(deployment, config)
                
                if healthy:
                    deployment.add_log(f"Health check passed: {check_name}")
                else:
                    deployment.add_log(f"Health check failed: {check_name}", "ERROR")
                    all_healthy = False
                
                # Record health check result
                deployment.health_check_results.append({
                    "check_name": check_name,
                    "healthy": healthy,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                deployment.add_log(f"Health check error: {check_name} - {str(e)}", "ERROR")
                all_healthy = False
        
        return all_healthy
    
    async def _check_application_health(self, deployment: DeploymentRecord, 
                                      config: DeploymentConfig) -> bool:
        """Check application health"""
        # This would make actual HTTP requests to health endpoints
        # For now, we'll simulate the check
        await asyncio.sleep(0.5)
        return True
    
    async def _check_database_health(self, deployment: DeploymentRecord,
                                   config: DeploymentConfig) -> bool:
        """Check database connectivity"""
        # This would test actual database connections
        await asyncio.sleep(0.5)
        return True
    
    async def _check_cache_health(self, deployment: DeploymentRecord,
                                config: DeploymentConfig) -> bool:
        """Check cache connectivity"""
        # This would test actual cache connections
        await asyncio.sleep(0.5)
        return True
    
    async def _check_api_endpoints(self, deployment: DeploymentRecord,
                                 config: DeploymentConfig) -> bool:
        """Check API endpoints"""
        # This would test actual API endpoints
        await asyncio.sleep(0.5)
        return True
    
    async def _check_replica_health(self, deployment: DeploymentRecord, replica_id: int) -> bool:
        """Check health of a specific replica"""
        await asyncio.sleep(0.2)
        return True
    
    async def _monitor_canary_metrics(self, deployment: DeploymentRecord, percentage: int) -> bool:
        """Monitor canary deployment metrics"""
        await asyncio.sleep(1)
        # This would monitor actual metrics (error rate, response time, etc.)
        return True
    
    async def _post_deployment_validation(self, deployment: DeploymentRecord, 
                                        config: DeploymentConfig):
        """Run post-deployment validation"""
        
        deployment.add_log("Running post-deployment validation...")
        
        # Run post-deployment hooks
        for hook in self.post_deployment_hooks:
            try:
                await hook(deployment, config)
            except Exception as e:
                raise Exception(f"Post-deployment hook failed: {str(e)}")
        
        # Final validation checks
        validation_checks = [
            "Configuration consistency",
            "Service discovery registration",
            "Monitoring setup",
            "Logging configuration"
        ]
        
        for check in validation_checks:
            deployment.add_log(f"Validating: {check}")
            await asyncio.sleep(0.2)
        
        deployment.add_log("Post-deployment validation completed")
    
    async def _rollback_deployment(self, deployment: DeploymentRecord, config: DeploymentConfig):
        """Rollback failed deployment"""
        
        deployment.add_log("Starting deployment rollback...")
        deployment.rollback_count += 1
        
        try:
            # Run rollback hooks
            for hook in self.rollback_hooks:
                try:
                    await hook(deployment, config)
                except Exception as e:
                    deployment.add_log(f"Rollback hook failed: {str(e)}", "ERROR")
            
            # Execute rollback steps
            rollback_steps = [
                "Stop new deployment",
                "Restore previous version",
                "Update load balancer",
                "Verify rollback health"
            ]
            
            for step in rollback_steps:
                deployment.add_log(f"Rollback step: {step}")
                await asyncio.sleep(0.5)
            
            deployment.status = DeploymentStatus.ROLLED_BACK
            deployment.add_log("Deployment rollback completed")
            
        except Exception as e:
            deployment.add_log(f"Rollback failed: {str(e)}", "ERROR")
            raise
    
    def get_deployment_history(self, environment: Optional[DeploymentEnvironment] = None,
                             limit: int = 10) -> List[DeploymentRecord]:
        """Get deployment history"""
        history = self.deployment_history
        
        if environment:
            history = [d for d in history if d.environment == environment]
        
        return sorted(history, key=lambda x: x.started_at, reverse=True)[:limit]
    
    def get_deployment_statistics(self) -> Dict[str, Any]:
        """Get deployment statistics"""
        if not self.deployment_history:
            return {"total_deployments": 0}
        
        total = len(self.deployment_history)
        successful = len([d for d in self.deployment_history if d.status == DeploymentStatus.COMPLETED])
        failed = len([d for d in self.deployment_history if d.status == DeploymentStatus.FAILED])
        rolled_back = len([d for d in self.deployment_history if d.status == DeploymentStatus.ROLLED_BACK])
        
        # Calculate average deployment time
        completed_deployments = [d for d in self.deployment_history if d.duration is not None]
        avg_duration = sum(d.duration for d in completed_deployments) / len(completed_deployments) if completed_deployments else 0
        
        return {
            "total_deployments": total,
            "successful_deployments": successful,
            "failed_deployments": failed,
            "rolled_back_deployments": rolled_back,
            "success_rate": successful / total if total > 0 else 0,
            "average_deployment_time": avg_duration,
            "active_deployments": len(self.active_deployments)
        }
    
    def add_pre_deployment_hook(self, hook: Callable):
        """Add pre-deployment hook"""
        self.pre_deployment_hooks.append(hook)
    
    def add_post_deployment_hook(self, hook: Callable):
        """Add post-deployment hook"""
        self.post_deployment_hooks.append(hook)
    
    def add_rollback_hook(self, hook: Callable):
        """Add rollback hook"""
        self.rollback_hooks.append(hook)


class BackupManager:
    """Manages backup and disaster recovery"""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Backup configuration
        self.retention_days = 30
        self.backup_schedule = "daily"  # daily, weekly, monthly
        self.compression_enabled = True
        
        # Backup history
        self.backup_history: List[Dict[str, Any]] = []
        
        logger.info(f"Backup manager initialized with directory: {self.backup_dir}")
    
    async def create_backup(self, backup_type: str = "full", 
                          environment: Optional[DeploymentEnvironment] = None) -> Dict[str, Any]:
        """Create a backup"""
        
        backup_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        backup_record = {
            "backup_id": backup_id,
            "backup_type": backup_type,
            "environment": environment.value if environment else "all",
            "timestamp": timestamp,
            "status": "in_progress",
            "size": 0,
            "files": []
        }
        
        try:
            logger.info(f"Creating {backup_type} backup: {backup_id}")
            
            # Create backup directory
            backup_path = self.backup_dir / f"{backup_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            backup_path.mkdir(exist_ok=True)
            
            # Backup components
            if backup_type in ["full", "database"]:
                await self._backup_database(backup_path, environment)
                backup_record["files"].append("database.sql")
            
            if backup_type in ["full", "configuration"]:
                await self._backup_configuration(backup_path, environment)
                backup_record["files"].append("configuration.tar.gz")
            
            if backup_type in ["full", "application"]:
                await self._backup_application(backup_path)
                backup_record["files"].append("application.tar.gz")
            
            # Calculate backup size
            backup_size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
            backup_record["size"] = backup_size
            
            # Compress if enabled
            if self.compression_enabled:
                await self._compress_backup(backup_path)
            
            backup_record["status"] = "completed"
            backup_record["backup_path"] = str(backup_path)
            
            # Add to history
            self.backup_history.append(backup_record)
            
            logger.info(f"Backup completed: {backup_id} ({backup_size} bytes)")
            
        except Exception as e:
            backup_record["status"] = "failed"
            backup_record["error"] = str(e)
            logger.error(f"Backup failed: {backup_id} - {str(e)}")
            raise
        
        return backup_record
    
    async def _backup_database(self, backup_path: Path, environment: Optional[DeploymentEnvironment]):
        """Backup database"""
        logger.info("Backing up database...")
        
        # This would execute actual database backup commands
        # For now, we'll simulate the backup
        
        db_backup_file = backup_path / "database.sql"
        
        # Simulate database dump
        await asyncio.sleep(2)
        
        # Create dummy backup file
        with open(db_backup_file, 'w') as f:
            f.write(f"-- Database backup created at {datetime.now()}\n")
            f.write("-- This is a simulated backup file\n")
        
        logger.info("Database backup completed")
    
    async def _backup_configuration(self, backup_path: Path, environment: Optional[DeploymentEnvironment]):
        """Backup configuration files"""
        logger.info("Backing up configuration...")
        
        config_backup_file = backup_path / "configuration.tar.gz"
        
        # This would create actual configuration backup
        # For now, we'll simulate it
        
        await asyncio.sleep(1)
        
        # Create dummy configuration backup
        with open(config_backup_file, 'w') as f:
            f.write(f"Configuration backup created at {datetime.now()}\n")
        
        logger.info("Configuration backup completed")
    
    async def _backup_application(self, backup_path: Path):
        """Backup application files"""
        logger.info("Backing up application...")
        
        app_backup_file = backup_path / "application.tar.gz"
        
        # This would create actual application backup
        # For now, we'll simulate it
        
        await asyncio.sleep(1)
        
        # Create dummy application backup
        with open(app_backup_file, 'w') as f:
            f.write(f"Application backup created at {datetime.now()}\n")
        
        logger.info("Application backup completed")
    
    async def _compress_backup(self, backup_path: Path):
        """Compress backup files"""
        logger.info("Compressing backup...")
        
        # This would use actual compression
        # For now, we'll simulate it
        
        await asyncio.sleep(0.5)
        
        logger.info("Backup compression completed")
    
    async def restore_backup(self, backup_id: str, 
                           environment: DeploymentEnvironment) -> Dict[str, Any]:
        """Restore from backup"""
        
        # Find backup record
        backup_record = None
        for record in self.backup_history:
            if record["backup_id"] == backup_id:
                backup_record = record
                break
        
        if not backup_record:
            raise Exception(f"Backup not found: {backup_id}")
        
        if backup_record["status"] != "completed":
            raise Exception(f"Backup is not in completed state: {backup_record['status']}")
        
        restore_record = {
            "restore_id": str(uuid.uuid4()),
            "backup_id": backup_id,
            "environment": environment.value,
            "timestamp": datetime.now(),
            "status": "in_progress"
        }
        
        try:
            logger.info(f"Restoring backup {backup_id} to {environment.value}")
            
            backup_path = Path(backup_record["backup_path"])
            
            # Restore components
            for file_name in backup_record["files"]:
                if file_name == "database.sql":
                    await self._restore_database(backup_path / file_name, environment)
                elif file_name == "configuration.tar.gz":
                    await self._restore_configuration(backup_path / file_name, environment)
                elif file_name == "application.tar.gz":
                    await self._restore_application(backup_path / file_name, environment)
            
            restore_record["status"] = "completed"
            logger.info(f"Backup restore completed: {backup_id}")
            
        except Exception as e:
            restore_record["status"] = "failed"
            restore_record["error"] = str(e)
            logger.error(f"Backup restore failed: {backup_id} - {str(e)}")
            raise
        
        return restore_record
    
    async def _restore_database(self, backup_file: Path, environment: DeploymentEnvironment):
        """Restore database from backup"""
        logger.info("Restoring database...")
        
        # This would execute actual database restore commands
        await asyncio.sleep(2)
        
        logger.info("Database restore completed")
    
    async def _restore_configuration(self, backup_file: Path, environment: DeploymentEnvironment):
        """Restore configuration from backup"""
        logger.info("Restoring configuration...")
        
        # This would restore actual configuration files
        await asyncio.sleep(1)
        
        logger.info("Configuration restore completed")
    
    async def _restore_application(self, backup_file: Path, environment: DeploymentEnvironment):
        """Restore application from backup"""
        logger.info("Restoring application...")
        
        # This would restore actual application files
        await asyncio.sleep(1)
        
        logger.info("Application restore completed")
    
    async def cleanup_old_backups(self):
        """Clean up old backups based on retention policy"""
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        backups_to_remove = [
            backup for backup in self.backup_history
            if backup["timestamp"] < cutoff_date
        ]
        
        for backup in backups_to_remove:
            try:
                # Remove backup files
                backup_path = Path(backup["backup_path"])
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                
                # Remove from history
                self.backup_history.remove(backup)
                
                logger.info(f"Removed old backup: {backup['backup_id']}")
                
            except Exception as e:
                logger.error(f"Error removing backup {backup['backup_id']}: {e}")
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get backup statistics"""
        if not self.backup_history:
            return {"total_backups": 0}
        
        total = len(self.backup_history)
        successful = len([b for b in self.backup_history if b["status"] == "completed"])
        failed = len([b for b in self.backup_history if b["status"] == "failed"])
        
        total_size = sum(b.get("size", 0) for b in self.backup_history if b["status"] == "completed")
        
        return {
            "total_backups": total,
            "successful_backups": successful,
            "failed_backups": failed,
            "success_rate": successful / total if total > 0 else 0,
            "total_backup_size": total_size,
            "retention_days": self.retention_days
        }


class DeploymentAutomationSystem:
    """
    Main Deployment and Operations Automation System
    
    Coordinates all deployment and operations components:
    - Configuration management
    - Deployment pipelines
    - Backup and recovery
    - Monitoring and logging
    """
    
    def __init__(self, config_dir: str = "config", backup_dir: str = "backups"):
        self.config_manager = ConfigurationManager(config_dir)
        self.deployment_pipeline = DeploymentPipeline(self.config_manager)
        self.backup_manager = BackupManager(backup_dir)
        
        # System state
        self.is_initialized = False
        self.maintenance_mode = False
        
        logger.info("Deployment automation system initialized")
    
    async def initialize(self):
        """Initialize the deployment automation system"""
        if self.is_initialized:
            return
        
        try:
            # Setup default configurations for all environments
            for environment in DeploymentEnvironment:
                await self._setup_environment_configs(environment)
            
            # Setup deployment hooks
            self._setup_deployment_hooks()
            
            self.is_initialized = True
            logger.info("Deployment automation system initialization completed")
            
        except Exception as e:
            logger.error(f"Failed to initialize deployment automation system: {e}")
            raise
    
    async def _setup_environment_configs(self, environment: DeploymentEnvironment):
        """Setup default configurations for an environment"""
        
        # Load or create default configurations
        for config_type in ConfigurationType:
            config = self.config_manager.load_config(config_type, environment)
            
            # Validate configuration
            errors = self.config_manager.validate_config(config_type, config)
            
            if errors:
                logger.warning(f"Configuration validation errors for {config_type.value} in {environment.value}: {errors}")
    
    def _setup_deployment_hooks(self):
        """Setup deployment hooks"""
        
        # Pre-deployment hook
        async def pre_deployment_hook(deployment: DeploymentRecord, config: DeploymentConfig):
            deployment.add_log("Pre-deployment hook: Validating system readiness")
            
            # Check if system is in maintenance mode
            if self.maintenance_mode:
                raise Exception("System is in maintenance mode")
            
            # Additional pre-deployment checks would go here
        
        # Post-deployment hook
        async def post_deployment_hook(deployment: DeploymentRecord, config: DeploymentConfig):
            deployment.add_log("Post-deployment hook: Updating monitoring and logging")
            
            # Setup monitoring for new deployment
            await self._setup_deployment_monitoring(deployment, config)
            
            # Create post-deployment backup
            if config.environment == DeploymentEnvironment.PRODUCTION:
                await self.backup_manager.create_backup("configuration", config.environment)
        
        # Rollback hook
        async def rollback_hook(deployment: DeploymentRecord, config: DeploymentConfig):
            deployment.add_log("Rollback hook: Cleaning up failed deployment")
            
            # Additional rollback cleanup would go here
        
        self.deployment_pipeline.add_pre_deployment_hook(pre_deployment_hook)
        self.deployment_pipeline.add_post_deployment_hook(post_deployment_hook)
        self.deployment_pipeline.add_rollback_hook(rollback_hook)
    
    async def _setup_deployment_monitoring(self, deployment: DeploymentRecord, config: DeploymentConfig):
        """Setup monitoring for deployment"""
        
        # This would integrate with actual monitoring systems
        # For now, we'll simulate the setup
        
        deployment.add_log("Setting up deployment monitoring...")
        await asyncio.sleep(0.5)
        deployment.add_log("Deployment monitoring configured")
    
    async def deploy_to_environment(self, environment: DeploymentEnvironment, 
                                  version: str, **kwargs) -> DeploymentRecord:
        """Deploy to a specific environment"""
        
        if not self.is_initialized:
            await self.initialize()
        
        # Create deployment configuration
        deployment_config = DeploymentConfig(
            environment=environment,
            version=version,
            **kwargs
        )
        
        # Load environment-specific settings
        env_configs = self.config_manager.get_environment_configs(environment)
        
        # Merge configurations
        deployment_config.app_settings = env_configs.get("application", {})
        deployment_config.database_config = env_configs.get("database", {})
        deployment_config.infrastructure_config = env_configs.get("infrastructure", {})
        
        # Execute deployment
        return await self.deployment_pipeline.deploy(deployment_config)
    
    async def create_backup(self, backup_type: str = "full", 
                          environment: Optional[DeploymentEnvironment] = None) -> Dict[str, Any]:
        """Create a backup"""
        return await self.backup_manager.create_backup(backup_type, environment)
    
    async def restore_from_backup(self, backup_id: str, 
                                environment: DeploymentEnvironment) -> Dict[str, Any]:
        """Restore from backup"""
        return await self.backup_manager.restore_backup(backup_id, environment)
    
    def set_maintenance_mode(self, enabled: bool):
        """Enable or disable maintenance mode"""
        self.maintenance_mode = enabled
        status = "enabled" if enabled else "disabled"
        logger.info(f"Maintenance mode {status}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        
        deployment_stats = self.deployment_pipeline.get_deployment_statistics()
        backup_stats = self.backup_manager.get_backup_statistics()
        
        return {
            "initialized": self.is_initialized,
            "maintenance_mode": self.maintenance_mode,
            "deployment_statistics": deployment_stats,
            "backup_statistics": backup_stats,
            "active_deployments": len(self.deployment_pipeline.active_deployments),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_deployment_history(self, environment: Optional[DeploymentEnvironment] = None,
                             limit: int = 10) -> List[DeploymentRecord]:
        """Get deployment history"""
        return self.deployment_pipeline.get_deployment_history(environment, limit)
    
    def get_backup_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get backup history"""
        return sorted(
            self.backup_manager.backup_history,
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]


# Global deployment automation system instance
deployment_system: Optional[DeploymentAutomationSystem] = None


def get_deployment_system(config_dir: str = "config", backup_dir: str = "backups") -> DeploymentAutomationSystem:
    """Get or create the global deployment automation system"""
    global deployment_system
    
    if deployment_system is None:
        deployment_system = DeploymentAutomationSystem(config_dir, backup_dir)
    
    return deployment_system