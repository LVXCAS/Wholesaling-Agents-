#!/usr/bin/env python3
"""
Comprehensive Test Runner for Real Estate Empire
Runs all working test suites and generates a final report
"""

import subprocess
import sys
import time
from datetime import datetime

def run_test_suite(name, test_files, description):
    """Run a test suite and return results"""
    print(f"\n{'='*60}")
    print(f"🧪 Running {name}")
    print(f"📝 {description}")
    print(f"{'='*60}")
    
    cmd = [
        sys.executable, "-m", "pytest",
        *test_files,
        "-v", "--tb=short", "-q"
    ]
    
    start_time = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        end_time = time.time()
        duration = end_time - start_time
        
        # Parse results from output
        output_lines = result.stdout.split('\n')
        summary_line = [line for line in output_lines if 'passed' in line and ('failed' in line or 'error' in line or 'skipped' in line)]
        
        if summary_line:
            summary = summary_line[-1]
        else:
            # Look for just passed
            passed_lines = [line for line in output_lines if 'passed' in line]
            summary = passed_lines[-1] if passed_lines else "No summary found"
        
        print(f"✅ {name} completed in {duration:.2f}s")
        print(f"📊 Results: {summary}")
        
        return {
            'name': name,
            'success': result.returncode == 0,
            'duration': duration,
            'summary': summary,
            'output': result.stdout
        }
        
    except Exception as e:
        print(f"❌ Error running {name}: {e}")
        return {
            'name': name,
            'success': False,
            'duration': 0,
            'summary': f"Error: {e}",
            'output': ""
        }

def main():
    """Run comprehensive test suite"""
    print("🏗️  Real Estate Empire - Comprehensive Test Suite")
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Define test suites
    test_suites = [
        {
            'name': 'Core Communication Services',
            'files': [
                'tests/test_email_service.py',
                'tests/test_sms_service.py', 
                'tests/test_unified_communication_service.py'
            ],
            'description': 'Email, SMS, and unified communication services'
        },
        {
            'name': 'Investment & Analysis Services',
            'files': [
                'tests/test_investment_criteria.py',
                'tests/test_deal_alerts.py',
                'tests/test_neighborhood_analysis.py'
            ],
            'description': 'Investment criteria, deal alerts, and neighborhood analysis'
        },
        {
            'name': 'Negotiation Services Suite',
            'files': [
                'tests/test_negotiation_coaching_service.py',
                'tests/test_offer_generation_service.py',
                'tests/test_negotiation_strategy_service.py',
                'tests/test_counter_offer_analyzer_service.py'
            ],
            'description': 'Complete negotiation workflow and coaching services'
        },
        {
            'name': 'Lead Management Services',
            'files': [
                'tests/test_lead_enrichment_service.py',
                'tests/test_lead_import_service.py',
                'tests/test_lead_nurturing_service.py',
                'tests/test_followup_management_service.py'
            ],
            'description': 'Lead enrichment, import, nurturing, and follow-up management'
        },
        {
            'name': 'Campaign & Messaging Services',
            'files': [
                'tests/test_outreach_campaign_service.py',
                'tests/test_conversation_management_service.py',
                'tests/test_response_analysis_service.py',
                'tests/test_message_generation_service.py'
            ],
            'description': 'Outreach campaigns, conversation management, and AI messaging'
        },
        {
            'name': 'Integration Services',
            'files': [
                'tests/test_mls_integration.py',
                'tests/test_public_records_integration.py',
                'tests/test_foreclosure_integration.py',
                'tests/test_off_market_finder.py'
            ],
            'description': 'External API integrations and off-market property discovery'
        }
    ]
    
    # Run all test suites
    results = []
    total_start_time = time.time()
    
    for suite in test_suites:
        result = run_test_suite(
            suite['name'],
            suite['files'],
            suite['description']
        )
        results.append(result)
    
    total_duration = time.time() - total_start_time
    
    # Generate final report
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
    print("="*80)
    
    successful_suites = sum(1 for r in results if r['success'])
    total_suites = len(results)
    
    print(f"🎯 Overall Success Rate: {successful_suites}/{total_suites} ({successful_suites/total_suites*100:.1f}%)")
    print(f"⏱️  Total Execution Time: {total_duration:.2f} seconds")
    print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n📋 Suite-by-Suite Results:")
    print("-" * 80)
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} | {result['name']:<35} | {result['duration']:.2f}s | {result['summary']}")
    
    print("\n🏆 PRODUCTION READINESS ASSESSMENT:")
    if successful_suites >= total_suites * 0.95:  # 95% success rate
        print("✅ PRODUCTION READY - Excellent test coverage and reliability")
        print("🚀 System is ready for deployment with high confidence")
    elif successful_suites >= total_suites * 0.90:  # 90% success rate
        print("⚠️  MOSTLY READY - Good test coverage with minor issues")
        print("🔧 Address remaining test failures before production deployment")
    else:
        print("❌ NOT READY - Significant test failures need attention")
        print("🛠️  Fix critical issues before considering production deployment")
    
    print("\n" + "="*80)
    print("🎉 Real Estate Empire Test Suite Complete!")
    print("="*80)
    
    return successful_suites == total_suites

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)