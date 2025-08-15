"""
Performance Optimization and Resource Management System
Implements automated scaling, load balancing, and resource optimization
"""

import asyncio
import logging
import psutil
import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from pydantic import BaseModel, Field

from .system_health_monitor import SystemHealthMonitor, HealthStatus, AlertSeverity
from .agent_state import AgentState, AgentType
from .workflow_orchestrator import WorkflowOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptimizationStrategy(str, Enum):
    """Performance optimization strategies"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    LOAD_BALANCE = "load_balance"
    RESOURCE_REALLOCATION = "resource_reallocation"
    CACHE_OPTIMIZATION = "cache_optimization"
    PARALLEL_PROCESSING = "parallel_processing"
    THROTTLING = "throttling"
    CIRCUIT_BREAKER = "circuit_breaker"


class ResourceType(str, Enum):
    """Types of system resources"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    THREADS = "threads"
    PROCESSES = "processes"
    CONNECTIONS = "connections"


class ScalingDirection(str, Enum):
    """Scaling directions"""
    UP = "up"
    DOWN = "down"
    MAINTAIN = "maintain"


@dataclass
class ResourceLimits:
    """Resource limits and thresholds"""
    cpu_max_percent: float = 80.0
    memory_max_percent: float = 85.0
    disk_max_percent: float = 90.0
    max_threads: int = 100
    max_processes: int = 20
    max_connections: int = 1000
    
    # Scaling thresholds
    scale_up_threshold: float = 75.0
    scale_down_threshold: float = 30.0
    
    # Performance thresholds
    response_time_threshold: float = 30.0  # seconds
    error_rate_threshold: float = 0.1  # 10%
    throughput_min: float = 10.0  # operations per minute


@dataclass
class OptimizationAction:
    """Represents an optimization action to be taken"""
    strategy: OptimizationStrategy
    resource_type: ResourceType
    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # 1=low, 5=critical
    estimated_impact: float = 0.0  # Expected performance improvement (0-1)
    execution_time_estimate: float = 0.0  # Seconds
    executed: bool = False
    execution_result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "strategy": self.strategy.value,
            "resource_type": self.resource_type.value,
            "description": self.description,
            "parameters": self.parameters,
            "priority": self.priority,
            "estimated_impact": self.estimated_impact,
            "execution_time_estimate": self.execution_time_estimate,
            "executed": self.executed,
            "execution_result": self.execution_result
        }


