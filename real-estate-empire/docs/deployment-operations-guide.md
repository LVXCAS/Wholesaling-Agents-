# Deployment and Operations Guide

## Overview

This guide covers the deployment and operations automation system for the Real Estate Empire AI platform. The system provides automated deployment pipelines, configuration management, backup and recovery, and monitoring capabilities.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Configuration Management](#configuration-management)
3. [Deployment Pipelines](#deployment-pipelines)
4. [Backup and Recovery](#backup-and-recovery)
5. [Monitoring and Logging](#monitoring-and-logging)
6. [Operations Procedures](#operations-procedures)
7. [Troubleshooting](#troubleshooting)

## System Architecture

The deployment automation system consists of several key components:

### Core Components

- **Configuration Manager**: Manages application and infrastructure configurations
- **Deployment Pipeline**: Handles automated deployments with multiple strategies
- **Backup Manager**: Manages backup and disaster recovery operations
- **Health Monitor**: Monitors system health and performance
- **Performance Optimizer**: Optimizes system resources and performance

### Deployment Environments

The system supports multiple deployment environments:

- **Development**: Local development environment
- **Testing**: Automated testing environment
- **Staging**: Pre-production testing environment
- **Production**: Live production environment

## Configuration Management

### Configuration Types

The system manages several types of configurations:

1. **Application Configuration**
   - Database connections
   - API settings
   - Logging configuration
   - Feature flags

2. **Database Configuration**
   - Connection parameters
   - Pool settings
   - Backup settings

3. **Infrastructure Configuration**
   - Resource limits
   - Scaling parameters
   - Network settings

4. **Security Configuration**
   - Authentication settings
   - Encryption parameters
   - Access controls

5. **Monitoring Configuration**
   - Metrics collection
   - Alerting rules
   - Log retention

### Configuration Files

Configurations are stored in YAML files with the naming convention:
```
config/{type}_{environment}.yaml
```

Example files:
- `config/application_production.yaml`
- `config/database_staging.yaml`
- `config/infrastructure_development.yaml`

### Managing Configurations

#### Loading Configuration

```python
from app.core.deployment_automation import get_deployment_system

deployment_system = get_deployment_system()
config_manager = deployment_system.config_manager

# Load application config for production
app_config = config_manager.load_config(
    ConfigurationType.APPLICATION,
    DeploymentEnvironment.PRODUCTION
)
```

#### Saving Configuration

```python
# Update and save configuration
app_config['debug'] = False
app_config['log_level'] = 'INFO'

config_manager.save_config(
    ConfigurationType.APPLICATION,
    DeploymentEnvironment.PRODUCTION,
    app_config
)
```

#### Validating Configuration

```python
# Validate configuration
errors = config_manager.validate_config(
    ConfigurationType.APPLICATION,
    app_config
)

if errors:
    print(f"Configuration errors: {errors}")
```

## Deployment Pipelines

### Deployment Strategies

The system supports multiple deployment strategies:

1. **Rolling Deployment**
   - Gradually replaces instances
   - Zero-downtime deployment
   - Default strategy

2. **Blue-Green Deployment**
   - Deploys to parallel environment
   - Instant traffic switch
   - Easy rollback

3. **Canary Deployment**
   - Gradual traffic migration
   - Risk mitigation
   - Performance monitoring

### Deployment Process

The deployment pipeline consists of the following steps:

1. **Pre-deployment Validation**
   - Configuration validation
   - Dependency checks
   - Pre-deployment hooks

2. **Build Application**
   - Code compilation
   - Asset generation
   - Container building

3. **Run Tests**
   - Unit tests
   - Integration tests
   - API tests

4. **Deploy Infrastructure**
   - Database setup
   - Cache configuration
   - Load balancer setup

5. **Deploy Application**
   - Application deployment
   - Configuration updates
   - Service registration

6. **Health Checks**
   - Application health
   - Database connectivity
   - API endpoint validation

7. **Post-deployment Validation**
   - Final validation
   - Monitoring setup
   - Post-deployment hooks

### Executing Deployments

#### Basic Deployment

```python
from app.core.deployment_automation import get_deployment_system, DeploymentEnvironment

deployment_system = get_deployment_system()

# Deploy to staging
deployment = await deployment_system.deploy_to_environment(
    environment=DeploymentEnvironment.STAGING,
    version="1.2.3"
)

print(f"Deployment status: {deployment.status}")
```

#### Advanced Deployment Configuration

```python
from app.core.deployment_automation import DeploymentConfig

# Create custom deployment configuration
config = DeploymentConfig(
    environment=DeploymentEnvironment.PRODUCTION,
    version="1.2.3",
    deployment_strategy="blue_green",
    health_check_timeout=600,
    rollback_on_failure=True,
    min_replicas=3,
    max_replicas=10
)

# Execute deployment
deployment = await deployment_system.deployment_pipeline.deploy(config)
```

### Monitoring Deployments

#### Check Deployment Status

```python
# Get deployment history
history = deployment_system.get_deployment_history(
    environment=DeploymentEnvironment.PRODUCTION,
    limit=5
)

for deployment in history:
    print(f"Deployment {deployment.id}: {deployment.status}")
    print(f"Version: {deployment.version}")
    print(f"Duration: {deployment.duration}s")
```

#### Deployment Statistics

```python
# Get deployment statistics
stats = deployment_system.deployment_pipeline.get_deployment_statistics()

print(f"Success rate: {stats['success_rate']:.2%}")
print(f"Average deployment time: {stats['average_deployment_time']:.1f}s")
print(f"Active deployments: {stats['active_deployments']}")
```

## Backup and Recovery

### Backup Types

The system supports several backup types:

1. **Full Backup**
   - Complete system backup
   - Database, configuration, and application
   - Recommended for production

2. **Database Backup**
   - Database only
   - Fast and efficient
   - Regular automated backups

3. **Configuration Backup**
   - Configuration files only
   - Before configuration changes
   - Quick recovery option

4. **Application Backup**
   - Application code and assets
   - Before deployments
   - Version control integration

### Creating Backups

#### Manual Backup

```python
# Create full backup
backup = await deployment_system.create_backup(
    backup_type="full",
    environment=DeploymentEnvironment.PRODUCTION
)

print(f"Backup created: {backup['backup_id']}")
print(f"Backup size: {backup['size']} bytes")
```

#### Scheduled Backups

```python
# Setup automated backup schedule
backup_manager = deployment_system.backup_manager

# Configure daily backups with 30-day retention
backup_manager.backup_schedule = "daily"
backup_manager.retention_days = 30

# Create backup
backup = await backup_manager.create_backup("database")
```

### Restoring from Backup

#### List Available Backups

```python
# Get backup history
backups = deployment_system.get_backup_history(limit=10)

for backup in backups:
    if backup['status'] == 'completed':
        print(f"Backup {backup['backup_id']}: {backup['timestamp']}")
        print(f"Type: {backup['backup_type']}")
        print(f"Size: {backup['size']} bytes")
```

#### Restore from Backup

```python
# Restore from specific backup
restore_result = await deployment_system.restore_from_backup(
    backup_id="backup-id-here",
    environment=DeploymentEnvironment.STAGING
)

print(f"Restore status: {restore_result['status']}")
```

### Backup Maintenance

#### Cleanup Old Backups

```python
# Clean up old backups based on retention policy
await deployment_system.backup_manager.cleanup_old_backups()
```

#### Backup Statistics

```python
# Get backup statistics
stats = deployment_system.backup_manager.get_backup_statistics()

print(f"Total backups: {stats['total_backups']}")
print(f"Success rate: {stats['success_rate']:.2%}")
print(f"Total size: {stats['total_backup_size']} bytes")
```

## Monitoring and Logging

### System Health Monitoring

The system includes comprehensive health monitoring:

#### Health Check Components

1. **System Resources**
   - CPU utilization
   - Memory usage
   - Disk space
   - Network performance

2. **Application Health**
   - Service availability
   - Response times
   - Error rates
   - Throughput metrics

3. **Database Health**
   - Connection status
   - Query performance
   - Replication lag
   - Storage usage

4. **Infrastructure Health**
   - Load balancer status
   - Cache performance
   - External service connectivity

#### Monitoring Setup

```python
from app.core.system_health_monitor import get_health_monitor

# Start health monitoring
health_monitor = get_health_monitor(monitoring_interval=30)
await health_monitor.start_monitoring()

# Get health summary
health_summary = health_monitor.get_system_health_summary()
print(f"Overall status: {health_summary['overall_status']}")
```

#### Performance Optimization

```python
from app.core.performance_optimizer import get_performance_optimizer

# Start performance optimization
optimizer = get_performance_optimizer()
await optimizer.start_optimization(health_monitor)

# Get optimization summary
summary = optimizer.get_optimization_summary()
print(f"Optimization status: {summary['optimization_status']}")
```

### Alerting

#### Alert Configuration

Alerts are configured in the monitoring configuration:

```yaml
# config/monitoring_production.yaml
alerting:
  enabled: true
  webhook_url: "https://hooks.slack.com/services/..."
  alert_thresholds:
    cpu_percent: 80
    memory_percent: 85
    error_rate: 0.05
    response_time: 5.0
```

#### Custom Alerts

```python
# Add custom alert callback
def custom_alert_handler(alert):
    print(f"ALERT: {alert.message}")
    # Send to external monitoring system
    
health_monitor.add_alert_callback(custom_alert_handler)
```

### Logging

#### Log Configuration

```yaml
# config/application_production.yaml
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  handlers:
    - type: file
      filename: /var/log/real-estate-empire/app.log
      max_bytes: 10485760  # 10MB
      backup_count: 5
    - type: syslog
      address: localhost:514
      facility: local0
```

#### Structured Logging

```python
import logging
import json

logger = logging.getLogger(__name__)

# Structured log entry
log_data = {
    "event": "deployment_started",
    "deployment_id": deployment.id,
    "environment": deployment.environment.value,
    "version": deployment.version,
    "timestamp": datetime.now().isoformat()
}

logger.info(json.dumps(log_data))
```

## Operations Procedures

### Daily Operations

#### Morning Checklist

1. **System Health Check**
   ```bash
   # Check system status
   python -c "
   from app.core.deployment_automation import get_deployment_system
   system = get_deployment_system()
   status = system.get_system_status()
   print(f'System Status: {status}')
   "
   ```

2. **Review Overnight Deployments**
   ```python
   # Check recent deployments
   history = deployment_system.get_deployment_history(limit=10)
   for deployment in history:
       if deployment.started_at.date() == datetime.now().date():
           print(f"Deployment {deployment.id}: {deployment.status}")
   ```

3. **Check Backup Status**
   ```python
   # Verify recent backups
   backups = deployment_system.get_backup_history(limit=5)
   for backup in backups:
       print(f"Backup {backup['backup_id']}: {backup['status']}")
   ```

4. **Review Alerts**
   ```python
   # Check active alerts
   alerts = health_monitor.get_active_alerts()
   print(f"Active alerts: {len(alerts)}")
   ```

#### Weekly Operations

1. **Performance Review**
   - Review deployment statistics
   - Analyze performance trends
   - Optimize resource allocation

2. **Backup Verification**
   - Test backup restoration
   - Verify backup integrity
   - Update backup policies

3. **Security Updates**
   - Review security configurations
   - Update dependencies
   - Rotate secrets and keys

4. **Capacity Planning**
   - Review resource usage trends
   - Plan for scaling needs
   - Update resource limits

### Emergency Procedures

#### Deployment Rollback

```python
# Emergency rollback procedure
async def emergency_rollback(deployment_id: str):
    # Get deployment record
    deployment = find_deployment(deployment_id)
    
    # Execute rollback
    config = DeploymentConfig(**deployment.config)
    await deployment_system.deployment_pipeline._rollback_deployment(
        deployment, config
    )
    
    print(f"Emergency rollback completed for {deployment_id}")
```

#### System Recovery

```python
# System recovery from backup
async def system_recovery(backup_id: str, environment: str):
    # Set maintenance mode
    deployment_system.set_maintenance_mode(True)
    
    try:
        # Restore from backup
        result = await deployment_system.restore_from_backup(
            backup_id, DeploymentEnvironment(environment)
        )
        
        # Verify system health
        health_summary = health_monitor.get_system_health_summary()
        
        if health_summary['overall_status'] == 'healthy':
            print("System recovery successful")
        else:
            print("System recovery completed with warnings")
            
    finally:
        # Disable maintenance mode
        deployment_system.set_maintenance_mode(False)
```

#### Performance Issues

```python
# Handle performance degradation
async def handle_performance_issues():
    # Force optimization cycle
    result = await optimizer.force_optimization_cycle()
    
    # Check for scaling needs
    if result['actions_identified'] > 0:
        print(f"Applied {result['actions_executed']} optimizations")
    
    # Enable circuit breakers if needed
    error_recovery = optimizer.error_recovery
    
    # Monitor for improvement
    await asyncio.sleep(300)  # Wait 5 minutes
    
    health_summary = health_monitor.get_system_health_summary()
    print(f"System status after optimization: {health_summary['overall_status']}")
```

### Maintenance Procedures

#### Scheduled Maintenance

```python
# Scheduled maintenance procedure
async def scheduled_maintenance():
    # Enable maintenance mode
    deployment_system.set_maintenance_mode(True)
    
    try:
        # Create pre-maintenance backup
        backup = await deployment_system.create_backup("full")
        print(f"Pre-maintenance backup: {backup['backup_id']}")
        
        # Perform maintenance tasks
        await perform_database_maintenance()
        await update_system_dependencies()
        await optimize_system_performance()
        
        # Verify system health
        health_summary = health_monitor.get_system_health_summary()
        
        if health_summary['overall_status'] != 'healthy':
            raise Exception("System health check failed after maintenance")
            
        print("Scheduled maintenance completed successfully")
        
    except Exception as e:
        print(f"Maintenance failed: {e}")
        # Consider rollback procedures
        
    finally:
        # Disable maintenance mode
        deployment_system.set_maintenance_mode(False)
```

#### Database Maintenance

```python
async def perform_database_maintenance():
    # Database optimization tasks
    tasks = [
        "VACUUM ANALYZE",
        "REINDEX DATABASE",
        "UPDATE STATISTICS",
        "CHECK CONSTRAINTS"
    ]
    
    for task in tasks:
        print(f"Executing: {task}")
        # Execute actual database commands
        await asyncio.sleep(1)  # Simulate execution
    
    print("Database maintenance completed")
```

## Troubleshooting

### Common Issues

#### Deployment Failures

**Issue**: Deployment fails during health checks
```
Solution:
1. Check application logs for errors
2. Verify database connectivity
3. Check resource availability
4. Review configuration changes
```

**Issue**: Rollback fails
```
Solution:
1. Check rollback logs
2. Verify previous version availability
3. Manual intervention may be required
4. Consider restore from backup
```

#### Performance Issues

**Issue**: High CPU usage
```
Solution:
1. Check for resource-intensive processes
2. Review recent deployments
3. Scale up resources if needed
4. Enable performance optimization
```

**Issue**: Memory leaks
```
Solution:
1. Monitor memory usage trends
2. Check for memory-intensive operations
3. Restart affected services
4. Review application code for leaks
```

#### Backup Issues

**Issue**: Backup creation fails
```
Solution:
1. Check disk space availability
2. Verify backup directory permissions
3. Check database connectivity
4. Review backup logs for errors
```

**Issue**: Restore fails
```
Solution:
1. Verify backup integrity
2. Check target environment status
3. Ensure sufficient resources
4. Review restore logs
```

### Diagnostic Commands

#### System Status

```python
# Get comprehensive system status
status = deployment_system.get_system_status()
print(json.dumps(status, indent=2))
```

#### Health Check

```python
# Run manual health check
health_summary = health_monitor.get_system_health_summary()
print(f"Overall Status: {health_summary['overall_status']}")

# Get detailed metrics
metrics = health_monitor.get_system_metrics_history(hours=1)
print(f"Recent metrics: {len(metrics)} data points")
```

#### Performance Analysis

```python
# Get performance report
report = health_monitor.get_performance_report()
print(f"Health Score: {report['overall_health_score']}")
print(f"Recommendations: {report['recommendations']}")
```

### Log Analysis

#### Application Logs

```bash
# View recent application logs
tail -f /var/log/real-estate-empire/app.log

# Search for errors
grep -i error /var/log/real-estate-empire/app.log | tail -20

# Filter by deployment ID
grep "deployment_id.*abc123" /var/log/real-estate-empire/app.log
```

#### System Logs

```bash
# Check system logs
journalctl -u real-estate-empire -f

# View deployment logs
journalctl -u real-estate-empire --since "1 hour ago" | grep deployment
```

### Support Contacts

For additional support:

- **Development Team**: dev-team@real-estate-empire.com
- **Operations Team**: ops-team@real-estate-empire.com
- **Emergency Hotline**: +1-555-EMERGENCY

### Additional Resources

- [API Documentation](api-documentation.md)
- [Architecture Guide](architecture-guide.md)
- [Security Guide](security-guide.md)
- [Performance Tuning Guide](performance-tuning.md)

---

*This guide is maintained by the Operations Team. Last updated: 2024-01-15*