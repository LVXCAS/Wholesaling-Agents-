"""
System monitoring and alerting service.
Provides comprehensive monitoring, alerting, and health checks.
"""

import os
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
import asyncio
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, field
from enum import Enum
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SystemAlert:
    """System alert data structure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    level: AlertLevel = AlertLevel.INFO
    component: str = ""
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class SystemMetrics:
    """System metrics data structure"""
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    active_connections: int = 0
    response_time_avg: float = 0.0
    error_rate: float = 0.0


class MonitoringService:
    """
    System monitoring and alerting service
    
    Provides comprehensive monitoring of:
    - System resources (CPU, memory, disk, network)
    - Application performance metrics
    - Health checks and alerts
    - Notification delivery
    """
    
    def __init__(self):
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.monitoring_interval = 30  # seconds
        
        # Metrics storage
        self.current_metrics = SystemMetrics()
        self.metrics_history: List[SystemMetrics] = []
        self.active_alerts: List[SystemAlert] = []
        self.resolved_alerts: List[SystemAlert] = []
        
        # Alert thresholds
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "response_time": 5.0,
            "error_rate": 0.05
        }
        
        # Notification settings
        self.notification_settings = {
            "email_enabled": True,
            "email_recipients": ["admin@realestate-empire.com"],
            "smtp_host": os.getenv("SMTP_HOST", "localhost"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "smtp_user": os.getenv("SMTP_USER", ""),
            "smtp_password": os.getenv("SMTP_PASSWORD", "")
        }
        
        # Alert callbacks
        self.alert_callbacks: List[Callable[[SystemAlert], None]] = []
        
        logger.info("Monitoring service initialized")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return {
            "timestamp": self.current_metrics.timestamp.isoformat(),
            "cpu_percent": self.current_metrics.cpu_percent,
            "memory_percent": self.current_metrics.memory_percent,
            "disk_percent": self.current_metrics.disk_percent,
            "network_bytes_sent": self.current_metrics.network_bytes_sent,
            "network_bytes_recv": self.current_metrics.network_bytes_recv,
            "active_connections": self.current_metrics.active_connections,
            "response_time_avg": self.current_metrics.response_time_avg,
            "error_rate": self.current_metrics.error_rate
        }
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        metrics = self.current_metrics
        active_alerts = [a for a in self.active_alerts if not a.resolved]
        
        # Determine overall health status
        critical_alerts = [a for a in active_alerts if a.level == AlertLevel.CRITICAL]
        error_alerts = [a for a in active_alerts if a.level == AlertLevel.ERROR]
        warning_alerts = [a for a in active_alerts if a.level == AlertLevel.WARNING]
        
        if critical_alerts:
            overall_status = "critical"
        elif error_alerts:
            overall_status = "degraded"
        elif warning_alerts:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "system_metrics": self.get_current_metrics(),
            "alerts": {
                "critical": len(critical_alerts),
                "error": len(error_alerts),
                "warning": len(warning_alerts),
                "total_active": len(active_alerts)
            },
            "monitoring_status": "active" if self.is_monitoring else "inactive"
        }


# Global monitoring service instance
_monitoring_service: Optional[MonitoringService] = None

def get_monitoring_service() -> MonitoringService:
    """Get global monitoring service instance"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service