"""
Contract Agent Tools Demo
Demonstrates the functionality of contract generation, e-signatures, document management, 
legal compliance checking, and transaction tracking tools.
"""

import asyncio
import json
from datetime import datetime, timedelta
from app.agents.contract_tools import (
    ContractGenerationTool,
    ElectronicSignatureTool,
    DocumentManagementTool,
    LegalComplianceTool,
    TransactionTrackingTool,
    ContractType,
    DocumentFormat,
    get_contract_tools
)


async def demo_contract_generation():
    """Demonstrate contract generation functionality"""
    print("\n" + "="*60)
    print("CONTRACT GENERATION DEMO")
    print("="*60)
    
    tool = ContractGenerationTool()
    
    # Sample deal data
    deal_data = {
        "property": {
            "address": "123 Investment Lane",
            "city": "Real Estate City",
            "state": "CA",
            "zip_code": "90210",
            "property_type": "Single Family Residence",
            "square_feet": 2500,
            "lot_size": 0.33,
            "year_built": 1995
        }
    }
    
    # Sample parties
    parties = [
        {
            "role": "Buyer",
            "name": "John Investor",
            "address": "456 Capital Ave, Investment City, CA 90211",
            "phone": "(555) 123-4567",
            "email": "john@investor.com"
        },
        {
            "role": "Seller",
            "name": "Sarah Homeowner",
            "address": "123 Investment Lane, Real Estate City, CA 90210",
            "phone": "(555) 987-6543",
            "email": "sarah@homeowner.com"
        }
    ]
    
    # Sample terms
    terms = {
        "purchase_price": 750000,
        "earnest_money": 15000,
        "down_payment": 150000,
        "financing_amount": 600000,
        "closing_date": "2024-03-15",
        "possession_date": "2024-03-15",
        "contingencies": [
            "Inspection contingency (14 days)",
            "Financing contingency (30 days)",
            "Appraisal contingency",
            "Title contingency"
        ],
        "inclusions": [
            "All built-in appliances",
            "Window treatments and blinds",
            "Garage door opener and remotes",
            "Irrigation system"
        ],
        "additional_terms": [
            "Property sold in as-is condition",
            "Seller to provide home warranty",
            "Buyer to assume existing HOA obligations"
        ]
    }
    
    # Generate purchase agreement
    print("Generating Purchase Agreement...")
    result = await tool.execute(
        contract_type=ContractType.PURCHASE_AGREEMENT,
        deal_data=deal_data,
        parties=parties,
        terms=terms,
        output_format=DocumentFormat.HTML
    )
    
    if result["success"]:
        print(f"✅ Contract generated successfully!")
        print(f"   Contract ID: {result['contract_id']}")
        print(f"   Document Path: {result['document_path']}")
        print(f"   Content Length: {len(result['result'].document_content)} characters")
        print(f"   Template Used: {result['result'].template_used}")
    else:
        print(f"❌ Contract generation failed: {result['error']}")
    
    # Generate assignment contract
    print("\nGenerating Assignment Contract...")
    assignment_terms = {
        "original_contract_date": "2024-02-01",
        "original_purchase_price": 750000,
        "assignment_fee": 25000,
        "assignment_date": "2024-02-15",
        "closing_date": "2024-03-15",
        "additional_terms": [
            "Assignee assumes all buyer obligations",
            "Assignment fee due upon execution",
            "Original contract remains in full force"
        ]
    }
    
    assignment_parties = [
        {
            "role": "Assignor",
            "name": "John Investor",
            "address": "456 Capital Ave, Investment City, CA 90211"
        },
        {
            "role": "Assignee", 
            "name": "Investment Partners LLC",
            "address": "789 Business Blvd, Investment City, CA 90211"
        }
    ]
    
    result = await tool.execute(
        contract_type=ContractType.ASSIGNMENT_CONTRACT,
        deal_data=deal_data,
        parties=assignment_parties,
        terms=assignment_terms
    )
    
    if result["success"]:
        print(f"✅ Assignment contract generated successfully!")
        print(f"   Contract ID: {result['contract_id']}")
        return result['contract_id'], result['result'].document_content
    else:
        print(f"❌ Assignment contract generation failed: {result['error']}")
        return None, None


