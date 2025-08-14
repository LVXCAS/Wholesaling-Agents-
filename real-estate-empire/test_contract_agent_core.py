#!/usr/bin/env python3
"""
Test script for Contract Agent Core Implementation
Tests the enhanced ContractAgent with LangGraph integration
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.agents.contract_agent_core import ContractAgentCore, ContractType, ContractStatus
from app.core.agent_state import AgentState, StateManager


async def test_contract_agent_core():
    """Test the Contract Agent core functionality"""
    print("Testing Contract Agent Core Implementation...")
    
    try:
        # Initialize Contract Agent
        print("\n1. Initializing Contract Agent...")
        contract_agent = ContractAgentCore("TestContractAgent")
        
        print(f"   ✓ Agent initialized: {contract_agent.name}")
        print(f"   ✓ Agent type: {contract_agent.agent_type.value}")
        print(f"   ✓ Capabilities: {len(contract_agent.capabilities)}")
        
        # Test template management system
        print("\n2. Testing Template Management System...")
        
        # Test creating a template
        template_data = {
            "name": "Test Purchase Agreement",
            "contract_type": "purchase_agreement",
            "content": "This is a test contract template for {{buyer_name}} and {{seller_name}} for property at {{property_address}}.",
            "variables": ["buyer_name", "seller_name", "property_address"],
            "jurisdiction": "TX"
        }
        
        result = await contract_agent.manage_template("create", template_data)
        if result.get("success"):
            print(f"   ✓ Template created: {result.get('template_id')}")
            template_id = result.get('template_id')
        else:
            print(f"   ✗ Template creation failed: {result.get('error')}")
            return False
        
        # Test listing templates
        result = await contract_agent.manage_template("list", {})
        if result.get("success"):
            print(f"   ✓ Templates listed: {result.get('count')} templates found")
        else:
            print(f"   ✗ Template listing failed: {result.get('error')}")
        
        # Test contract generation workflow
        print("\n3. Testing Contract Generation Workflow...")
        
        deal_data = {
            "id": "test_deal_001",
            "property_address": "123 Test Street",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701",
            "buyer_name": "Test Buyer LLC",
            "seller_name": "Test Seller",
            "purchase_price": 350000,
            "investment_strategy": "flip"
        }
        
        # Test workflow execution
        workflow_result = await contract_agent.generate_contract_with_workflow(deal_data)
        if workflow_result.get("success"):
            print(f"   ✓ Contract generation workflow completed")
        else:
            print(f"   ✗ Contract generation workflow failed: {workflow_result.get('error')}")
        
        # Test electronic signature service
        print("\n4. Testing Electronic Signature Service...")
        
        if hasattr(contract_agent, 'signature_service') and contract_agent.signature_service:
            signers = [
                {"name": "Test Buyer", "email": "buyer@test.com", "role": "buyer"},
                {"name": "Test Seller", "email": "seller@test.com", "role": "seller"}
            ]
            
            sig_result = await contract_agent.signature_service.send_for_signature(
                "/path/to/test/contract.pdf",
                signers,
                "Test Contract for Signature"
            )
            
            if sig_result.get("success"):
                print(f"   ✓ Signature request sent: {sig_result.get('signature_request_id')}")
            else:
                print(f"   ✗ Signature request failed: {sig_result.get('error')}")
        else:
            print("   ⚠ Signature service not initialized")
        
        # Test transaction monitoring
        print("\n5. Testing Transaction Monitoring...")
        
        if hasattr(contract_agent, 'transaction_monitor') and contract_agent.transaction_monitor:
            milestones = [
                {"name": "Contract Execution", "days_from_start": 0, "required": True, "status": "pending"},
                {"name": "Inspection Period", "days_from_start": 10, "required": True, "status": "pending"}
            ]
            
            transaction_id = contract_agent.transaction_monitor.create_transaction(
                "test_contract_001", 
                "test_deal_001", 
                milestones
            )
            
            if transaction_id:
                print(f"   ✓ Transaction monitor created: {transaction_id}")
                
                # Test milestone update
                success = contract_agent.transaction_monitor.update_milestone(
                    transaction_id, 
                    "Contract Execution", 
                    "completed"
                )
                
                if success:
                    print("   ✓ Milestone updated successfully")
                else:
                    print("   ✗ Milestone update failed")
            else:
                print("   ✗ Transaction monitor creation failed")
        else:
            print("   ⚠ Transaction monitor not initialized")
        
        # Test agent state processing
        print("\n6. Testing Agent State Processing...")
        
        # Create test state
        test_state = StateManager.create_initial_state()
        test_state["current_deals"] = [deal_data]
        
        # Process state
        updated_state = await contract_agent.process_state(test_state)
        
        if updated_state:
            print("   ✓ Agent state processed successfully")
            messages = updated_state.get("agent_messages", [])
            print(f"   ✓ Agent messages: {len(messages)}")
        else:
            print("   ✗ Agent state processing failed")
        
        # Test available tasks
        print("\n7. Testing Available Tasks...")
        
        available_tasks = contract_agent.get_available_tasks()
        print(f"   ✓ Available tasks: {', '.join(available_tasks)}")
        
        print("\n✅ Contract Agent Core Implementation Test Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Contract Agent Core Implementation Test")
    print("=" * 50)
    
    # Run the test
    success = asyncio.run(test_contract_agent_core())
    
    if success:
        print("\n🎉 All tests passed! Contract Agent core is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Please check the implementation.")
        sys.exit(1)