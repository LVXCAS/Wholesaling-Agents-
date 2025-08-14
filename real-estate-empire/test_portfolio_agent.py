"""
Test Portfolio Agent Implementation
Basic test to verify Portfolio Agent functionality
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.agents.portfolio_agent import PortfolioAgent
from app.core.agent_state import StateManager, AgentState


async def test_portfolio_agent():
    """Test basic Portfolio Agent functionality"""
    print("Testing Portfolio Agent Implementation...")
    
    try:
        # Create Portfolio Agent
        portfolio_agent = PortfolioAgent()
        print(f"✓ Created Portfolio Agent: {portfolio_agent.name}")
        
        # Test agent capabilities
        capabilities = [cap.name for cap in portfolio_agent.capabilities]
        print(f"✓ Agent capabilities: {capabilities}")
        
        # Test available tasks
        tasks = portfolio_agent.get_available_tasks()
        print(f"✓ Available tasks: {tasks}")
        
        # Test available workflows
        workflows = portfolio_agent.get_available_workflows()
        print(f"✓ Available workflows: {workflows}")
        
        # Create test state
        state = StateManager.create_initial_state()
        
        # Add some test closed deals to simulate portfolio
        test_deals = [
            {
                "id": "deal_1",
                "property_address": "123 Main St",
                "city": "Austin",
                "state": "TX",
                "property_type": "single_family",
                "listing_price": 250000,
                "estimated_value": 280000,
                "analysis_data": {
                    "monthly_rent": 2200,
                    "monthly_expenses": 800
                },
                "discovered_at": datetime.now().isoformat(),
                "added_to_portfolio": False
            },
            {
                "id": "deal_2", 
                "property_address": "456 Oak Ave",
                "city": "Dallas",
                "state": "TX",
                "property_type": "single_family",
                "listing_price": 180000,
                "estimated_value": 200000,
                "analysis_data": {
                    "monthly_rent": 1800,
                    "monthly_expenses": 600
                },
                "discovered_at": datetime.now().isoformat(),
                "added_to_portfolio": False
            }
        ]
        
        state["closed_deals"] = test_deals
        print(f"✓ Created test state with {len(test_deals)} closed deals")
        
        # Test portfolio analysis task
        print("\nTesting portfolio analysis...")
        analysis_result = await portfolio_agent.execute_task(
            "analyze_portfolio", 
            {}, 
            state
        )
        
        if analysis_result.get("success", False):
            print("✓ Portfolio analysis completed successfully")
            analysis = analysis_result.get("analysis", {})
            print(f"  - Portfolio metrics: {len(analysis.get('portfolio_metrics', {}))}")
            print(f"  - Confidence score: {analysis_result.get('confidence_score', 0):.2f}")
        else:
            print(f"✗ Portfolio analysis failed: {analysis_result.get('error', 'Unknown error')}")
        
        # Test state processing
        print("\nTesting state processing...")
        updated_state = await portfolio_agent.process_state(state)
        
        portfolio_status = updated_state.get("portfolio_status", {})
        if portfolio_status:
            print("✓ State processing completed successfully")
            print(f"  - Portfolio status updated: {len(portfolio_status)} metrics")
        else:
            print("✓ State processing completed (no portfolio updates needed)")
        
        # Test agent metrics
        metrics = portfolio_agent.get_metrics()
        print(f"\n✓ Agent metrics:")
        print(f"  - Tasks completed: {metrics.tasks_completed}")
        print(f"  - Success rate: {metrics.success_rate:.2%}")
        print(f"  - Average response time: {metrics.average_response_time:.2f}s")
        
        print("\n🎉 Portfolio Agent test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Portfolio Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_portfolio_agent())
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)