async def demo_electronic_signatures(contract_id, document_content):
    """Demonstrate electronic signature functionality"""
    print("\n" + "="*60)
    print("ELECTRONIC SIGNATURE DEMO")
    print("="*60)
    
    tool = ElectronicSignatureTool()
    
    # Sample signers
    signers = [
        {
            "name": "John Investor",
            "email": "john@investor.com",
            "role": "Assignor"
        },
        {
            "name": "Investment Partners LLC",
            "email": "legal@investmentpartners.com",
            "role": "Assignee"
        }
    ]
    
    # Send for signature
    print("Sending document for electronic signature...")
    result = await tool.execute(
        action="send_for_signature",
        document_path=f"contracts/{contract_id}.html",
        signers=signers,
        subject="Assignment Contract for Electronic Signature",
        message="Please review and electronically sign this assignment contract."
    )
    
    if result["success"]:
        print(f"✅ Document sent for signature successfully!")
        print(f"   Signature Request ID: {result['signature_request_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Number of Signers: {len(result['signing_urls'])}")
        
        for i, signer_info in enumerate(result['signing_urls']):
            print(f"   Signer {i+1}: {signer_info['signer']['name']} - {signer_info['signing_url']}")
        
        signature_request_id = result['signature_request_id']
    else:
        print(f"❌ Failed to send for signature: {result['error']}")
        return
    
    # Check signature status
    print("\nChecking signature status...")
    result = await tool.execute(
        action="check_status",
        signature_request_id=signature_request_id
    )
    
    if result["success"]:
        print(f"✅ Signature status retrieved!")
        print(f"   Status: {result['status']}")
        print(f"   Last Updated: {result['last_updated']}")
    else:
        print(f"❌ Failed to check status: {result['error']}")
    
    # Download signed document (simulate completed signature)
    print("\nDownloading signed document...")
    result = await tool.execute(
        action="download_signed",
        signature_request_id=signature_request_id
    )
    
    if result["success"]:
        print(f"✅ Signed document download link generated!")
        print(f"   Download URL: {result['download_url']}")
        print(f"   Document Path: {result['document_path']}")
    else:
        print(f"❌ Failed to download signed document: {result['error']}")


async def demo_document_management(contract_id, document_content):
    """Demonstrate document management functionality"""
    print("\n" + "="*60)
    print("DOCUMENT MANAGEMENT DEMO")
    print("="*60)
    
    tool = DocumentManagementTool()
    
    # Store document
    print("Storing contract document...")
    result = await tool.execute(
        action="store",
        document_content=document_content,
        metadata={
            "contract_type": "assignment_contract",
            "deal_id": "DEAL_2024_001",
            "parties": ["John Investor", "Investment Partners LLC"],
            "contract_value": 25000,
            "created_by": "contract_agent",
            "tags": ["assignment", "real_estate", "investment"]
        }
    )
    
    if result["success"]:
        print(f"✅ Document stored successfully!")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Stored Path: {result['stored_path']}")
        print(f"   Hash: {result['metadata']['hash'][:16]}...")
        
        document_id = result['document_id']
    else:
        print(f"❌ Failed to store document: {result['error']}")
        return
    
    # Retrieve document
    print("\nRetrieving stored document...")
    result = await tool.execute(
        action="retrieve",
        document_id=document_id
    )
    
    if result["success"]:
        print(f"✅ Document retrieved successfully!")
        print(f"   Document Path: {result['document_path']}")
        print(f"   Download URL: {result['download_url']}")
    else:
        print(f"❌ Failed to retrieve document: {result['error']}")
    
    # List documents
    print("\nListing documents...")
    result = await tool.execute(
        action="list",
        deal_id="DEAL_2024_001",
        limit=10
    )
    
    if result["success"]:
        print(f"✅ Document list retrieved!")
        print(f"   Total Documents: {result['total_count']}")
        for doc in result['documents'][:3]:  # Show first 3
            print(f"   - {doc['document_id']}: {doc['document_type']} ({doc['status']})")
    else:
        print(f"❌ Failed to list documents: {result['error']}")
    
    # Search documents
    print("\nSearching documents...")
    result = await tool.execute(
        action="search",
        query="assignment contract",
        filters={"document_type": "assignment_contract"}
    )
    
    if result["success"]:
        print(f"✅ Document search completed!")
        print(f"   Query: '{result['query']}'")
        print(f"   Total Matches: {result['total_matches']}")
        for match in result['results']:
            print(f"   - {match['title']} (Score: {match['relevance_score']:.2f})")
    else:
        print(f"❌ Failed to search documents: {result['error']}")


async def demo_legal_compliance(document_content):
    """Demonstrate legal compliance checking"""
    print("\n" + "="*60)
    print("LEGAL COMPLIANCE DEMO")
    print("="*60)
    
    tool = LegalComplianceTool()
    
    # Check compliance for assignment contract
    print("Checking legal compliance...")
    result = await tool.execute(
        document_content=document_content,
        contract_type=ContractType.ASSIGNMENT_CONTRACT,
        jurisdiction="CA"
    )
    
    if result["success"]:
        compliance_result = result["result"]
        print(f"✅ Compliance check completed!")
        print(f"   Overall Compliant: {'✅ YES' if result['compliant'] else '❌ NO'}")
        print(f"   Jurisdiction: {compliance_result.jurisdiction}")
        print(f"   Issues Found: {len(compliance_result.issues)}")
        print(f"   Warnings: {len(compliance_result.warnings)}")
        print(f"   Recommendations: {len(compliance_result.recommendations)}")
        
        if compliance_result.issues:
            print("\n   🚨 ISSUES:")
            for issue in compliance_result.issues:
                print(f"      - {issue}")
        
        if compliance_result.warnings:
            print("\n   ⚠️  WARNINGS:")
            for warning in compliance_result.warnings:
                print(f"      - {warning}")
        
        if compliance_result.recommendations:
            print("\n   💡 RECOMMENDATIONS:")
            for rec in compliance_result.recommendations:
                print(f"      - {rec}")
    else:
        print(f"❌ Compliance check failed: {result['error']}")
    
    # Test with problematic contract (missing signature)
    print("\nTesting with problematic contract...")
    problematic_contract = """
    <html><body>
    <h1>ASSIGNMENT CONTRACT</h1>
    <p>Assignment Fee: $25,000</p>
    <p>This is a very short contract without proper signature section.</p>
    </body></html>
    """
    
    result = await tool.execute(
        document_content=problematic_contract,
        contract_type=ContractType.ASSIGNMENT_CONTRACT,
        jurisdiction="CA"
    )
    
    if result["success"]:
        print(f"   Compliant: {'✅ YES' if result['compliant'] else '❌ NO'}")
        print(f"   Issues: {result['issues_count']}")
        print(f"   Summary: {result['summary']}")
    else:
        print(f"❌ Compliance check failed: {result['error']}")


