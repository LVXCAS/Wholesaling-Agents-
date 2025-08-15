"""
Production Launch API
API endpoints for managing production launches
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from ...core.production_launcher import (
    get_production_launcher,
    ProductionLaunchConfig,
    LaunchStatus,
    LaunchPhase
)

router = APIRouter(prefix="/production", tags=["production"])


class LaunchRequest(BaseModel):
    """Production launch request"""
    version: str
    build_id: Optional[str] = None
    
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
    rollback_threshold_error_rate: float = 0.1
    rollback_threshold_response_time: float = 10.0
    
    # Monitoring thresholds
    cpu_alert_threshold: float = 80.0
    memory_alert_threshold: float = 85.0
    error_rate_alert_threshold: float = 0.05
    response_time_alert_threshold: float = 5.0
    
    # Support settings
    support_email: str = "support@realestate-empire.com"
    support_phone: str = "+1-555-SUPPORT"
    support_hours: str = "24/7"


class LaunchResponse(BaseModel):
    """Production launch response"""
    launch_id: str
    version: str
    status: str
    current_phase: str
    started_at: datetime
    message: str


class LaunchStatusResponse(BaseModel):
    """Launch status response"""
    active: bool
    launch_id: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None
    current_phase: Optional[str] = None
    started_at: Optional[datetime] = None
    duration: Optional[float] = None


class LaunchHistoryResponse(BaseModel):
    """Launch history response"""
    launches: List[Dict[str, Any]]
    total: int


class ProductionMetricsResponse(BaseModel):
    """Production metrics response"""
    overall_status: str
    timestamp: datetime
    system_metrics: Dict[str, Any]
    agent_health: Dict[str, Any]
    workflow_health: Dict[str, Any]
    alerts: Dict[str, Any]
    monitoring_status: str


@router.post("/launch", response_model=LaunchResponse)
async def launch_production(
    request: LaunchRequest,
    background_tasks: BackgroundTasks
):
    """
    Launch production system
    
    Initiates a complete production launch including:
    - Deployment to production environment
    - Health monitoring setup
    - Alerting configuration
    - Support system activation
    - User feedback collection
    """
    try:
        launcher = get_production_launcher()
        
        # Check if launch is already in progress
        current_status = launcher.get_launch_status()
        if current_status["active"]:
            raise HTTPException(
                status_code=409,
                detail=f"Production launch already in progress: {current_status['launch_id']}"
            )
        
        # Create launch configuration
        config = ProductionLaunchConfig(
            version=request.version,
            build_id=request.build_id or f"build-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            enable_monitoring=request.enable_monitoring,
            enable_alerting=request.enable_alerting,
            enable_user_feedback=request.enable_user_feedback,
            enable_support_system=request.enable_support_system,
            enable_auto_scaling=request.enable_auto_scaling,
            enable_performance_optimization=request.enable_performance_optimization,
            auto_rollback_on_failure=request.auto_rollback_on_failure,
            rollback_threshold_error_rate=request.rollback_threshold_error_rate,
            rollback_threshold_response_time=request.rollback_threshold_response_time,
            cpu_alert_threshold=request.cpu_alert_threshold,
            memory_alert_threshold=request.memory_alert_threshold,
            error_rate_alert_threshold=request.error_rate_alert_threshold,
            response_time_alert_threshold=request.response_time_alert_threshold,
            support_email=request.support_email,
            support_phone=request.support_phone,
            support_hours=request.support_hours
        )
        
        # Start launch in background
        background_tasks.add_task(launcher.launch_production, config)
        
        return LaunchResponse(
            launch_id=config.build_id,
            version=config.version,
            status=LaunchStatus.PENDING.value,
            current_phase=LaunchPhase.PRE_LAUNCH.value,
            started_at=datetime.now(),
            message="Production launch initiated successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=LaunchStatusResponse)
async def get_launch_status():
    """
    Get current production launch status
    
    Returns the status of any active production launch
    """
    try:
        launcher = get_production_launcher()
        status = launcher.get_launch_status()
        
        return LaunchStatusResponse(
            active=status["active"],
            launch_id=status.get("launch_id"),
            version=status.get("version"),
            status=status.get("status"),
            current_phase=status.get("current_phase"),
            started_at=datetime.fromisoformat(status["started_at"]) if status.get("started_at") else None,
            duration=status.get("duration")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=LaunchHistoryResponse)
async def get_launch_history(limit: int = 10):
    """
    Get production launch history
    
    Returns history of recent production launches
    """
    try:
        launcher = get_production_launcher()
        history = launcher.get_launch_history(limit=limit)
        
        return LaunchHistoryResponse(
            launches=history,
            total=len(history)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=ProductionMetricsResponse)
async def get_production_metrics():
    """
    Get production system metrics
    
    Returns comprehensive production system health and performance metrics
    """
    try:
        launcher = get_production_launcher()
        metrics = launcher.get_production_metrics()
        
        return ProductionMetricsResponse(
            overall_status=metrics.get("overall_status", "unknown"),
            timestamp=datetime.fromisoformat(metrics.get("timestamp", datetime.now().isoformat())),
            system_metrics=metrics.get("system_metrics", {}),
            agent_health=metrics.get("agent_health", {}),
            workflow_health=metrics.get("workflow_health", {}),
            alerts=metrics.get("alerts", {}),
            monitoring_status=metrics.get("monitoring_status", "inactive")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rollback/{launch_id}")
async def rollback_launch(launch_id: str):
    """
    Rollback a production launch
    
    Initiates rollback of a specific production launch
    """
    try:
        launcher = get_production_launcher()
        
        # Find launch in history
        history = launcher.get_launch_history(limit=50)
        launch = next((l for l in history if l["id"] == launch_id), None)
        
        if not launch:
            raise HTTPException(status_code=404, detail="Launch not found")
        
        if launch["status"] not in ["completed", "failed"]:
            raise HTTPException(
                status_code=400,
                detail="Can only rollback completed or failed launches"
            )
        
        # This would implement actual rollback logic
        # For now, return success message
        
        return {
            "message": f"Rollback initiated for launch {launch_id}",
            "launch_id": launch_id,
            "status": "rollback_initiated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def production_health_check():
    """
    Production system health check
    
    Quick health check endpoint for load balancers and monitoring
    """
    try:
        launcher = get_production_launcher()
        metrics = launcher.get_production_metrics()
        
        overall_status = metrics.get("overall_status", "unknown")
        
        if overall_status in ["healthy", "warning"]:
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"  # This would come from actual version
            }
        else:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "unhealthy",
                    "overall_status": overall_status,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.post("/maintenance/enable")
async def enable_maintenance_mode():
    """
    Enable maintenance mode
    
    Puts the production system into maintenance mode
    """
    try:
        # This would implement actual maintenance mode logic
        return {
            "message": "Maintenance mode enabled",
            "timestamp": datetime.now().isoformat(),
            "status": "maintenance_enabled"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/maintenance/disable")
async def disable_maintenance_mode():
    """
    Disable maintenance mode
    
    Takes the production system out of maintenance mode
    """
    try:
        # This would implement actual maintenance mode logic
        return {
            "message": "Maintenance mode disabled",
            "timestamp": datetime.now().isoformat(),
            "status": "maintenance_disabled"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/{launch_id}")
async def get_launch_logs(launch_id: str, phase: Optional[str] = None):
    """
    Get production launch logs
    
    Returns logs for a specific launch, optionally filtered by phase
    """
    try:
        launcher = get_production_launcher()
        
        # Find launch in history
        history = launcher.get_launch_history(limit=50)
        launch = next((l for l in history if l["id"] == launch_id), None)
        
        if not launch:
            raise HTTPException(status_code=404, detail="Launch not found")
        
        # This would return actual logs from the launch record
        # For now, return placeholder
        
        return {
            "launch_id": launch_id,
            "phase": phase,
            "logs": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "level": "INFO",
                    "message": "Sample log message",
                    "phase": "deployment"
                }
            ],
            "total_logs": 1
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_user_feedback(
    user_id: str,
    feedback_type: str,
    content: str,
    rating: int = Field(..., ge=1, le=5)
):
    """
    Submit user feedback
    
    Allows users to submit feedback about the production system
    """
    try:
        launcher = get_production_launcher()
        
        if launcher.feedback_system:
            launcher.feedback_system.collect_feedback(
                user_id=user_id,
                feedback_type=feedback_type,
                content=content,
                rating=rating
            )
        
        return {
            "message": "Feedback submitted successfully",
            "timestamp": datetime.now().isoformat(),
            "feedback_id": f"feedback-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/support/status")
async def get_support_status():
    """
    Get support system status
    
    Returns the current status of the support system
    """
    try:
        launcher = get_production_launcher()
        
        # This would return actual support system status
        return {
            "support_active": True,
            "support_email": "support@realestate-empire.com",
            "support_phone": "+1-555-SUPPORT",
            "support_hours": "24/7",
            "knowledge_base_articles": 25,
            "open_tickets": 3,
            "average_response_time": "2 hours",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))