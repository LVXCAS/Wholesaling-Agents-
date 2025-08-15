"""
System Health Monitoring Dashboard
Real-time monitoring of agent performance, system resources, and workflow health
"""

import asyncio
import logging
import psutil
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json
import uuid

from pydantic import BaseModel, Field

from .agent_state import AgentState, AgentType, WorkflowStatus
from .workflow_orchestrator import WorkflowMetrics
from .shared_memory import SharedMemoryManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """System health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """Types of metrics to monitor"""
    SYSTEM_RESOURCE = "system_resource"
    AGENT_PERFORMANCE = "agent_performance"
    WORKFLOW_HEALTH = "workflow_health"
    COMMUNICATION = "communication"
    BUSINESS_KPI = "business_kpi"


@dataclass
class SystemMetrics:
    """System resource metrics"""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # CPU metrics
    cpu_percent: float = 0.0
    cpu_count: int = 0
    load_average: List[float] = field(default_factory=list)
    
    # Memory metrics
    memory_total: int = 0
    memory_available: int = 0
    memory_percent: float = 0.0
    memory_used: int = 0
    
    # Disk metrics
    disk_total: int = 0
    disk_used: int = 0
    disk_free: int = 0
    disk_percent: float = 0.0
    
    # Network metrics
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    network_packets_sent: int = 0
    network_packets_recv: int = 0
    
    # Process metrics
    process_count: int = 0
    thread_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu": {
                "percent": self.cpu_percent,
                "count": self.cpu_count,
                "load_average": self.load_average
            },
            "memory": {
                "total": self.memory_total,
                "available": self.memory_available,
                "percent": self.memory_percent,
                "used": self.memory_used
            },
            "disk": {
                "total": self.disk_total,
                "used": self.disk_used,
                "free": self.disk_free,
                "percent": self.disk_percent
            },
            "network": {
                "bytes_sent": self.network_bytes_sent,
                "bytes_recv": self.network_bytes_recv,
                "packets_sent": self.network_packets_sent,
                "packets_recv": self.network_packets_recv
            },
            "processes": {
                "count": self.process_count,
                "threads": self.thread_count
            }
        }


@dataclass
class AgentHealthMetrics:
    """Agent-specific health metrics"""
    agent_type: str
    agent_name: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Performance metrics
    response_time_avg: float = 0.0
    response_time_p95: float = 0.0
    success_rate: float = 1.0
    error_rate: float = 0.0
    
    # Execution metrics
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_pending: int = 0
    execution_time_avg: float = 0.0
    
    # Resource usage
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    
    # Status
    status: HealthStatus = HealthStatus.HEALTHY
    last_activity: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "agent_type": self.agent_type,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp.isoformat(),
            "performance": {
                "response_time_avg": self.response_time_avg,
                "response_time_p95": self.response_time_p95,
                "success_rate": self.success_rate,
                "error_rate": self.error_rate
            },
            "execution": {
                "tasks_completed": self.tasks_completed,
                "tasks_failed": self.tasks_failed,
                "tasks_pending": self.tasks_pending,
                "execution_time_avg": self.execution_time_avg
            },
            "resources": {
                "memory_usage": self.memory_usage,
                "cpu_usage": self.cpu_usage
            },
            "status": self.status.value,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None
        }


class HealthAlert(BaseModel):
    """Health monitoring alert"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    severity: AlertSeverity
    metric_type: MetricType
    component: str  # Agent name, system component, etc.
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def resolve(self):
        """Mark alert as resolved"""
        self.resolved = True
        self.resolved_at = datetime.now()


