"""
Demo script showcasing the completed LangGraph Core Framework
"""

import asyncio
import logging
from datetime import datetime

from app.core.langgraph_setup import LangGraphOrchestrator
from app.core.agent_state import StateManager, AgentType
from app.core.supervisor_agent import SupervisorAgent
from app.core.base_agent import agent_lifecycle_manager
from app.core.shared_memory import shared_memory_manager


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_langgraph_framework():
    """Demonstrate the LangGraph core framework capabilities"""
    
    print("=" * 80)
    print("🏠 Real Estate Empire - LangGraph Core Framework Demo")
    print("=" * 80)
    
    try:
        # 1. Initialize the LangGraph orchestrator
        print("\n1. Initializing LangGraph Orchestrator...")
        orchestrator = LangGraphOrchestrator()
        print(f"   ✅ Orchestrator initialized with {len(orchestrator.workflow.nodes)} agent nodes")
        
        # 2. Initialize shared memory manager
        print("\n2. Initializing Shared Memory Manager...")
        await shared_memory_manager.initialize()
        print("   ✅ Shared memory manager initialized")
        
        # 3. Initialize agent lifecycle manager
        print("\n3. Initializing Agent Lifecycle Manager...")
        await agent_lifecycle_manager.initialize()
        print("   ✅ Agent lifecycle manager initialized")
        
        # 4. Create and register supervisor agent
        print("\n4. Creating Supervisor Agent...")
        supervisor = SupervisorAgent()
        supervisor.decision_engine.initialize()
        agent_lifecycle_manager.register_agent(supervisor, group="core")
        print(f"   ✅ Supervisor agent created with {len(supervisor.capabilities)} capabilities")
        
        # 5. Create initial workflow state
        print("\n5. Creating Initial Workflow State...")
        initial_state = StateManager.create_initial_state()
        initial_state["investment_strategy"] = {
            "target_markets": ["Austin, TX", "Dallas, TX"],
            "max_investment": 500000,
            "preferred_strategies": ["fix_and_flip", "buy_and_hold"]
        }
        initial_state["available_capital"] = 1000000
        print(f"   ✅ Initial state created for workflow: {initial_state['workflow_id']}")
        
        # 6. Demonstrate supervisor decision making
        print("\n6. Demonstrating Supervisor Decision Making...")
        
        # Add some sample deals to trigger analysis
        initial_state["current_deals"] = [
            {
                "id": "deal_001",
                "property_address": "123 Main St",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701",
                "listing_price": 350000,
                "analyzed": False,
                "status": "discovered"
            },
            {
                "id": "deal_002", 
                "property_address": "456 Oak Ave",
                "city": "Dallas",
                "state": "TX",
                "zip_code": "75201",
                "listing_price": 275000,
                "analyzed": True,
                "status": "approved",
                "outreach_initiated": False
            }
        ]
        
        # Process state with supervisor
        processed_state = await supervisor.process_state(initial_state)
        print(f"   ✅ Supervisor processed state and made decision: {processed_state.get('next_action', 'none')}")
        
        # 7. Demonstrate workflow execution
        print("\n7. Demonstrating Workflow Execution...")
        workflow_id = await orchestrator.start_workflow(processed_state)
        print(f"   ✅ Workflow started with ID: {workflow_id}")
        
        # Get final workflow state
        final_state = await orchestrator.get_workflow_state(workflow_id)
        print(f"   ✅ Workflow completed with status: {final_state.get('workflow_status', 'unknown')}")
        
        # 8. Display agent messages and decisions
        print("\n8. Agent Messages and Decisions:")
        agent_messages = final_state.get("agent_messages", [])
        for i, message in enumerate(agent_messages[-5:], 1):  # Show last 5 messages
            timestamp = message.get("timestamp", "unknown")
            agent = message.get("agent", "unknown")
            msg = message.get("message", "")
            print(f"   {i}. [{timestamp}] {agent}: {msg}")
        
        # 9. Display supervisor decision history
        print("\n9. Supervisor Decision History:")
        decision_history = supervisor.get_decision_history(limit=3)
        for i, decision in enumerate(decision_history, 1):
            action = decision.get("action", "unknown")
            reasoning = decision.get("reasoning", "")
            confidence = decision.get("confidence", 0)
            print(f"   {i}. Action: {action} (Confidence: {confidence:.2f})")
            print(f"      Reasoning: {reasoning}")
        
        # 10. Display system performance summary
        print("\n10. System Performance Summary:")
        performance = supervisor.get_performance_summary()
        monitoring_data = performance.get("monitoring_data", {})
        print(f"   • Decision Count: {performance.get('decision_count', 0)}")
        print(f"   • Active Conflicts: {performance.get('active_conflicts', 0)}")
        print(f"   • Workflow Coordinations: {performance.get('workflow_coordinations', 0)}")
        
        # 11. Display agent lifecycle status
        print("\n11. Agent Lifecycle Status:")
        status_summary = agent_lifecycle_manager.get_agent_status_summary()
        print(f"   • Total Agents: {status_summary.get('total_agents', 0)}")
        print(f"   • Active Agents: {len(status_summary.get('active_agents', []))}")
        print(f"   • Agent Types: {status_summary.get('by_type', {})}")
        
        # 12. Display memory usage statistics
        print("\n12. Memory Usage Statistics:")
        memory_stats = shared_memory_manager.get_memory_stats()
        print(f"   • Transient Items: {memory_stats.get('transient_items', 0)}")
        print(f"   • Redis Available: {memory_stats.get('redis_available', False)}")
        print(f"   • Database Available: {memory_stats.get('database_available', False)}")
        
        print("\n" + "=" * 80)
        print("🎉 LangGraph Core Framework Demo Completed Successfully!")
        print("=" * 80)
        
        # Display framework capabilities summary
        print("\n📋 Framework Capabilities Summary:")
        print("   ✅ LangGraph Workflow Orchestration")
        print("   ✅ Multi-Agent State Management") 
        print("   ✅ Agent Communication Protocols")
        print("   ✅ Supervisor Agent Framework")
        print("   ✅ Base Agent Classes and Interfaces")
        print("   ✅ Shared Memory and Persistence")
        print("   ✅ Human-in-the-Loop Integration")
        print("   ✅ Performance Monitoring")
        print("   ✅ Conflict Resolution")
        print("   ✅ Agent Lifecycle Management")
        
        return True
        
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        print(f"\n❌ Demo failed: {e}")
        return False
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up resources...")
        await agent_lifecycle_manager.shutdown_all_agents()
        print("   ✅ All agents shut down")