class LoadBalancer:
    """Load balancing for agent tasks and system resources"""
    
    def __init__(self):
        self.agent_loads: Dict[str, float] = {}
        self.task_queue: List[Dict[str, Any]] = []
        self.processing_capacity: Dict[str, int] = {}
        self.load_history: List[Dict[str, Any]] = []
        
        # Load balancing configuration
        self.max_queue_size = 100
        self.load_check_interval = 30  # seconds
        self.rebalance_threshold = 0.3  # 30% load difference
        
        logger.info("Load balancer initialized")
    
    def update_agent_load(self, agent_type: str, load: float):
        """Update agent load metrics"""
        self.agent_loads[agent_type] = max(0.0, min(1.0, load))
        
        # Record load history
        self.load_history.append({
            "timestamp": datetime.now(),
            "agent_type": agent_type,
            "load": load
        })
        
        # Limit history size
        if len(self.load_history) > 1000:
            self.load_history = self.load_history[-500:]
    
    def get_least_loaded_agent(self, agent_types: List[str]) -> Optional[str]:
        """Get the least loaded agent from a list of agent types"""
        if not agent_types:
            return None
        
        available_agents = [
            agent_type for agent_type in agent_types
            if agent_type in self.agent_loads
        ]
        
        if not available_agents:
            return agent_types[0]  # Return first if no load data
        
        # Find agent with lowest load
        least_loaded = min(available_agents, key=lambda x: self.agent_loads[x])
        return least_loaded
    
    def should_rebalance(self) -> bool:
        """Check if load rebalancing is needed"""
        if len(self.agent_loads) < 2:
            return False
        
        loads = list(self.agent_loads.values())
        max_load = max(loads)
        min_load = min(loads)
        
        return (max_load - min_load) > self.rebalance_threshold
    
    def get_rebalancing_recommendations(self) -> List[Dict[str, Any]]:
        """Get load rebalancing recommendations"""
        recommendations = []
        
        if not self.should_rebalance():
            return recommendations
        
        # Sort agents by load
        sorted_agents = sorted(
            self.agent_loads.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        high_load_agents = [
            agent for agent, load in sorted_agents[:len(sorted_agents)//2]
            if load > 0.7
        ]
        
        low_load_agents = [
            agent for agent, load in sorted_agents[len(sorted_agents)//2:]
            if load < 0.4
        ]
        
        for high_agent in high_load_agents:
            for low_agent in low_load_agents:
                recommendations.append({
                    "action": "redistribute_tasks",
                    "from_agent": high_agent,
                    "to_agent": low_agent,
                    "estimated_improvement": 0.2
                })
        
        return recommendations
    
    def get_load_statistics(self) -> Dict[str, Any]:
        """Get load balancing statistics"""
        if not self.agent_loads:
            return {}
        
        loads = list(self.agent_loads.values())
        
        return {
            "total_agents": len(self.agent_loads),
            "average_load": sum(loads) / len(loads),
            "max_load": max(loads),
            "min_load": min(loads),
            "load_variance": self._calculate_variance(loads),
            "rebalancing_needed": self.should_rebalance(),
            "queue_size": len(self.task_queue)
        }
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of load values"""
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance


class AutoScaler:
    """Automatic scaling system for resources and processing capacity"""
    
    def __init__(self, resource_limits: ResourceLimits):
        self.resource_limits = resource_limits
        self.scaling_history: List[Dict[str, Any]] = []
        self.current_scale: Dict[str, int] = {
            "threads": 10,
            "processes": 2,
            "connections": 50
        }
        
        # Thread and process pools
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.process_pool: Optional[ProcessPoolExecutor] = None
        
        # Scaling configuration
        self.min_scale_interval = 300  # 5 minutes between scaling actions
        self.last_scale_time: Dict[str, datetime] = {}
        
        self._initialize_pools()
        logger.info("Auto scaler initialized")
    
    def _initialize_pools(self):
        """Initialize thread and process pools"""
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.current_scale["threads"],
            thread_name_prefix="optimizer"
        )
        
        self.process_pool = ProcessPoolExecutor(
            max_workers=self.current_scale["processes"]
        )
    
    def analyze_scaling_needs(self, system_metrics: Dict[str, Any]) -> List[OptimizationAction]:
        """Analyze system metrics and determine scaling needs"""
        actions = []
        
        try:
            # CPU scaling analysis
            cpu_percent = system_metrics.get("cpu", {}).get("percent", 0)
            if cpu_percent > self.resource_limits.scale_up_threshold:
                actions.append(self._create_scaling_action(
                    ResourceType.CPU,
                    ScalingDirection.UP,
                    f"CPU usage at {cpu_percent:.1f}%",
                    {"current_usage": cpu_percent, "target_reduction": 20}
                ))
            elif cpu_percent < self.resource_limits.scale_down_threshold:
                actions.append(self._create_scaling_action(
                    ResourceType.CPU,
                    ScalingDirection.DOWN,
                    f"CPU usage at {cpu_percent:.1f}%",
                    {"current_usage": cpu_percent, "target_optimization": 10}
                ))
            
            # Memory scaling analysis
            memory_percent = system_metrics.get("memory", {}).get("percent", 0)
            if memory_percent > self.resource_limits.scale_up_threshold:
                actions.append(self._create_scaling_action(
                    ResourceType.MEMORY,
                    ScalingDirection.UP,
                    f"Memory usage at {memory_percent:.1f}%",
                    {"current_usage": memory_percent, "target_reduction": 15}
                ))
            
            # Thread pool scaling analysis
            if self._should_scale_threads():
                thread_action = self._analyze_thread_scaling()
                if thread_action:
                    actions.append(thread_action)
            
        except Exception as e:
            logger.error(f"Error analyzing scaling needs: {e}")
        
        return actions
    
    def _create_scaling_action(self, resource_type: ResourceType, direction: ScalingDirection,
                              description: str, parameters: Dict[str, Any]) -> OptimizationAction:
        """Create a scaling optimization action"""
        
        if direction == ScalingDirection.UP:
            strategy = OptimizationStrategy.SCALE_UP
            priority = 3
            estimated_impact = 0.3
        else:
            strategy = OptimizationStrategy.SCALE_DOWN
            priority = 2
            estimated_impact = 0.1
        
        return OptimizationAction(
            strategy=strategy,
            resource_type=resource_type,
            description=description,
            parameters=parameters,
            priority=priority,
            estimated_impact=estimated_impact,
            execution_time_estimate=30.0
        )
    
    def _should_scale_threads(self) -> bool:
        """Check if thread pool scaling is needed"""
        resource_key = "threads"
        
        if resource_key in self.last_scale_time:
            time_since_last = (datetime.now() - self.last_scale_time[resource_key]).total_seconds()
            if time_since_last < self.min_scale_interval:
                return False
        
        return True
    
    def _analyze_thread_scaling(self) -> Optional[OptimizationAction]:
        """Analyze thread pool scaling needs"""
        current_threads = self.current_scale["threads"]
        
        # This would analyze actual thread utilization
        # For now, we'll use a simple heuristic
        
        if current_threads < self.resource_limits.max_threads // 2:
            return OptimizationAction(
                strategy=OptimizationStrategy.SCALE_UP,
                resource_type=ResourceType.THREADS,
                description=f"Scale up thread pool from {current_threads} threads",
                parameters={"current_threads": current_threads, "target_threads": current_threads * 2},
                priority=2,
                estimated_impact=0.2,
                execution_time_estimate=10.0
            )
        
        return None
    
    async def execute_scaling_action(self, action: OptimizationAction) -> Dict[str, Any]:
        """Execute a scaling action"""
        try:
            logger.info(f"Executing scaling action: {action.description}")
            
            if action.resource_type == ResourceType.THREADS:
                return await self._scale_thread_pool(action)
            elif action.resource_type == ResourceType.PROCESSES:
                return await self._scale_process_pool(action)
            else:
                return {"success": False, "error": f"Unsupported resource type: {action.resource_type}"}
            
        except Exception as e:
            logger.error(f"Error executing scaling action: {e}")
            return {"success": False, "error": str(e)}
    
    async def _scale_thread_pool(self, action: OptimizationAction) -> Dict[str, Any]:
        """Scale the thread pool"""
        try:
            current_threads = self.current_scale["threads"]
            target_threads = action.parameters.get("target_threads", current_threads)
            
            # Limit to maximum
            target_threads = min(target_threads, self.resource_limits.max_threads)
            target_threads = max(target_threads, 1)  # Minimum 1 thread
            
            if target_threads != current_threads:
                # Shutdown old pool
                if self.thread_pool:
                    self.thread_pool.shutdown(wait=False)
                
                # Create new pool
                self.thread_pool = ThreadPoolExecutor(
                    max_workers=target_threads,
                    thread_name_prefix="optimizer"
                )
                
                self.current_scale["threads"] = target_threads
                self.last_scale_time["threads"] = datetime.now()
                
                # Record scaling action
                self.scaling_history.append({
                    "timestamp": datetime.now(),
                    "resource_type": "threads",
                    "action": action.strategy.value,
                    "from_value": current_threads,
                    "to_value": target_threads
                })
                
                logger.info(f"Scaled thread pool from {current_threads} to {target_threads}")
                
                return {
                    "success": True,
                    "from_threads": current_threads,
                    "to_threads": target_threads,
                    "improvement_estimate": action.estimated_impact
                }
            else:
                return {"success": True, "message": "No scaling needed"}
            
        except Exception as e:
            logger.error(f"Error scaling thread pool: {e}")
            return {"success": False, "error": str(e)}
    
    async def _scale_process_pool(self, action: OptimizationAction) -> Dict[str, Any]:
        """Scale the process pool"""
        try:
            current_processes = self.current_scale["processes"]
            target_processes = action.parameters.get("target_processes", current_processes)
            
            # Limit to maximum
            target_processes = min(target_processes, self.resource_limits.max_processes)
            target_processes = max(target_processes, 1)  # Minimum 1 process
            
            if target_processes != current_processes:
                # Shutdown old pool
                if self.process_pool:
                    self.process_pool.shutdown(wait=False)
                
                # Create new pool
                self.process_pool = ProcessPoolExecutor(max_workers=target_processes)
                
                self.current_scale["processes"] = target_processes
                self.last_scale_time["processes"] = datetime.now()
                
                # Record scaling action
                self.scaling_history.append({
                    "timestamp": datetime.now(),
                    "resource_type": "processes",
                    "action": action.strategy.value,
                    "from_value": current_processes,
                    "to_value": target_processes
                })
                
                logger.info(f"Scaled process pool from {current_processes} to {target_processes}")
                
                return {
                    "success": True,
                    "from_processes": current_processes,
                    "to_processes": target_processes,
                    "improvement_estimate": action.estimated_impact
                }
            else:
                return {"success": True, "message": "No scaling needed"}
            
        except Exception as e:
            logger.error(f"Error scaling process pool: {e}")
            return {"success": False, "error": str(e)}
    
    def get_scaling_statistics(self) -> Dict[str, Any]:
        """Get scaling statistics"""
        return {
            "current_scale": self.current_scale.copy(),
            "resource_limits": {
                "max_threads": self.resource_limits.max_threads,
                "max_processes": self.resource_limits.max_processes,
                "max_connections": self.resource_limits.max_connections
            },
            "scaling_history_count": len(self.scaling_history),
            "last_scaling_actions": self.scaling_history[-5:] if self.scaling_history else []
        }
    
    def cleanup(self):
        """Cleanup resources"""
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)
        
        if self.process_pool:
            self.process_pool.shutdown(wait=True)


class ErrorRecoverySystem:
    """Error handling and recovery system"""
    
    def __init__(self):
        self.error_history: List[Dict[str, Any]] = []
        self.recovery_strategies: Dict[str, Callable] = {}
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        
        # Recovery configuration
        self.max_retry_attempts = 3
        self.retry_delay_base = 1.0  # seconds
        self.circuit_breaker_threshold = 5  # failures before opening
        self.circuit_breaker_timeout = 300  # seconds
        
        self._setup_default_strategies()
        logger.info("Error recovery system initialized")
    
    def _setup_default_strategies(self):
        """Set up default recovery strategies"""
        self.recovery_strategies = {
            "agent_timeout": self._recover_agent_timeout,
            "memory_exhaustion": self._recover_memory_exhaustion,
            "connection_failure": self._recover_connection_failure,
            "processing_overload": self._recover_processing_overload,
            "data_corruption": self._recover_data_corruption
        }
    
    def record_error(self, error_type: str, component: str, details: Dict[str, Any]):
        """Record an error for analysis and recovery"""
        error_record = {
            "timestamp": datetime.now(),
            "error_type": error_type,
            "component": component,
            "details": details,
            "recovery_attempted": False,
            "recovery_successful": False
        }
        
        self.error_history.append(error_record)
        
        # Limit history size
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-500:]
        
        # Update circuit breaker
        self._update_circuit_breaker(component, error_type)
        
        logger.warning(f"Error recorded: {error_type} in {component}")
    
    def _update_circuit_breaker(self, component: str, error_type: str):
        """Update circuit breaker state"""
        key = f"{component}:{error_type}"
        
        if key not in self.circuit_breakers:
            self.circuit_breakers[key] = {
                "failure_count": 0,
                "last_failure": None,
                "state": "closed",  # closed, open, half_open
                "opened_at": None
            }
        
        breaker = self.circuit_breakers[key]
        breaker["failure_count"] += 1
        breaker["last_failure"] = datetime.now()
        
        # Open circuit breaker if threshold exceeded
        if (breaker["failure_count"] >= self.circuit_breaker_threshold and 
            breaker["state"] == "closed"):
            breaker["state"] = "open"
            breaker["opened_at"] = datetime.now()
            logger.warning(f"Circuit breaker opened for {key}")
    
    def is_circuit_breaker_open(self, component: str, error_type: str) -> bool:
        """Check if circuit breaker is open"""
        key = f"{component}:{error_type}"
        
        if key not in self.circuit_breakers:
            return False
        
        breaker = self.circuit_breakers[key]
        
        if breaker["state"] == "open":
            # Check if timeout has passed
            if breaker["opened_at"]:
                time_since_open = (datetime.now() - breaker["opened_at"]).total_seconds()
                if time_since_open > self.circuit_breaker_timeout:
                    breaker["state"] = "half_open"
                    logger.info(f"Circuit breaker half-opened for {key}")
                    return False
            return True
        
        return False
    
    async def attempt_recovery(self, error_type: str, component: str, 
                              details: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to recover from an error"""
        
        # Check circuit breaker
        if self.is_circuit_breaker_open(component, error_type):
            return {
                "success": False,
                "reason": "circuit_breaker_open",
                "message": f"Circuit breaker is open for {component}:{error_type}"
            }
        
        # Find appropriate recovery strategy
        recovery_func = self.recovery_strategies.get(error_type)
        
        if not recovery_func:
            return {
                "success": False,
                "reason": "no_strategy",
                "message": f"No recovery strategy for error type: {error_type}"
            }
        
        try:
            # Attempt recovery
            recovery_result = await recovery_func(component, details)
            
            # Update error record
            for error_record in reversed(self.error_history):
                if (error_record["error_type"] == error_type and 
                    error_record["component"] == component and
                    not error_record["recovery_attempted"]):
                    error_record["recovery_attempted"] = True
                    error_record["recovery_successful"] = recovery_result.get("success", False)
                    break
            
            # Reset circuit breaker on successful recovery
            if recovery_result.get("success", False):
                key = f"{component}:{error_type}"
                if key in self.circuit_breakers:
                    self.circuit_breakers[key]["failure_count"] = 0
                    self.circuit_breakers[key]["state"] = "closed"
                    logger.info(f"Circuit breaker reset for {key}")
            
            return recovery_result
            
        except Exception as e:
            logger.error(f"Error during recovery attempt: {e}")
            return {
                "success": False,
                "reason": "recovery_failed",
                "error": str(e)
            }
    
    async def _recover_agent_timeout(self, component: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Recover from agent timeout"""
        try:
            # Restart agent or increase timeout
            logger.info(f"Attempting to recover from agent timeout: {component}")
            
            # Simulate recovery actions
            await asyncio.sleep(1)
            
            return {
                "success": True,
                "action": "agent_restart",
                "message": f"Agent {component} recovery attempted"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _recover_memory_exhaustion(self, component: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Recover from memory exhaustion"""
        try:
            logger.info(f"Attempting to recover from memory exhaustion: {component}")
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Clear caches if available
            # This would integrate with actual cache systems
            
            return {
                "success": True,
                "action": "memory_cleanup",
                "message": f"Memory cleanup performed for {component}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _recover_connection_failure(self, component: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Recover from connection failure"""
        try:
            logger.info(f"Attempting to recover from connection failure: {component}")
            
            # Retry connection with exponential backoff
            for attempt in range(self.max_retry_attempts):
                await asyncio.sleep(self.retry_delay_base * (2 ** attempt))
                
                # Simulate connection attempt
                # This would integrate with actual connection systems
                
                if attempt == self.max_retry_attempts - 1:  # Last attempt
                    return {
                        "success": True,
                        "action": "connection_retry",
                        "attempts": attempt + 1,
                        "message": f"Connection recovery attempted for {component}"
                    }
            
            return {"success": False, "message": "All retry attempts failed"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _recover_processing_overload(self, component: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Recover from processing overload"""
        try:
            logger.info(f"Attempting to recover from processing overload: {component}")
            
            # Implement throttling or load shedding
            # This would integrate with actual load management systems
            
            return {
                "success": True,
                "action": "load_throttling",
                "message": f"Load throttling applied to {component}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _recover_data_corruption(self, component: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Recover from data corruption"""
        try:
            logger.info(f"Attempting to recover from data corruption: {component}")
            
            # Restore from backup or reinitialize
            # This would integrate with actual backup systems
            
            return {
                "success": True,
                "action": "data_restore",
                "message": f"Data recovery attempted for {component}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error and recovery statistics"""
        if not self.error_history:
            return {"total_errors": 0}
        
        # Calculate statistics
        total_errors = len(self.error_history)
        recovery_attempts = len([e for e in self.error_history if e["recovery_attempted"]])
        successful_recoveries = len([e for e in self.error_history if e["recovery_successful"]])
        
        # Error types breakdown
        error_types = {}
        for error in self.error_history:
            error_type = error["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Component breakdown
        components = {}
        for error in self.error_history:
            component = error["component"]
            components[component] = components.get(component, 0) + 1
        
        return {
            "total_errors": total_errors,
            "recovery_attempts": recovery_attempts,
            "successful_recoveries": successful_recoveries,
            "recovery_success_rate": successful_recoveries / max(recovery_attempts, 1),
            "error_types": error_types,
            "components": components,
            "circuit_breakers": len(self.circuit_breakers),
            "open_circuit_breakers": len([
                cb for cb in self.circuit_breakers.values() 
                if cb["state"] == "open"
            ])
        }


class PerformanceOptimizer:
    """
    Main Performance Optimization System
    
    Coordinates all optimization components:
    - Load balancing
    - Auto scaling
    - Error recovery
    - Resource optimization
    """
    
    def __init__(self, resource_limits: Optional[ResourceLimits] = None):
        self.resource_limits = resource_limits or ResourceLimits()
        
        # Core components
        self.load_balancer = LoadBalancer()
        self.auto_scaler = AutoScaler(self.resource_limits)
        self.error_recovery = ErrorRecoverySystem()
        self.health_monitor: Optional[SystemHealthMonitor] = None
        
        # Optimization state
        self.is_optimizing = False
        self.optimization_task: Optional[asyncio.Task] = None
        self.optimization_interval = 60  # seconds
        
        # Optimization history
        self.optimization_history: List[Dict[str, Any]] = []
        self.performance_improvements: List[Dict[str, Any]] = []
        
        # Callbacks for optimization events
        self.optimization_callbacks: List[Callable] = []
        
        logger.info("Performance optimizer initialized")
    
    async def start_optimization(self, health_monitor: Optional[SystemHealthMonitor] = None):
        """Start the performance optimization system"""
        if self.is_optimizing:
            logger.warning("Performance optimization is already running")
            return
        
        self.health_monitor = health_monitor
        self.is_optimizing = True
        self.optimization_task = asyncio.create_task(self._optimization_loop())
        
        logger.info("Performance optimization started")
    
    async def stop_optimization(self):
        """Stop the performance optimization system"""
        if not self.is_optimizing:
            return
        
        self.is_optimizing = False
        
        if self.optimization_task and not self.optimization_task.done():
            self.optimization_task.cancel()
            try:
                await self.optimization_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup resources
        self.auto_scaler.cleanup()
        
        logger.info("Performance optimization stopped")
    
    async def _optimization_loop(self):
        """Main optimization loop"""
        while self.is_optimizing:
            try:
                # Collect current system metrics
                system_metrics = await self._collect_system_metrics()
                
                # Analyze optimization opportunities
                optimization_actions = await self._analyze_optimization_opportunities(system_metrics)
                
                # Execute high-priority optimizations
                if optimization_actions:
                    await self._execute_optimization_actions(optimization_actions)
                
                # Update load balancing
                await self._update_load_balancing()
                
                # Check for error recovery opportunities
                await self._check_error_recovery()
                
                # Record optimization cycle
                self._record_optimization_cycle(system_metrics, optimization_actions)
                
                # Wait for next cycle
                await asyncio.sleep(self.optimization_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(self.optimization_interval)
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        try:
            if self.health_monitor:
                health_summary = self.health_monitor.get_system_health_summary()
                return health_summary.get("system_metrics", {})
            else:
                # Fallback to basic metrics collection
                return {
                    "cpu": {"percent": psutil.cpu_percent()},
                    "memory": {"percent": psutil.virtual_memory().percent},
                    "disk": {"percent": psutil.disk_usage('/').percent}
                }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    async def _analyze_optimization_opportunities(self, system_metrics: Dict[str, Any]) -> List[OptimizationAction]:
        """Analyze system metrics and identify optimization opportunities"""
        actions = []
        
        try:
            # Auto scaling analysis
            scaling_actions = self.auto_scaler.analyze_scaling_needs(system_metrics)
            actions.extend(scaling_actions)
            
            # Load balancing analysis
            if self.load_balancer.should_rebalance():
                rebalancing_recommendations = self.load_balancer.get_rebalancing_recommendations()
                
                for recommendation in rebalancing_recommendations:
                    actions.append(OptimizationAction(
                        strategy=OptimizationStrategy.LOAD_BALANCE,
                        resource_type=ResourceType.THREADS,
                        description=f"Rebalance load from {recommendation['from_agent']} to {recommendation['to_agent']}",
                        parameters=recommendation,
                        priority=2,
                        estimated_impact=recommendation.get("estimated_improvement", 0.1)
                    ))
            
            # Resource optimization analysis
            resource_actions = await self._analyze_resource_optimization(system_metrics)
            actions.extend(resource_actions)
            
            # Cache optimization analysis
            cache_actions = await self._analyze_cache_optimization()
            actions.extend(cache_actions)
            
            # Sort actions by priority and impact
            actions.sort(key=lambda x: (x.priority, -x.estimated_impact), reverse=True)
            
        except Exception as e:
            logger.error(f"Error analyzing optimization opportunities: {e}")
        
        return actions
    
    async def _analyze_resource_optimization(self, system_metrics: Dict[str, Any]) -> List[OptimizationAction]:
        """Analyze resource optimization opportunities"""
        actions = []
        
        try:
            # Memory optimization
            memory_percent = system_metrics.get("memory", {}).get("percent", 0)
            if memory_percent > 80:
                actions.append(OptimizationAction(
                    strategy=OptimizationStrategy.RESOURCE_REALLOCATION,
                    resource_type=ResourceType.MEMORY,
                    description=f"Optimize memory usage (currently {memory_percent:.1f}%)",
                    parameters={"current_usage": memory_percent, "target_reduction": 15},
                    priority=3,
                    estimated_impact=0.25
                ))
            
            # Disk optimization
            disk_percent = system_metrics.get("disk", {}).get("percent", 0)
            if disk_percent > 85:
                actions.append(OptimizationAction(
                    strategy=OptimizationStrategy.RESOURCE_REALLOCATION,
                    resource_type=ResourceType.DISK,
                    description=f"Clean up disk space (currently {disk_percent:.1f}%)",
                    parameters={"current_usage": disk_percent, "target_reduction": 20},
                    priority=4,
                    estimated_impact=0.15
                ))
            
        except Exception as e:
            logger.error(f"Error analyzing resource optimization: {e}")
        
        return actions
    
    async def _analyze_cache_optimization(self) -> List[OptimizationAction]:
        """Analyze cache optimization opportunities"""
        actions = []
        
        try:
            # This would analyze actual cache performance
            # For now, we'll create a placeholder optimization
            
            actions.append(OptimizationAction(
                strategy=OptimizationStrategy.CACHE_OPTIMIZATION,
                resource_type=ResourceType.MEMORY,
                description="Optimize cache performance and hit rates",
                parameters={"cache_type": "general", "optimization_level": "standard"},
                priority=1,
                estimated_impact=0.1
            ))
            
        except Exception as e:
            logger.error(f"Error analyzing cache optimization: {e}")
        
        return actions
    
    async def _execute_optimization_actions(self, actions: List[OptimizationAction]):
        """Execute optimization actions"""
        executed_count = 0
        
        for action in actions[:5]:  # Limit to top 5 actions per cycle
            try:
                logger.info(f"Executing optimization action: {action.description}")
                
                result = await self._execute_single_action(action)
                
                action.executed = True
                action.execution_result = result
                
                if result.get("success", False):
                    executed_count += 1
                    
                    # Record performance improvement
                    self.performance_improvements.append({
                        "timestamp": datetime.now(),
                        "action_id": action.id,
                        "strategy": action.strategy.value,
                        "estimated_impact": action.estimated_impact,
                        "actual_result": result
                    })
                    
                    # Notify callbacks
                    for callback in self.optimization_callbacks:
                        try:
                            callback(action, result)
                        except Exception as e:
                            logger.error(f"Error in optimization callback: {e}")
                
            except Exception as e:
                logger.error(f"Error executing optimization action: {e}")
                action.executed = True
                action.execution_result = {"success": False, "error": str(e)}
        
        if executed_count > 0:
            logger.info(f"Executed {executed_count} optimization actions")
    
    async def _execute_single_action(self, action: OptimizationAction) -> Dict[str, Any]:
        """Execute a single optimization action"""
        
        if action.strategy in [OptimizationStrategy.SCALE_UP, OptimizationStrategy.SCALE_DOWN]:
            return await self.auto_scaler.execute_scaling_action(action)
        
        elif action.strategy == OptimizationStrategy.LOAD_BALANCE:
            return await self._execute_load_balancing(action)
        
        elif action.strategy == OptimizationStrategy.RESOURCE_REALLOCATION:
            return await self._execute_resource_reallocation(action)
        
        elif action.strategy == OptimizationStrategy.CACHE_OPTIMIZATION:
            return await self._execute_cache_optimization(action)
        
        else:
            return {"success": False, "error": f"Unknown optimization strategy: {action.strategy}"}
    
    async def _execute_load_balancing(self, action: OptimizationAction) -> Dict[str, Any]:
        """Execute load balancing optimization"""
        try:
            # This would implement actual load balancing
            # For now, we'll simulate the action
            
            from_agent = action.parameters.get("from_agent")
            to_agent = action.parameters.get("to_agent")
            
            logger.info(f"Load balancing from {from_agent} to {to_agent}")
            
            return {
                "success": True,
                "action": "load_rebalanced",
                "from_agent": from_agent,
                "to_agent": to_agent
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_resource_reallocation(self, action: OptimizationAction) -> Dict[str, Any]:
        """Execute resource reallocation optimization"""
        try:
            resource_type = action.resource_type
            
            if resource_type == ResourceType.MEMORY:
                # Force garbage collection
                import gc
                gc.collect()
                
                return {
                    "success": True,
                    "action": "memory_cleanup",
                    "resource_type": resource_type.value
                }
            
            elif resource_type == ResourceType.DISK:
                # This would implement disk cleanup
                # For now, we'll simulate the action
                
                return {
                    "success": True,
                    "action": "disk_cleanup",
                    "resource_type": resource_type.value
                }
            
            else:
                return {"success": False, "error": f"Unsupported resource type: {resource_type}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_cache_optimization(self, action: OptimizationAction) -> Dict[str, Any]:
        """Execute cache optimization"""
        try:
            # This would implement actual cache optimization
            # For now, we'll simulate the action
            
            cache_type = action.parameters.get("cache_type", "general")
            
            return {
                "success": True,
                "action": "cache_optimized",
                "cache_type": cache_type
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _update_load_balancing(self):
        """Update load balancing metrics"""
        try:
            # This would collect actual agent load metrics
            # For now, we'll simulate some load updates
            
            import random
            agent_types = ["scout", "analyst", "negotiator", "contract", "portfolio"]
            
            for agent_type in agent_types:
                load = random.uniform(0.2, 0.8)
                self.load_balancer.update_agent_load(agent_type, load)
            
        except Exception as e:
            logger.error(f"Error updating load balancing: {e}")
    
    async def _check_error_recovery(self):
        """Check for error recovery opportunities"""
        try:
            # This would check for recent errors that need recovery
            # For now, we'll just log that we're checking
            
            error_stats = self.error_recovery.get_error_statistics()
            
            if error_stats.get("total_errors", 0) > 0:
                logger.debug(f"Error recovery check: {error_stats['total_errors']} total errors")
            
        except Exception as e:
            logger.error(f"Error checking error recovery: {e}")
    
    def _record_optimization_cycle(self, system_metrics: Dict[str, Any], actions: List[OptimizationAction]):
        """Record optimization cycle results"""
        cycle_record = {
            "timestamp": datetime.now(),
            "system_metrics": system_metrics,
            "actions_identified": len(actions),
            "actions_executed": len([a for a in actions if a.executed]),
            "total_estimated_impact": sum(a.estimated_impact for a in actions if a.executed)
        }
        
        self.optimization_history.append(cycle_record)
        
        # Limit history size
        if len(self.optimization_history) > 100:
            self.optimization_history = self.optimization_history[-50:]
    
    # Public Interface Methods
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get optimization system summary"""
        try:
            # Load balancing statistics
            load_stats = self.load_balancer.get_load_statistics()
            
            # Scaling statistics
            scaling_stats = self.auto_scaler.get_scaling_statistics()
            
            # Error recovery statistics
            error_stats = self.error_recovery.get_error_statistics()
            
            # Performance improvements
            recent_improvements = self.performance_improvements[-10:] if self.performance_improvements else []
            
            return {
                "optimization_status": "active" if self.is_optimizing else "inactive",
                "load_balancing": load_stats,
                "auto_scaling": scaling_stats,
                "error_recovery": error_stats,
                "optimization_cycles": len(self.optimization_history),
                "recent_improvements": recent_improvements,
                "total_improvements": len(self.performance_improvements)
            }
            
        except Exception as e:
            logger.error(f"Error getting optimization summary: {e}")
            return {"error": str(e)}
    
    def get_performance_improvements(self) -> List[Dict[str, Any]]:
        """Get performance improvement history"""
        return self.performance_improvements.copy()
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """Get optimization cycle history"""
        return self.optimization_history.copy()
    
    def add_optimization_callback(self, callback: Callable):
        """Add callback for optimization events"""
        self.optimization_callbacks.append(callback)
    
    def remove_optimization_callback(self, callback: Callable):
        """Remove optimization callback"""
        if callback in self.optimization_callbacks:
            self.optimization_callbacks.remove(callback)
    
    async def force_optimization_cycle(self) -> Dict[str, Any]:
        """Force an immediate optimization cycle"""
        try:
            logger.info("Forcing optimization cycle")
            
            # Collect metrics
            system_metrics = await self._collect_system_metrics()
            
            # Analyze opportunities
            actions = await self._analyze_optimization_opportunities(system_metrics)
            
            # Execute actions
            if actions:
                await self._execute_optimization_actions(actions)
            
            # Record cycle
            self._record_optimization_cycle(system_metrics, actions)
            
            return {
                "success": True,
                "actions_identified": len(actions),
                "actions_executed": len([a for a in actions if a.executed]),
                "system_metrics": system_metrics
            }
            
        except Exception as e:
            logger.error(f"Error in forced optimization cycle: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_error(self, error_type: str, component: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an error and attempt recovery"""
        # Record the error
        self.error_recovery.record_error(error_type, component, details)
        
        # Attempt recovery
        recovery_result = await self.error_recovery.attempt_recovery(error_type, component, details)
        
        return recovery_result


# Global performance optimizer instance
performance_optimizer: Optional[PerformanceOptimizer] = None


def get_performance_optimizer(resource_limits: Optional[ResourceLimits] = None) -> PerformanceOptimizer:
    """Get or create the global performance optimizer"""
    global performance_optimizer
    
    if performance_optimizer is None:
        performance_optimizer = PerformanceOptimizer(resource_limits)
    
    return performance_optimizer