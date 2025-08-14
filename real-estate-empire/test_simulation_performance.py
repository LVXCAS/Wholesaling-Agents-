"""
Performance testing suite for simulation components
Tests scalability, memory usage, and response times
"""
import asyncio
import os
import sys
import time
import psutil
import json
from datetime import datetime
from typing import Dict, List, Any
import concurrent.futures

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from simulation.homeowner_simulator import HomeownerConversationSimulator, ConversationContext
from simulation.market_simulator import MarketSimulator
from simulation.agent_trainer import AgentTrainer
from services.market_data_service import MarketDataService
from services.investment_analyzer_service import InvestmentAnalyzerService

class PerformanceMonitor:
    """Monitor system performance during tests"""
    
    def __init__(self):
        self.start_time = None
        self.start_memory = None
        self.measurements = []
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.measurements = []
    
    def record_measurement(self, operation: str, duration: float, memory_delta: float = None):
        """Record a performance measurement"""
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        if memory_delta is None:
            memory_delta = current_memory - self.start_memory
        
        self.measurements.append({
            "operation": operation,
            "duration": duration,
            "memory_usage": current_memory,
            "memory_delta": memory_delta,
            "timestamp": time.time() - self.start_time
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.measurements:
            return {"error": "No measurements recorded"}
        
        durations = [m["duration"] for m in self.measurements]
        memory_deltas = [m["memory_delta"] for m in self.measurements]
        
        return {
            "total_operations": len(self.measurements),
            "total_time": time.time() - self.start_time,
            "average_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "total_memory_delta": max(memory_deltas) - min(memory_deltas),
            "peak_memory_usage": max(m["memory_usage"] for m in self.measurements),
            "measurements": self.measurements
        }

async def test_homeowner_simulator_scalability():
    """Test homeowner simulator scalability"""
    print("🏠 Testing Homeowner Simulator Scalability")
    print("=" * 50)
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    simulator = HomeownerConversationSimulator()
    
    # Test different batch sizes
    batch_sizes = [1, 5, 10, 25, 50]
    results = {}
    
    for batch_size in batch_sizes:
        print(f"\nTesting batch size: {batch_size}")
        
        property_data_list = [
            {
                "asking_price": 300000 + (i * 10000),
                "city": "Miami",
                "state": "Florida",
                "bedrooms": 3,
                "bathrooms": 2,
                "house_size": 1800,
                "property_type": "single_family"
            }
            for i in range(3)  # 3 different properties
        ]
        
        scenario_types = ["cold_call", "follow_up", "negotiation"]
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        try:
            conversations = await simulator.generate_conversation_batch(
                property_data_list, scenario_types, count=batch_size
            )
            
            duration = time.time() - start_time
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_delta = end_memory - start_memory
            
            results[batch_size] = {
                "conversations_generated": len(conversations),
                "duration": duration,
                "memory_delta": memory_delta,
                "conversations_per_second": len(conversations) / duration,
                "memory_per_conversation": memory_delta / len(conversations) if conversations else 0
            }
            
            monitor.record_measurement(f"batch_{batch_size}", duration, memory_delta)
            
            print(f"  Generated {len(conversations)} conversations in {duration:.2f}s")
            print(f"  Rate: {len(conversations) / duration:.2f} conversations/second")
            print(f"  Memory usage: {memory_delta:.2f} MB")
            
        except Exception as e:
            print(f"  Failed: {e}")
            results[batch_size] = {"error": str(e)}
    
    print(f"\n📊 Scalability Analysis:")
    for batch_size, data in results.items():
        if "error" not in data:
            print(f"  Batch {batch_size}: {data['conversations_per_second']:.2f} conv/s, {data['memory_per_conversation']:.2f} MB/conv")
    
    return results

async def test_concurrent_operations():
    """Test concurrent simulation operations"""
    print("\n⚡ Testing Concurrent Operations")
    print("=" * 50)
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # Initialize services
    simulator = HomeownerConversationSimulator()
    market_service = MarketDataService()
    market_simulator = MarketSimulator(market_service)
    investment_analyzer = InvestmentAnalyzerService()
    agent_trainer = AgentTrainer(market_simulator, investment_analyzer)
    
    async def generate_conversation():
        """Generate a single conversation"""
        property_data = {
            "asking_price": 400000,
            "city": "Tampa",
            "state": "Florida",
            "bedrooms": 3,
            "bathrooms": 2,
            "house_size": 1800,
            "property_type": "single_family"
        }
        
        profile = simulator.generate_homeowner_profile(property_data)
        context = ConversationContext(
            scenario_type="cold_call",
            property_details=property_data,
            market_conditions={"trend": "stable", "inventory": "normal"},
            previous_interactions=[],
            agent_goal="Schedule property evaluation",
            difficulty_level=0.5
        )
        
        return await simulator.generate_conversation_scenario(profile, context)
    
    async def analyze_market():
        """Analyze market conditions"""
        return await market_simulator.get_ai_market_analysis()
    
    async def train_agent():
        """Train an agent"""
        from test_simulation_comprehensive import AdvancedMockAgent
        agent = AdvancedMockAgent("concurrent_test", "balanced")
        scenario = agent_trainer.create_training_scenario("deal_analysis", 0.5)
        return await agent_trainer.train_agent(agent, scenario)
    
    # Test different concurrency levels
    concurrency_levels = [1, 2, 5, 10]
    results = {}
    
    for concurrency in concurrency_levels:
        print(f"\nTesting concurrency level: {concurrency}")
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Create tasks
        tasks = []
        for i in range(concurrency):
            if i % 3 == 0:
                tasks.append(generate_conversation())
            elif i % 3 == 1:
                tasks.append(analyze_market())
            else:
                tasks.append(train_agent())
        
        try:
            # Run tasks concurrently
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            duration = time.time() - start_time
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_delta = end_memory - start_memory
            
            # Count successful operations
            successful = sum(1 for result in task_results if not isinstance(result, Exception))
            
            results[concurrency] = {
                "total_tasks": len(tasks),
                "successful_tasks": successful,
                "duration": duration,
                "memory_delta": memory_delta,
                "tasks_per_second": successful / duration,
                "success_rate": successful / len(tasks) * 100
            }
            
            monitor.record_measurement(f"concurrent_{concurrency}", duration, memory_delta)
            
            print(f"  Completed {successful}/{len(tasks)} tasks in {duration:.2f}s")
            print(f"  Rate: {successful / duration:.2f} tasks/second")
            print(f"  Success rate: {successful / len(tasks) * 100:.1f}%")
            print(f"  Memory usage: {memory_delta:.2f} MB")
            
        except Exception as e:
            print(f"  Failed: {e}")
            results[concurrency] = {"error": str(e)}
    
    print(f"\n📊 Concurrency Analysis:")
    for concurrency, data in results.items():
        if "error" not in data:
            print(f"  Level {concurrency}: {data['tasks_per_second']:.2f} tasks/s, {data['success_rate']:.1f}% success")
    
    return results

async def test_memory_usage_patterns():
    """Test memory usage patterns over time"""
    print("\n💾 Testing Memory Usage Patterns")
    print("=" * 50)
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    simulator = HomeownerConversationSimulator()
    
    # Track memory usage over multiple operations
    memory_snapshots = []
    operations = []
    
    def take_memory_snapshot(operation: str):
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        memory_snapshots.append(memory_mb)
        operations.append(operation)
        return memory_mb
    
    initial_memory = take_memory_snapshot("initial")
    print(f"Initial memory usage: {initial_memory:.2f} MB")
    
    # Perform various operations and track memory
    property_data = {
        "asking_price": 400000,
        "city": "Miami",
        "state": "Florida",
        "bedrooms": 3,
        "bathrooms": 2,
        "house_size": 1800,
        "property_type": "single_family"
    }
    
    # Generate multiple conversations
    for i in range(10):
        profile = simulator.generate_homeowner_profile(property_data)
        context = ConversationContext(
            scenario_type="cold_call",
            property_details=property_data,
            market_conditions={"trend": "stable", "inventory": "normal"},
            previous_interactions=[],
            agent_goal="Schedule property evaluation",
            difficulty_level=0.5
        )
        
        await simulator.generate_conversation_scenario(profile, context)
        memory = take_memory_snapshot(f"conversation_{i+1}")
        
        if i % 3 == 0:
            print(f"  After {i+1} conversations: {memory:.2f} MB")
    
    # Analyze memory patterns
    memory_growth = memory_snapshots[-1] - memory_snapshots[0]
    max_memory = max(memory_snapshots)
    min_memory = min(memory_snapshots)
    avg_memory = sum(memory_snapshots) / len(memory_snapshots)
    
    print(f"\nMemory Usage Analysis:")
    print(f"  Initial memory: {initial_memory:.2f} MB")
    print(f"  Final memory: {memory_snapshots[-1]:.2f} MB")
    print(f"  Total growth: {memory_growth:.2f} MB")
    print(f"  Peak memory: {max_memory:.2f} MB")
    print(f"  Average memory: {avg_memory:.2f} MB")
    print(f"  Memory per operation: {memory_growth / (len(memory_snapshots) - 1):.2f} MB")
    
    return {
        "initial_memory": initial_memory,
        "final_memory": memory_snapshots[-1],
        "memory_growth": memory_growth,
        "peak_memory": max_memory,
        "average_memory": avg_memory,
        "memory_snapshots": memory_snapshots,
        "operations": operations
    }

async def test_response_time_distribution():
    """Test response time distribution for different operations"""
    print("\n⏱️ Testing Response Time Distribution")
    print("=" * 50)
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # Initialize services
    simulator = HomeownerConversationSimulator()
    market_service = MarketDataService()
    market_simulator = MarketSimulator(market_service)
    
    operations = {
        "profile_generation": [],
        "conversation_generation": [],
        "market_analysis": [],
        "deal_generation": []
    }
    
    # Test profile generation
    print("Testing profile generation...")
    for i in range(20):
        property_data = {
            "asking_price": 300000 + (i * 10000),
            "city": "Miami",
            "state": "Florida",
            "bedrooms": 3,
            "bathrooms": 2,
            "house_size": 1800,
            "property_type": "single_family"
        }
        
        start_time = time.time()
        simulator.generate_homeowner_profile(property_data)
        duration = time.time() - start_time
        operations["profile_generation"].append(duration)
    
    # Test conversation generation
    print("Testing conversation generation...")
    for i in range(10):
        property_data = {
            "asking_price": 400000,
            "city": "Tampa",
            "state": "Florida",
            "bedrooms": 3,
            "bathrooms": 2,
            "house_size": 1800,
            "property_type": "single_family"
        }
        
        profile = simulator.generate_homeowner_profile(property_data)
        context = ConversationContext(
            scenario_type="cold_call",
            property_details=property_data,
            market_conditions={"trend": "stable", "inventory": "normal"},
            previous_interactions=[],
            agent_goal="Schedule property evaluation",
            difficulty_level=0.5
        )
        
        start_time = time.time()
        await simulator.generate_conversation_scenario(profile, context)
        duration = time.time() - start_time
        operations["conversation_generation"].append(duration)
    
    # Test market analysis
    print("Testing market analysis...")
    for i in range(10):
        start_time = time.time()
        await market_simulator.get_ai_market_analysis()
        duration = time.time() - start_time
        operations["market_analysis"].append(duration)
    
    # Test deal generation
    print("Testing deal generation...")
    for i in range(15):
        start_time = time.time()
        try:
            market_simulator.generate_deal_scenario()
            duration = time.time() - start_time
            operations["deal_generation"].append(duration)
        except:
            pass  # Expected if no data
    
    # Analyze response times
    results = {}
    for operation, times in operations.items():
        if times:
            times.sort()
            n = len(times)
            
            results[operation] = {
                "count": n,
                "min": min(times),
                "max": max(times),
                "average": sum(times) / n,
                "median": times[n // 2],
                "p95": times[int(n * 0.95)] if n > 1 else times[0],
                "p99": times[int(n * 0.99)] if n > 1 else times[0]
            }
        else:
            results[operation] = {"count": 0, "error": "No successful operations"}
    
    print(f"\nResponse Time Analysis:")
    for operation, stats in results.items():
        if "error" not in stats:
            print(f"  {operation.replace('_', ' ').title()}:")
            print(f"    Count: {stats['count']}")
            print(f"    Average: {stats['average']:.3f}s")
            print(f"    Median: {stats['median']:.3f}s")
            print(f"    95th percentile: {stats['p95']:.3f}s")
            print(f"    Min/Max: {stats['min']:.3f}s / {stats['max']:.3f}s")
    
    return results

async def test_stress_conditions():
    """Test system behavior under stress conditions"""
    print("\n🔥 Testing Stress Conditions")
    print("=" * 50)
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    simulator = HomeownerConversationSimulator()
    
    # Stress test parameters
    stress_duration = 30  # seconds
    max_concurrent = 20
    
    print(f"Running stress test for {stress_duration} seconds with up to {max_concurrent} concurrent operations...")
    
    start_time = time.time()
    completed_operations = 0
    failed_operations = 0
    active_tasks = set()
    
    async def stress_operation():
        """Single stress test operation"""
        nonlocal completed_operations, failed_operations
        
        try:
            property_data = {
                "asking_price": 400000,
                "city": "Miami",
                "state": "Florida",
                "bedrooms": 3,
                "bathrooms": 2,
                "house_size": 1800,
                "property_type": "single_family"
            }
            
            profile = simulator.generate_homeowner_profile(property_data)
            context = ConversationContext(
                scenario_type="cold_call",
                property_details=property_data,
                market_conditions={"trend": "stable", "inventory": "normal"},
                previous_interactions=[],
                agent_goal="Schedule property evaluation",
                difficulty_level=0.5
            )
            
            await simulator.generate_conversation_scenario(profile, context)
            completed_operations += 1
            
        except Exception as e:
            failed_operations += 1
            print(f"    Operation failed: {e}")
    
    # Run stress test
    while time.time() - start_time < stress_duration:
        # Maintain concurrent operations
        while len(active_tasks) < max_concurrent:
            task = asyncio.create_task(stress_operation())
            active_tasks.add(task)
        
        # Clean up completed tasks
        done_tasks = [task for task in active_tasks if task.done()]
        for task in done_tasks:
            active_tasks.remove(task)
        
        await asyncio.sleep(0.1)  # Small delay to prevent overwhelming
    
    # Wait for remaining tasks to complete
    if active_tasks:
        await asyncio.gather(*active_tasks, return_exceptions=True)
    
    total_time = time.time() - start_time
    total_operations = completed_operations + failed_operations
    
    # Get final memory usage
    final_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    print(f"\nStress Test Results:")
    print(f"  Duration: {total_time:.2f} seconds")
    print(f"  Total operations attempted: {total_operations}")
    print(f"  Completed operations: {completed_operations}")
    print(f"  Failed operations: {failed_operations}")
    print(f"  Success rate: {completed_operations / total_operations * 100:.1f}%")
    print(f"  Operations per second: {completed_operations / total_time:.2f}")
    print(f"  Final memory usage: {final_memory:.2f} MB")
    
    return {
        "duration": total_time,
        "total_operations": total_operations,
        "completed_operations": completed_operations,
        "failed_operations": failed_operations,
        "success_rate": completed_operations / total_operations * 100 if total_operations > 0 else 0,
        "operations_per_second": completed_operations / total_time,
        "final_memory": final_memory
    }

async def run_performance_tests():
    """Run all performance tests"""
    print("🚀 Starting Performance Test Suite")
    print("=" * 60)
    
    test_results = {}
    
    # Run performance tests
    tests = [
        ("Scalability", test_homeowner_simulator_scalability),
        ("Concurrent Operations", test_concurrent_operations),
        ("Memory Usage", test_memory_usage_patterns),
        ("Response Times", test_response_time_distribution),
        ("Stress Conditions", test_stress_conditions)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            start_time = time.time()
            result = await test_func()
            test_time = time.time() - start_time
            
            test_results[test_name] = {
                "result": result,
                "execution_time": test_time,
                "status": "passed"
            }
            print(f"✅ {test_name} completed in {test_time:.2f} seconds")
            
        except Exception as e:
            test_results[test_name] = {
                "error": str(e),
                "status": "failed"
            }
            print(f"❌ {test_name} failed: {e}")
    
    # Generate performance report
    print(f"\n{'='*60}")
    print("📊 PERFORMANCE TEST REPORT")
    print("=" * 60)
    
    passed = sum(1 for result in test_results.values() if result["status"] == "passed")
    total = len(test_results)
    
    print(f"Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"\nPerformance Summary:")
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result["status"] == "passed" else "❌ FAILED"
        if result["status"] == "passed":
            time_info = f" ({result['execution_time']:.2f}s)"
        else:
            time_info = f" - Error: {result['error']}"
        
        print(f"  {test_name}: {status}{time_info}")
    
    # Save performance report
    report_file = f"performance_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed performance report saved to: {report_file}")
    
    if passed == total:
        print("🎉 All performance tests passed! System is performing well under load.")
    else:
        print("⚠️ Some performance tests failed. Check the detailed report for optimization opportunities.")
    
    return test_results

if __name__ == "__main__":
    # Set up environment
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️ Warning: GEMINI_API_KEY not found in environment")
        print("Loading from .env file...")
        
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('GEMINI_API_KEY='):
                        key = line.split('=', 1)[1].strip()
                        os.environ['GEMINI_API_KEY'] = key
                        print("✅ Gemini API key loaded from .env file")
                        break
    
    # Run performance tests
    asyncio.run(run_performance_tests())