async def demo_transaction_tracking():
    """Demonstrate transaction tracking functionality"""
    print("\n" + "="*60)
    print("TRANSACTION TRACKING DEMO")
    print("="*60)
    
    tool = TransactionTrackingTool()
    
    transaction_id = "TXN_2024_DEMO_001"
    
    # Get transaction status
    print("Getting transaction status...")
    result = await tool.execute(
        action="get_status",
        transaction_id=transaction_id
    )
    
    if result["success"]:
        tracking_result = result["result"]
        print(f"✅ Transaction status retrieved!")
        print(f"   Transaction ID: {tracking_result.transaction_id}")
        print(f"   Current Status: {result['current_status']}")
        print(f"   Progress: {result['progress_percentage']:.1f}%")
        print(f"   Completed Items: {len(tracking_result.completed_items)}")
        print(f"   Pending Items: {len(tracking_result.pending_items)}")
        
        print("\n   📋 MILESTONES:")
        for milestone in tracking_result.milestones[:5]:  # Show first 5
            status_icon = "✅" if milestone["status"] == "completed" else "🔄" if milestone["status"] == "in_progress" else "⏳"
            print(f"      {status_icon} {milestone['milestone']} ({milestone['status']})")
        
        print("\n   🎯 NEXT ACTIONS:")
        for action in tracking_result.next_actions:
            print(f"      - {action}")
    else:
        print(f"❌ Failed to get transaction status: {result['error']}")
    
    # Update milestone
    print("\nUpdating milestone...")
    result = await tool.execute(
        action="update_milestone",
        transaction_id=transaction_id,
        milestone="Inspection Period",
        status="completed",
        notes="Property inspection completed successfully. No major issues found."
    )
    
    if result["success"]:
        print(f"✅ Milestone updated successfully!")
        print(f"   Milestone: {result['milestone']}")
        print(f"   New Status: {result['new_status']}")
        print(f"   Notes: {result['notes']}")
    else:
        print(f"❌ Failed to update milestone: {result['error']}")
    
    # Get timeline
    print("\nGetting transaction timeline...")
    result = await tool.execute(
        action="get_timeline",
        transaction_id=transaction_id
    )
    
    if result["success"]:
        print(f"✅ Timeline retrieved!")
        print(f"   Contract Date: {result['contract_date']}")
        print(f"   Estimated Closing: {result['estimated_closing']}")
        
        print("\n   📅 TIMELINE:")
        for event in result['timeline']:
            status_icon = "✅" if event["status"] == "completed" else "📅"
            event_date = datetime.fromisoformat(event["date"]).strftime("%m/%d/%Y")
            print(f"      {status_icon} {event_date}: {event['event']}")
    else:
        print(f"❌ Failed to get timeline: {result['error']}")


async def demo_tools_registry():
    """Demonstrate tools registry functionality"""
    print("\n" + "="*60)
    print("TOOLS REGISTRY DEMO")
    print("="*60)
    
    # Get all contract tools
    tools = get_contract_tools()
    print(f"Available Contract Tools: {len(tools)}")
    
    for tool_name, tool in tools.items():
        print(f"\n🔧 {tool_name.upper()}")
        print(f"   Description: {tool.metadata.description}")
        print(f"   Category: {tool.metadata.category}")
        print(f"   Access Level: {tool.metadata.access_level}")
        print(f"   Timeout: {tool.metadata.timeout_seconds}s")
        print(f"   Usage Count: {tool.usage_count}")


async def main():
    """Run all contract tools demos"""
    print("🏠 REAL ESTATE CONTRACT AGENT TOOLS DEMO")
    print("Demonstrating comprehensive contract management capabilities")
    
    try:
        # Generate contracts
        contract_id, document_content = await demo_contract_generation()
        
        if contract_id and document_content:
            # Electronic signatures
            await demo_electronic_signatures(contract_id, document_content)
            
            # Document management
            await demo_document_management(contract_id, document_content)
            
            # Legal compliance
            await demo_legal_compliance(document_content)
        
        # Transaction tracking
        await demo_transaction_tracking()
        
        # Tools registry
        await demo_tools_registry()
        
        print("\n" + "="*60)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("Contract Agent Tools are ready for production use.")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())