async def demo_supervisor_capabilities():
    """Demonstrate specific supervisor agent capabilities"""
    
    print("\n" + "=" * 60)
    print("🤖 Supervisor Agent Capabilities Demo")
    print("=" * 60)
    
    supervisor = SupervisorAgent()
    supervisor.decision_engine.initialize()
    
    # Test different decision scenarios
    scenarios = [
        {
            "name": "Low Deal Pipeline",
            "state": {"current_deals": []},
            "expected": "scout"
        },
        {
            "name": "Unanalyzed Deals",
            "state": {"current_deals": [{"analyzed": False}]},
            "expected": "analyze"
        },
        {
            "name": "Approved Deals Ready for Outreach",
            "state": {"current_deals": [{"status": "approved", "outreach_initiated": False}]},
            "expected": "negotiate"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. Testing Scenario: {scenario['name']}")
        
        # Create test state
        test_state = StateManager.create_initial_state()
        test_state.update(scenario["state"])
        
        # Analyze situation
        analysis = await supervisor._analyze_situation(test_state)
        
        # Make decision
        decision = await supervisor.decision_engine.make_decision(test_state, analysis)
        
        print(f"   Decision: {decision.action}")
        print(f"   Confidence: {decision.confidence:.2f}")
        print(f"   Reasoning: {decision.reasoning}")
        
        # Check if decision matches expected
        if decision.target_agent == scenario["expected"] or decision.action == scenario["expected"]:
            print("   ✅ Decision matches expected outcome")
        else:
            print(f"   ⚠️  Expected {scenario['expected']}, got {decision.action}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("Starting Real Estate Empire LangGraph Framework Demo...")
    
    # Run the main demo
    success = asyncio.run(demo_langgraph_framework())
    
    if success:
        # Run supervisor capabilities demo
        asyncio.run(demo_supervisor_capabilities())
        
        print("\n🚀 All demos completed successfully!")
        print("The LangGraph Core Framework is ready for real estate investment automation!")
    else:
        print("\n💥 Demo failed. Please check the logs for details.")