class WorkflowHealthMetrics(BaseModel):
    """Workflow health metrics"""
    workflow_id: str
    status: WorkflowStatus
    current_phase: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Performance metrics
    execution_time: float = 0.0
    phases_completed: int = 0
    phases_failed: int = 0
    
    # Deal metrics
    deals_processed: int = 0
    deals_successful: int = 0
    deals_failed: int = 0
    
    # Agent coordination
    agent_handoffs: int = 0
    agent_failures: int = 0
    communication_delays: float = 0.0
    
    # Resource utilization
    memory_peak: float = 0.0
    cpu_peak: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value if isinstance(self.status, WorkflowStatus) else self.status,
            "current_phase": self.current_phase,
            "performance": {
                "execution_time": self.execution_time,
                "phases_completed": self.phases_completed,
                "phases_failed": self.phases_failed
            },
            "deals": {
                "processed": self.deals_processed,
                "successful": self.deals_successful,
                "failed": self.deals_failed
            },
            "coordination": {
                "agent_handoffs": self.agent_handoffs,
                "agent_failures": self.agent_failures,
                "communication_delays": self.communication_delays
            },
            "resources": {
                "memory_peak": self.memory_peak,
                "cpu_peak": self.cpu_peak
            }
        }


class SystemHealthMonitor:
    """
    System Health Monitoring Dashboard
    
    Provides real-time monitoring of:
    - System resource utilization
    - Agent performance and health
    - Workflow execution status
    - Communication metrics
    - Business KPIs
    """
    
    def __init__(self, monitoring_interval: int = 30):
        self.monitoring_interval = monitoring_interval
        
        # Monitoring state
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Metrics storage
        self.system_metrics_history: List[SystemMetrics] = []
        self.agent_metrics: Dict[str, AgentHealthMetrics] = {}
        self.workflow_metrics: Dict[str, WorkflowHealthMetrics] = {}
        self.active_alerts: List[HealthAlert] = []
        self.resolved_alerts: List[HealthAlert] = []
        
        # Thresholds for alerts
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "agent_response_time": 30.0,  # seconds
            "agent_error_rate": 0.1,  # 10%
            "workflow_execution_time": 3600.0,  # 1 hour
        }
        
        # Metrics retention
        self.max_history_size = 1000
        self.metrics_retention_hours = 24
        
        # Alert callbacks
        self.alert_callbacks: List[Callable[[HealthAlert], None]] = []
        
        # Shared memory for cross-component communication
        self.shared_memory = SharedMemoryManager()
        
        logger.info("System Health Monitor initialized")
    
    async def start_monitoring(self):
        """Start the health monitoring system"""
        if self.is_monitoring:
            logger.warning("Health monitoring is already running")
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("System health monitoring started")
    
    async def stop_monitoring(self):
        """Stop the health monitoring system"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("System health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect system metrics
                system_metrics = await self._collect_system_metrics()
                self.system_metrics_history.append(system_metrics)
                
                # Check system health alerts
                await self._check_system_alerts(system_metrics)
                
                # Collect agent metrics
                await self._collect_agent_metrics()
                
                # Check agent health alerts
                await self._check_agent_alerts()
                
                # Collect workflow metrics
                await self._collect_workflow_metrics()
                
                # Check workflow health alerts
                await self._check_workflow_alerts()
                
                # Clean up old metrics
                await self._cleanup_old_metrics()
                
                # Wait for next monitoring cycle
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system resource metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else []
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Process metrics
            process_count = len(psutil.pids())
            
            # Thread count (approximate)
            thread_count = 0
            for proc in psutil.process_iter(['num_threads']):
                try:
                    thread_count += proc.info['num_threads'] or 0
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                load_average=load_avg,
                memory_total=memory.total,
                memory_available=memory.available,
                memory_percent=memory.percent,
                memory_used=memory.used,
                disk_total=disk.total,
                disk_used=disk.used,
                disk_free=disk.free,
                disk_percent=disk.percent,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                network_packets_sent=network.packets_sent,
                network_packets_recv=network.packets_recv,
                process_count=process_count,
                thread_count=thread_count
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics()
    
    async def _collect_agent_metrics(self):
        """Collect agent performance metrics"""
        try:
            # This would integrate with actual agent instances
            # For now, we'll simulate agent metrics collection
            
            agent_types = ["scout", "analyst", "negotiator", "contract", "portfolio"]
            
            for agent_type in agent_types:
                # Get or create agent metrics
                if agent_type not in self.agent_metrics:
                    self.agent_metrics[agent_type] = AgentHealthMetrics(
                        agent_type=agent_type,
                        agent_name=f"{agent_type}_agent"
                    )
                
                agent_metrics = self.agent_metrics[agent_type]
                
                # Update metrics (this would come from actual agent monitoring)
                agent_metrics.timestamp = datetime.now()
                agent_metrics.last_activity = datetime.now()
                
                # Simulate some metrics updates
                import random
                agent_metrics.response_time_avg = random.uniform(1.0, 10.0)
                agent_metrics.success_rate = random.uniform(0.85, 1.0)
                agent_metrics.error_rate = 1.0 - agent_metrics.success_rate
                agent_metrics.memory_usage = random.uniform(50.0, 200.0)  # MB
                agent_metrics.cpu_usage = random.uniform(5.0, 25.0)  # %
                
                # Determine health status
                if agent_metrics.error_rate > 0.2:
                    agent_metrics.status = HealthStatus.CRITICAL
                elif agent_metrics.error_rate > 0.1:
                    agent_metrics.status = HealthStatus.WARNING
                elif agent_metrics.response_time_avg > 20.0:
                    agent_metrics.status = HealthStatus.DEGRADED
                else:
                    agent_metrics.status = HealthStatus.HEALTHY
                
        except Exception as e:
            logger.error(f"Error collecting agent metrics: {e}")
    
    async def _collect_workflow_metrics(self):
        """Collect workflow health metrics"""
        try:
            # This would integrate with actual workflow orchestrator
            # For now, we'll simulate workflow metrics
            
            from .workflow_orchestrator import get_workflow_orchestrator
            
            try:
                orchestrator = get_workflow_orchestrator()
                workflow_metrics = orchestrator.get_workflow_metrics()
                
                workflow_health = WorkflowHealthMetrics(
                    workflow_id=workflow_metrics.get("workflow_id", "unknown"),
                    status=WorkflowStatus.RUNNING,
                    current_phase=workflow_metrics.get("current_phase", "unknown"),
                    execution_time=workflow_metrics.get("execution_time", 0.0),
                    deals_processed=workflow_metrics.get("total_deals_processed", 0),
                    deals_successful=workflow_metrics.get("deals_closed", 0),
                    agent_handoffs=workflow_metrics.get("cross_agent_handoffs", 0)
                )
                
                self.workflow_metrics[workflow_health.workflow_id] = workflow_health
                
            except Exception as e:
                logger.debug(f"Could not collect workflow metrics: {e}")
                
        except Exception as e:
            logger.error(f"Error collecting workflow metrics: {e}")
    
    async def _check_system_alerts(self, metrics: SystemMetrics):
        """Check for system resource alerts"""
        try:
            # CPU alert
            if metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
                await self._create_alert(
                    severity=AlertSeverity.WARNING,
                    metric_type=MetricType.SYSTEM_RESOURCE,
                    component="cpu",
                    message=f"High CPU usage: {metrics.cpu_percent:.1f}%",
                    current_value=metrics.cpu_percent,
                    threshold_value=self.alert_thresholds["cpu_percent"]
                )
            
            # Memory alert
            if metrics.memory_percent > self.alert_thresholds["memory_percent"]:
                await self._create_alert(
                    severity=AlertSeverity.WARNING,
                    metric_type=MetricType.SYSTEM_RESOURCE,
                    component="memory",
                    message=f"High memory usage: {metrics.memory_percent:.1f}%",
                    current_value=metrics.memory_percent,
                    threshold_value=self.alert_thresholds["memory_percent"]
                )
            
            # Disk alert
            if metrics.disk_percent > self.alert_thresholds["disk_percent"]:
                await self._create_alert(
                    severity=AlertSeverity.CRITICAL,
                    metric_type=MetricType.SYSTEM_RESOURCE,
                    component="disk",
                    message=f"High disk usage: {metrics.disk_percent:.1f}%",
                    current_value=metrics.disk_percent,
                    threshold_value=self.alert_thresholds["disk_percent"]
                )
                
        except Exception as e:
            logger.error(f"Error checking system alerts: {e}")
    
    async def _check_agent_alerts(self):
        """Check for agent performance alerts"""
        try:
            for agent_name, metrics in self.agent_metrics.items():
                # Response time alert
                if metrics.response_time_avg > self.alert_thresholds["agent_response_time"]:
                    await self._create_alert(
                        severity=AlertSeverity.WARNING,
                        metric_type=MetricType.AGENT_PERFORMANCE,
                        component=agent_name,
                        message=f"Slow agent response: {metrics.response_time_avg:.1f}s",
                        current_value=metrics.response_time_avg,
                        threshold_value=self.alert_thresholds["agent_response_time"]
                    )
                
                # Error rate alert
                if metrics.error_rate > self.alert_thresholds["agent_error_rate"]:
                    await self._create_alert(
                        severity=AlertSeverity.ERROR,
                        metric_type=MetricType.AGENT_PERFORMANCE,
                        component=agent_name,
                        message=f"High agent error rate: {metrics.error_rate:.1%}",
                        current_value=metrics.error_rate,
                        threshold_value=self.alert_thresholds["agent_error_rate"]
                    )
                
                # Agent offline alert
                if metrics.last_activity:
                    time_since_activity = (datetime.now() - metrics.last_activity).total_seconds()
                    if time_since_activity > 300:  # 5 minutes
                        await self._create_alert(
                            severity=AlertSeverity.CRITICAL,
                            metric_type=MetricType.AGENT_PERFORMANCE,
                            component=agent_name,
                            message=f"Agent appears offline: {time_since_activity:.0f}s since last activity",
                            current_value=time_since_activity,
                            threshold_value=300.0
                        )
                        
        except Exception as e:
            logger.error(f"Error checking agent alerts: {e}")
    
    async def _check_workflow_alerts(self):
        """Check for workflow health alerts"""
        try:
            for workflow_id, metrics in self.workflow_metrics.items():
                # Long execution time alert
                if metrics.execution_time > self.alert_thresholds["workflow_execution_time"]:
                    await self._create_alert(
                        severity=AlertSeverity.WARNING,
                        metric_type=MetricType.WORKFLOW_HEALTH,
                        component=workflow_id,
                        message=f"Long workflow execution: {metrics.execution_time:.0f}s",
                        current_value=metrics.execution_time,
                        threshold_value=self.alert_thresholds["workflow_execution_time"]
                    )
                
                # High failure rate alert
                if metrics.deals_processed > 0:
                    failure_rate = metrics.deals_failed / metrics.deals_processed
                    if failure_rate > 0.2:  # 20% failure rate
                        await self._create_alert(
                            severity=AlertSeverity.ERROR,
                            metric_type=MetricType.WORKFLOW_HEALTH,
                            component=workflow_id,
                            message=f"High workflow failure rate: {failure_rate:.1%}",
                            current_value=failure_rate,
                            threshold_value=0.2
                        )
                        
        except Exception as e:
            logger.error(f"Error checking workflow alerts: {e}")
    
    async def _create_alert(self, severity: AlertSeverity, metric_type: MetricType, 
                           component: str, message: str, current_value: Optional[float] = None,
                           threshold_value: Optional[float] = None, details: Optional[Dict[str, Any]] = None):
        """Create a new health alert"""
        try:
            # Check if similar alert already exists
            existing_alert = None
            for alert in self.active_alerts:
                if (alert.component == component and 
                    alert.metric_type == metric_type and 
                    not alert.resolved):
                    existing_alert = alert
                    break
            
            if existing_alert:
                # Update existing alert
                existing_alert.timestamp = datetime.now()
                existing_alert.current_value = current_value
                existing_alert.details = details or {}
            else:
                # Create new alert
                alert = HealthAlert(
                    severity=severity,
                    metric_type=metric_type,
                    component=component,
                    message=message,
                    current_value=current_value,
                    threshold_value=threshold_value,
                    details=details or {}
                )
                
                self.active_alerts.append(alert)
                
                # Notify alert callbacks
                for callback in self.alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        logger.error(f"Error in alert callback: {e}")
                
                logger.warning(f"Health alert created: {message}")
                
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics to prevent memory bloat"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.metrics_retention_hours)
            
            # Clean up system metrics
            self.system_metrics_history = [
                m for m in self.system_metrics_history 
                if m.timestamp > cutoff_time
            ]
            
            # Limit history size
            if len(self.system_metrics_history) > self.max_history_size:
                self.system_metrics_history = self.system_metrics_history[-self.max_history_size:]
            
            # Clean up resolved alerts
            self.resolved_alerts = [
                a for a in self.resolved_alerts
                if a.resolved_at and a.resolved_at > cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")
    
    # Public Interface Methods
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        try:
            # Get latest system metrics
            latest_system = self.system_metrics_history[-1] if self.system_metrics_history else None
            
            # Calculate overall health status
            critical_alerts = [a for a in self.active_alerts if a.severity == AlertSeverity.CRITICAL and not a.resolved]
            error_alerts = [a for a in self.active_alerts if a.severity == AlertSeverity.ERROR and not a.resolved]
            warning_alerts = [a for a in self.active_alerts if a.severity == AlertSeverity.WARNING and not a.resolved]
            
            if critical_alerts:
                overall_status = HealthStatus.CRITICAL
            elif error_alerts:
                overall_status = HealthStatus.DEGRADED
            elif warning_alerts:
                overall_status = HealthStatus.WARNING
            else:
                overall_status = HealthStatus.HEALTHY
            
            # Agent health summary
            agent_health = {}
            for agent_name, metrics in self.agent_metrics.items():
                agent_health[agent_name] = {
                    "status": metrics.status.value,
                    "success_rate": metrics.success_rate,
                    "response_time": metrics.response_time_avg,
                    "last_activity": metrics.last_activity.isoformat() if metrics.last_activity else None
                }
            
            # Workflow health summary
            workflow_health = {}
            for workflow_id, metrics in self.workflow_metrics.items():
                workflow_health[workflow_id] = {
                    "status": metrics.status.value if isinstance(metrics.status, WorkflowStatus) else metrics.status,
                    "current_phase": metrics.current_phase,
                    "execution_time": metrics.execution_time,
                    "deals_processed": metrics.deals_processed,
                    "success_rate": metrics.deals_successful / max(metrics.deals_processed, 1)
                }
            
            return {
                "overall_status": overall_status.value,
                "timestamp": datetime.now().isoformat(),
                "system_metrics": latest_system.to_dict() if latest_system else {},
                "agent_health": agent_health,
                "workflow_health": workflow_health,
                "alerts": {
                    "critical": len(critical_alerts),
                    "error": len(error_alerts),
                    "warning": len(warning_alerts),
                    "total_active": len(self.active_alerts)
                },
                "monitoring_status": "active" if self.is_monitoring else "inactive"
            }
            
        except Exception as e:
            logger.error(f"Error getting system health summary: {e}")
            return {
                "overall_status": HealthStatus.OFFLINE.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return [alert.dict() for alert in self.active_alerts if not alert.resolved]
    
    def get_system_metrics_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get system metrics history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            metrics.to_dict() 
            for metrics in self.system_metrics_history 
            if metrics.timestamp > cutoff_time
        ]
    
    def get_agent_metrics(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get agent performance metrics"""
        if agent_name:
            if agent_name in self.agent_metrics:
                return self.agent_metrics[agent_name].to_dict()
            else:
                return {}
        else:
            return {
                name: metrics.to_dict() 
                for name, metrics in self.agent_metrics.items()
            }
    
    def get_workflow_metrics(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """Get workflow health metrics"""
        if workflow_id:
            if workflow_id in self.workflow_metrics:
                return self.workflow_metrics[workflow_id].to_dict()
            else:
                return {}
        else:
            return {
                wf_id: metrics.to_dict() 
                for wf_id, metrics in self.workflow_metrics.items()
            }
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert"""
        try:
            for alert in self.active_alerts:
                if alert.id == alert_id and not alert.resolved:
                    alert.resolve()
                    self.resolved_alerts.append(alert)
                    logger.info(f"Alert resolved: {alert.message}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return False
    
    def add_alert_callback(self, callback: Callable[[HealthAlert], None]):
        """Add a callback for new alerts"""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[HealthAlert], None]):
        """Remove an alert callback"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def update_alert_thresholds(self, thresholds: Dict[str, float]):
        """Update alert thresholds"""
        self.alert_thresholds.update(thresholds)
        logger.info(f"Alert thresholds updated: {thresholds}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report"""
        try:
            # Calculate time ranges
            now = datetime.now()
            last_hour = now - timedelta(hours=1)
            last_day = now - timedelta(days=1)
            
            # System performance over last hour
            recent_metrics = [m for m in self.system_metrics_history if m.timestamp > last_hour]
            
            if recent_metrics:
                avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
                avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
                avg_disk = sum(m.disk_percent for m in recent_metrics) / len(recent_metrics)
            else:
                avg_cpu = avg_memory = avg_disk = 0.0
            
            # Agent performance summary
            agent_performance = {}
            for agent_name, metrics in self.agent_metrics.items():
                agent_performance[agent_name] = {
                    "availability": 1.0 if metrics.status == HealthStatus.HEALTHY else 0.5,
                    "performance_score": metrics.success_rate * (1.0 - min(metrics.response_time_avg / 30.0, 1.0)),
                    "reliability": 1.0 - metrics.error_rate
                }
            
            # Alert statistics
            recent_alerts = [a for a in self.active_alerts + self.resolved_alerts if a.timestamp > last_day]
            alert_stats = {
                "total_alerts_24h": len(recent_alerts),
                "critical_alerts_24h": len([a for a in recent_alerts if a.severity == AlertSeverity.CRITICAL]),
                "avg_resolution_time": 0.0  # Would calculate from resolved alerts
            }
            
            return {
                "report_timestamp": now.isoformat(),
                "system_performance": {
                    "avg_cpu_1h": avg_cpu,
                    "avg_memory_1h": avg_memory,
                    "avg_disk_1h": avg_disk,
                    "uptime_percentage": 99.9  # Would calculate from actual uptime
                },
                "agent_performance": agent_performance,
                "alert_statistics": alert_stats,
                "overall_health_score": self._calculate_health_score(),
                "recommendations": self._generate_recommendations()
            }
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def _calculate_health_score(self) -> float:
        """Calculate overall system health score (0-100)"""
        try:
            score = 100.0
            
            # Deduct points for active alerts
            for alert in self.active_alerts:
                if not alert.resolved:
                    if alert.severity == AlertSeverity.CRITICAL:
                        score -= 20.0
                    elif alert.severity == AlertSeverity.ERROR:
                        score -= 10.0
                    elif alert.severity == AlertSeverity.WARNING:
                        score -= 5.0
            
            # Deduct points for poor agent performance
            for metrics in self.agent_metrics.values():
                if metrics.error_rate > 0.1:
                    score -= 10.0 * metrics.error_rate
                if metrics.response_time_avg > 20.0:
                    score -= 5.0
            
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 0.0
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        try:
            # System resource recommendations
            if self.system_metrics_history:
                latest = self.system_metrics_history[-1]
                
                if latest.cpu_percent > 80:
                    recommendations.append("Consider scaling up CPU resources or optimizing agent workloads")
                
                if latest.memory_percent > 85:
                    recommendations.append("Memory usage is high - consider increasing available memory")
                
                if latest.disk_percent > 90:
                    recommendations.append("Disk space is critically low - clean up old data or expand storage")
            
            # Agent performance recommendations
            for agent_name, metrics in self.agent_metrics.items():
                if metrics.error_rate > 0.15:
                    recommendations.append(f"Agent {agent_name} has high error rate - investigate and fix issues")
                
                if metrics.response_time_avg > 25.0:
                    recommendations.append(f"Agent {agent_name} response time is slow - optimize performance")
            
            # Alert-based recommendations
            critical_alerts = [a for a in self.active_alerts if a.severity == AlertSeverity.CRITICAL and not a.resolved]
            if len(critical_alerts) > 3:
                recommendations.append("Multiple critical alerts active - immediate attention required")
            
            if not recommendations:
                recommendations.append("System is performing well - no immediate action required")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append("Unable to generate recommendations due to monitoring error")
        
        return recommendations


# Global health monitor instance
health_monitor: Optional[SystemHealthMonitor] = None


def get_health_monitor(monitoring_interval: int = 30) -> SystemHealthMonitor:
    """Get or create the global health monitor"""
    global health_monitor
    
    if health_monitor is None:
        health_monitor = SystemHealthMonitor(monitoring_interval)
    
    return health_monitor