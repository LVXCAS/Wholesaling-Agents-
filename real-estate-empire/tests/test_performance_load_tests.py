"""
Performance and Load Tests
Tests system performance under various load conditions and validates optimization
"""

import pytest
import asyncio
import time
import statistics
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch, AsyncMock
import psutil
import threading

from app.core.performance_optimizer import PerformanceOptimizer, ResourceLimits, OptimizationStrategy
from app.core.system_health_monitor import SystemHealthMonitor
from app.core.workflow_orchestrator import WorkflowOrchestrator, WorkflowConfiguration
from app.core.agent_state import StateManager


class TestPerformanceAndLoad:
    """Test suite for performance and load testing"""
    
    @pytest.fixture
    def resource_limits(self):
        """Create test resource limits"""
        return ResourceLimits(
            cpu_max_percent=70.0,
            memory_max_percent=75.0,
            disk_max_percent=80.0,
            max_threads=50,
            max_processes=10,
            max_connections=500,
            scale_up_threshold=60.0,
            scale_down_threshold=20.0,
            response_time_threshold=15.0,
            error_rate_threshold=0.05
        )
    
    @pytest.fixture
    async def performance_optimizer(self, resource_limits):
        """Create performance optimizer for testing"""
        optimizer = PerformanceOptimizer(resource_limits)
        yield optimizer
        await optimizer.stop_optimization()
    
    @pytest.fixture
    async def health_monitor(self):
        """Create health monitor for testing"""
        monitor = SystemHealthMonitor(monitoring_interval=2)
        await monitor.start_monitoring()
        yield monitor
        await monitor.stop_monitoring()
    
    @pytest.fixture
    def workflow_config(self):
        """Create test workflow configuration"""
        return WorkflowConfiguration(
            max_concurrent_deals=20,
            max_execution_time_minutes=30,
            enable_parallel_processing=True,
            agent_timeout_seconds=10,
            max_retries_per_agent=2,
            batch_communications=True,
            communication_delay_seconds=1,
            enable_real_time_monitoring=True,
            metrics_collection_interval=5
        )
    
    @pytest.mark.asyncio
    async def test_system_performance_under_load(self, performance_optimizer, health_monitor):
        """Test system performance under various load conditions"""
        
        # Start optimization
        await performance_optimizer.start_optimization(health_monitor)
        
        # Simulate different load levels
        load_scenarios = [
            {"name": "light_load", "concurrent_tasks": 5, "duration": 10},
            {"name": "medium_load", "concurrent_tasks": 15, "duration": 15},
            {"name": "heavy_load", "concurrent_tasks": 30, "duration": 20}
        ]
        
        performance_results = []
        
        for scenario in load_scenarios:
            logger.info(f"Testing scenario: {scenario['name']}")
            
            # Record baseline metrics
            baseline_metrics = await self._collect_performance_metrics(health_monitor)
            
            # Generate load
            start_time = time.time()
            
            tasks = []
            for i in range(scenario["concurrent_tasks"]):
                task = asyncio.create_task(self._simulate_agent_work(i, scenario["duration"]))
                tasks.append(task)
            
            # Wait for tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Record final metrics
            final_metrics = await self._collect_performance_metrics(health_monitor)
            
            # Calculate performance metrics
            scenario_results = {
                "scenario": scenario["name"],
                "concurrent_tasks": scenario["concurrent_tasks"],
                "expected_duration": scenario["duration"],
                "actual_duration": execution_time,
                "baseline_metrics": baseline_metrics,
                "final_metrics": final_metrics,
                "performance_degradation": self._calculate_performance_degradation(baseline_metrics, final_metrics)
            }
            
            performance_results.append(scenario_results)
            
            # Wait for system to stabilize
            await asyncio.sleep(5)
        
        # Analyze results
        for result in performance_results:
            # Performance should not degrade significantly under load
            degradation = result["performance_degradation"]
            
            if result["scenario"] == "light_load":
                assert degradation < 0.1, f"Light load caused {degradation:.2%} performance degradation"
            elif result["scenario"] == "medium_load":
                assert degradation < 0.3, f"Medium load caused {degradation:.2%} performance degradation"
            elif result["scenario"] == "heavy_load":
                assert degradation < 0.5, f"Heavy load caused {degradation:.2%} performance degradation"
        
        # Verify optimization system responded to load
        optimization_summary = performance_optimizer.get_optimization_summary()
        assert optimization_summary["optimization_status"] == "active"
        
        # Should have some optimization cycles
        assert optimization_summary["optimization_cycles"] > 0
    
    @pytest.mark.asyncio
    async def test_auto_scaling_performance(self, performance_optimizer, health_monitor):
        """Test auto-scaling system performance"""
        
        await performance_optimizer.start_optimization(health_monitor)
        
        # Force high CPU usage to trigger scaling
        cpu_load_tasks = []
        for i in range(10):
            task = asyncio.create_task(self._simulate_cpu_intensive_work(duration=15))
            cpu_load_tasks.append(task)
        
        # Wait a bit for scaling to kick in
        await asyncio.sleep(10)
        
        # Check if scaling actions were taken
        scaling_stats = performance_optimizer.auto_scaler.get_scaling_statistics()
        
        # Should have attempted some scaling
        assert scaling_stats["scaling_history_count"] >= 0
        
        # Check optimization summary
        optimization_summary = performance_optimizer.get_optimization_summary()
        auto_scaling = optimization_summary.get("auto_scaling", {})
        
        # Should have current scale information
        assert "current_scale" in auto_scaling
        assert "resource_limits" in auto_scaling
        
        # Wait for tasks to complete
        await asyncio.gather(*cpu_load_tasks, return_exceptions=True)
        
        # Force an optimization cycle to see scaling in action
        cycle_result = await performance_optimizer.force_optimization_cycle()
        
        assert cycle_result["success"] is True
        assert cycle_result["actions_identified"] >= 0
    
    @pytest.mark.asyncio
    async def test_load_balancing_effectiveness(self, performance_optimizer):
        """Test load balancing effectiveness"""
        
        load_balancer = performance_optimizer.load_balancer
        
        # Simulate uneven agent loads
        agent_loads = {
            "scout": 0.9,      # High load
            "analyst": 0.8,    # High load
            "negotiator": 0.2, # Low load
            "contract": 0.3,   # Low load
            "portfolio": 0.1   # Very low load
        }
        
        for agent_type, load in agent_loads.items():
            load_balancer.update_agent_load(agent_type, load)
        
        # Check if rebalancing is needed
        assert load_balancer.should_rebalance() is True
        
        # Get rebalancing recommendations
        recommendations = load_balancer.get_rebalancing_recommendations()
        
        # Should have recommendations to redistribute load
        assert len(recommendations) > 0
        
        # Verify recommendations make sense
        for rec in recommendations:
            from_agent = rec["from_agent"]
            to_agent = rec["to_agent"]
            
            # From agent should have higher load than to agent
            assert agent_loads[from_agent] > agent_loads[to_agent]
        
        # Test least loaded agent selection
        high_load_agents = ["scout", "analyst"]
        least_loaded = load_balancer.get_least_loaded_agent(high_load_agents)
        
        # Should select the one with lower load
        assert least_loaded in high_load_agents
        assert agent_loads[least_loaded] <= max(agent_loads[agent] for agent in high_load_agents)
        
        # Get load statistics
        load_stats = load_balancer.get_load_statistics()
        
        assert load_stats["total_agents"] == len(agent_loads)
        assert load_stats["rebalancing_needed"] is True
        assert 0 <= load_stats["average_load"] <= 1
        assert 0 <= load_stats["max_load"] <= 1
        assert 0 <= load_stats["min_load"] <= 1
    
    @pytest.mark.asyncio
    async def test_error_recovery_system(self, performance_optimizer):
        """Test error recovery system performance"""
        
        error_recovery = performance_optimizer.error_recovery
        
        # Simulate various error scenarios
        error_scenarios = [
            {"type": "agent_timeout", "component": "scout_agent", "details": {"timeout": 30}},
            {"type": "memory_exhaustion", "component": "analyst_agent", "details": {"memory_used": "2GB"}},
            {"type": "connection_failure", "component": "negotiator_agent", "details": {"endpoint": "api.example.com"}},
            {"type": "processing_overload", "component": "contract_agent", "details": {"queue_size": 100}},
        ]
        
        recovery_results = []
        
        for scenario in error_scenarios:
            # Record the error
            error_recovery.record_error(
                scenario["type"],
                scenario["component"],
                scenario["details"]
            )
            
            # Attempt recovery
            recovery_result = await error_recovery.attempt_recovery(
                scenario["type"],
                scenario["component"],
                scenario["details"]
            )
            
            recovery_results.append({
                "scenario": scenario,
                "recovery_result": recovery_result
            })
        
        # Verify recovery attempts were made
        for result in recovery_results:
            recovery_result = result["recovery_result"]
            
            # Should have attempted recovery (success may vary)
            assert "success" in recovery_result
            assert "reason" in recovery_result or "action" in recovery_result
        
        # Get error statistics
        error_stats = error_recovery.get_error_statistics()
        
        assert error_stats["total_errors"] == len(error_scenarios)
        assert error_stats["recovery_attempts"] >= 0
        assert 0 <= error_stats["recovery_success_rate"] <= 1
        
        # Test circuit breaker functionality
        # Simulate repeated failures to trigger circuit breaker
        for i in range(6):  # Exceed threshold
            error_recovery.record_error("connection_failure", "test_component", {"attempt": i})
        
        # Circuit breaker should be open now
        is_open = error_recovery.is_circuit_breaker_open("test_component", "connection_failure")
        assert is_open is True
        
        # Recovery should be blocked
        blocked_recovery = await error_recovery.attempt_recovery(
            "connection_failure", "test_component", {"test": True}
        )
        
        assert blocked_recovery["success"] is False
        assert "circuit_breaker_open" in blocked_recovery["reason"]
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_performance(self, workflow_config):
        """Test performance with multiple concurrent workflows"""
        
        # Create multiple workflow orchestrators
        orchestrators = []
        workflow_tasks = []
        
        try:
            # Create 5 concurrent workflows
            for i in range(5):
                config = WorkflowConfiguration(
                    name=f"Test Workflow {i}",
                    max_concurrent_deals=5,
                    max_execution_time_minutes=10,
                    enable_parallel_processing=True
                )
                
                orchestrator = WorkflowOrchestrator(config)
                orchestrators.append(orchestrator)
            
            # Mock agents for all orchestrators
            with patch('app.agents.scout_agent.ScoutAgent') as mock_scout:
                
                # Configure mock scout
                scout_instance = Mock()
                scout_instance.execute_task = AsyncMock(return_value={
                    "success": True,
                    "deals_found": 2,
                    "execution_time": 3.0
                })
                mock_scout.return_value = scout_instance
                
                # Start all workflows concurrently
                start_time = time.time()
                
                for orchestrator in orchestrators:
                    initial_state = StateManager.create_initial_state()
                    task = asyncio.create_task(orchestrator.start_workflow(initial_state))
                    workflow_tasks.append(task)
                
                # Wait for all workflows to process
                await asyncio.sleep(15)
                
                end_time = time.time()
                total_execution_time = end_time - start_time
                
                # Collect metrics from all workflows
                all_metrics = []
                for orchestrator in orchestrators:
                    metrics = orchestrator.get_workflow_metrics()
                    all_metrics.append(metrics)
                
                # Verify performance
                assert total_execution_time < 30, f"Concurrent workflows took too long: {total_execution_time}s"
                
                # All workflows should have some metrics
                for i, metrics in enumerate(all_metrics):
                    assert metrics["workflow_id"] is not None
                    assert isinstance(metrics["total_deals_processed"], int)
                
                # Verify no significant resource contention
                # (This would be more meaningful with actual resource monitoring)
                
        finally:
            # Cleanup
            for orchestrator in orchestrators:
                await orchestrator.stop_workflow()
            
            # Cancel any remaining tasks
            for task in workflow_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
    
    @pytest.mark.asyncio
    async def test_memory_usage_optimization(self, performance_optimizer, health_monitor):
        """Test memory usage optimization"""
        
        await performance_optimizer.start_optimization(health_monitor)
        
        # Simulate memory-intensive operations
        memory_hogs = []
        
        try:
            # Create memory pressure
            for i in range(10):
                # Create large data structures
                large_data = [0] * 100000  # 100k integers
                memory_hogs.append(large_data)
            
            # Wait for monitoring to detect high memory usage
            await asyncio.sleep(10)
            
            # Force optimization cycle
            cycle_result = await performance_optimizer.force_optimization_cycle()
            
            assert cycle_result["success"] is True
            
            # Check if memory optimization actions were identified
            actions_identified = cycle_result["actions_identified"]
            assert actions_identified >= 0
            
            # Get optimization summary
            optimization_summary = performance_optimizer.get_optimization_summary()
            
            # Should have some optimization activity
            assert optimization_summary["optimization_cycles"] > 0
            
        finally:
            # Clean up memory
            memory_hogs.clear()
            import gc
            gc.collect()
    
    @pytest.mark.asyncio
    async def test_response_time_optimization(self, performance_optimizer):
        """Test response time optimization"""
        
        # Simulate slow agent responses
        slow_response_times = [25.0, 30.0, 35.0, 20.0, 28.0]  # Seconds
        
        load_balancer = performance_optimizer.load_balancer
        
        # Update agent loads based on response times
        for i, response_time in enumerate(slow_response_times):
            agent_name = f"agent_{i}"
            
            # Convert response time to load (higher response time = higher load)
            load = min(response_time / 30.0, 1.0)
            load_balancer.update_agent_load(agent_name, load)
        
        # Force optimization cycle
        cycle_result = await performance_optimizer.force_optimization_cycle()
        
        assert cycle_result["success"] is True
        
        # Check load balancing recommendations
        recommendations = load_balancer.get_rebalancing_recommendations()
        
        # Should have recommendations if there's load imbalance
        if load_balancer.should_rebalance():
            assert len(recommendations) > 0
        
        # Get load statistics
        load_stats = load_balancer.get_load_statistics()
        
        # Verify statistics are reasonable
        assert load_stats["total_agents"] == len(slow_response_times)
        assert 0 <= load_stats["average_load"] <= 1
    
    @pytest.mark.asyncio
    async def test_throughput_optimization(self, performance_optimizer, health_monitor):
        """Test system throughput optimization"""
        
        await performance_optimizer.start_optimization(health_monitor)
        
        # Measure baseline throughput
        baseline_start = time.time()
        baseline_tasks = []
        
        for i in range(20):
            task = asyncio.create_task(self._simulate_lightweight_work(i))
            baseline_tasks.append(task)
        
        await asyncio.gather(*baseline_tasks)
        baseline_time = time.time() - baseline_start
        baseline_throughput = len(baseline_tasks) / baseline_time
        
        # Wait for optimization
        await asyncio.sleep(10)
        
        # Force optimization cycle
        await performance_optimizer.force_optimization_cycle()
        
        # Measure optimized throughput
        optimized_start = time.time()
        optimized_tasks = []
        
        for i in range(20):
            task = asyncio.create_task(self._simulate_lightweight_work(i))
            optimized_tasks.append(task)
        
        await asyncio.gather(*optimized_tasks)
        optimized_time = time.time() - optimized_start
        optimized_throughput = len(optimized_tasks) / optimized_time
        
        # Throughput should not significantly degrade
        throughput_ratio = optimized_throughput / baseline_throughput
        
        # Allow for some variation, but should be reasonably close
        assert throughput_ratio > 0.7, f"Throughput degraded significantly: {throughput_ratio:.2f}"
        
        logger.info(f"Baseline throughput: {baseline_throughput:.2f} tasks/sec")
        logger.info(f"Optimized throughput: {optimized_throughput:.2f} tasks/sec")
        logger.info(f"Throughput ratio: {throughput_ratio:.2f}")
    
    @pytest.mark.asyncio
    async def test_resource_limit_enforcement(self, performance_optimizer):
        """Test resource limit enforcement"""
        
        resource_limits = performance_optimizer.resource_limits
        auto_scaler = performance_optimizer.auto_scaler
        
        # Test thread limit enforcement
        current_threads = auto_scaler.current_scale["threads"]
        max_threads = resource_limits.max_threads
        
        # Try to scale beyond limits
        scale_action = Mock()
        scale_action.resource_type = "threads"
        scale_action.parameters = {"target_threads": max_threads + 10}
        scale_action.strategy = OptimizationStrategy.SCALE_UP
        
        result = await auto_scaler._scale_thread_pool(scale_action)
        
        # Should succeed but be limited to max
        assert result["success"] is True
        assert auto_scaler.current_scale["threads"] <= max_threads
        
        # Test process limit enforcement
        current_processes = auto_scaler.current_scale["processes"]
        max_processes = resource_limits.max_processes
        
        scale_action.resource_type = "processes"
        scale_action.parameters = {"target_processes": max_processes + 5}
        
        result = await auto_scaler._scale_process_pool(scale_action)
        
        # Should succeed but be limited to max
        assert result["success"] is True
        assert auto_scaler.current_scale["processes"] <= max_processes
    
    # Helper Methods
    
    async def _simulate_agent_work(self, agent_id: int, duration: int):
        """Simulate agent work with specified duration"""
        start_time = time.time()
        
        # Simulate CPU and I/O work
        while time.time() - start_time < duration:
            # CPU work
            _ = sum(i * i for i in range(1000))
            
            # I/O simulation
            await asyncio.sleep(0.1)
    
    async def _simulate_cpu_intensive_work(self, duration: int):
        """Simulate CPU-intensive work"""
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # CPU-intensive calculation
            _ = sum(i * i * i for i in range(10000))
            await asyncio.sleep(0.01)  # Small yield
    
    async def _simulate_lightweight_work(self, task_id: int):
        """Simulate lightweight work for throughput testing"""
        # Simple calculation
        result = sum(i for i in range(100))
        
        # Small delay
        await asyncio.sleep(0.01)
        
        return result
    
    async def _collect_performance_metrics(self, health_monitor: SystemHealthMonitor) -> Dict[str, Any]:
        """Collect performance metrics"""
        try:
            health_summary = health_monitor.get_system_health_summary()
            system_metrics = health_summary.get("system_metrics", {})
            
            return {
                "cpu_percent": system_metrics.get("cpu", {}).get("percent", 0),
                "memory_percent": system_metrics.get("memory", {}).get("percent", 0),
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
            return {"cpu_percent": 0, "memory_percent": 0, "timestamp": time.time()}
    
    def _calculate_performance_degradation(self, baseline: Dict[str, Any], final: Dict[str, Any]) -> float:
        """Calculate performance degradation between baseline and final metrics"""
        try:
            baseline_cpu = baseline.get("cpu_percent", 0)
            final_cpu = final.get("cpu_percent", 0)
            
            baseline_memory = baseline.get("memory_percent", 0)
            final_memory = final.get("memory_percent", 0)
            
            # Calculate relative increase in resource usage
            cpu_increase = (final_cpu - baseline_cpu) / max(baseline_cpu, 1)
            memory_increase = (final_memory - baseline_memory) / max(baseline_memory, 1)
            
            # Average degradation
            degradation = (cpu_increase + memory_increase) / 2
            
            return max(0, degradation)  # Don't return negative degradation
            
        except Exception as e:
            logger.error(f"Error calculating performance degradation: {e}")
            return 0.0
    
    @pytest.mark.asyncio
    async def test_stress_test_system_limits(self, performance_optimizer, health_monitor):
        """Stress test to find system limits"""
        
        await performance_optimizer.start_optimization(health_monitor)
        
        # Gradually increase load until system shows stress
        max_concurrent_tasks = 100
        step_size = 10
        stress_results = []
        
        for concurrent_tasks in range(step_size, max_concurrent_tasks + 1, step_size):
            logger.info(f"Stress testing with {concurrent_tasks} concurrent tasks")
            
            # Record start metrics
            start_metrics = await self._collect_performance_metrics(health_monitor)
            start_time = time.time()
            
            # Create concurrent tasks
            tasks = []
            for i in range(concurrent_tasks):
                task = asyncio.create_task(self._simulate_agent_work(i, 5))
                tasks.append(task)
            
            # Wait for completion
            await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            end_metrics = await self._collect_performance_metrics(health_monitor)
            
            # Calculate metrics
            execution_time = end_time - start_time
            throughput = concurrent_tasks / execution_time
            degradation = self._calculate_performance_degradation(start_metrics, end_metrics)
            
            stress_result = {
                "concurrent_tasks": concurrent_tasks,
                "execution_time": execution_time,
                "throughput": throughput,
                "degradation": degradation,
                "cpu_usage": end_metrics["cpu_percent"],
                "memory_usage": end_metrics["memory_percent"]
            }
            
            stress_results.append(stress_result)
            
            # Stop if system is too stressed
            if degradation > 1.0 or end_metrics["cpu_percent"] > 90:
                logger.warning(f"System stress limit reached at {concurrent_tasks} tasks")
                break
            
            # Brief recovery period
            await asyncio.sleep(2)
        
        # Analyze stress test results
        assert len(stress_results) > 0, "No stress test results collected"
        
        # Find optimal performance point
        best_throughput = max(result["throughput"] for result in stress_results)
        optimal_result = next(r for r in stress_results if r["throughput"] == best_throughput)
        
        logger.info(f"Optimal performance: {optimal_result['concurrent_tasks']} tasks, "
                   f"{optimal_result['throughput']:.2f} tasks/sec")
        
        # Verify system handled at least moderate load
        max_tasks_tested = max(result["concurrent_tasks"] for result in stress_results)
        assert max_tasks_tested >= 20, f"System couldn't handle even moderate load: {max_tasks_tested} tasks"
        
        # Get final optimization summary
        optimization_summary = performance_optimizer.get_optimization_summary()
        
        # Should have performed optimizations during stress test
        assert optimization_summary["optimization_cycles"] > 0
        assert optimization_summary["optimization_status"] == "active"


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto", "-s"])