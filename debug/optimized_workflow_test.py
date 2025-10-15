#!/usr/bin/env python3
"""
Optimized Workflow Test
Tests the new single-call unified responder workflow
Compare performance with traditional 2-call workflow
"""
import sys
import os
import asyncio
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable OpenTelemetry for tests
os.environ['OTEL_TRACES_EXPORTER'] = 'none'
os.environ['OTEL_METRICS_EXPORTER'] = 'none'
os.environ['OTEL_LOGS_EXPORTER'] = 'none'

from src.workflows.optimized_workflow import OptimizedHomeAISystem
from src.workflows.traditional_workflow import HomeAISystem
from src.utils.config import Config


def print_separator(title=""):
    """Print a nice separator"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    else:
        print(f"{'='*60}\n")


async def test_optimized_workflow():
    """Test the optimized single-call workflow"""
    
    print_separator("🚀 Optimized Workflow Test (Single API Call)")
    
    # Load config
    config = Config()
    
    # Create optimized system
    system = OptimizedHomeAISystem(config)
    
    # Test user
    user_id = "test_user_optimized"
    
    # Test cases with different familiarity scores
    test_cases = [
        {
            "name": "Low Familiarity - Device Control Request (Should Reject)",
            "familiarity": 20,
            "input": "帮我开灯"
        },
        {
            "name": "Medium Familiarity - Simple Device Control",
            "familiarity": 50,
            "input": "开灯"
        },
        {
            "name": "High Familiarity - Complex Device Control",
            "familiarity": 80,
            "input": "把客厅的灯调亮一点，然后打开空调"
        },
        {
            "name": "Casual Conversation",
            "familiarity": 60,
            "input": "你好吗？"
        },
        {
            "name": "Context Reference",
            "familiarity": 70,
            "input": "把它关掉"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"📝 Test Case {i}: {test_case['name']}")
        print(f"   Familiarity: {test_case['familiarity']}/100")
        print(f"   Input: \"{test_case['input']}\"")
        
        # Set user familiarity
        system.db_service.get_or_create_user(user_id)
        system.db_service.update_user_familiarity(user_id, test_case['familiarity'])
        
        # Measure time
        start_time = time.time()
        
        try:
            response = await system.process_user_input(
                user_input=test_case['input'],
                user_id=user_id
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            print(f"   ✅ Response ({elapsed_ms:.0f}ms): {response}")
            
            results.append({
                "test": test_case['name'],
                "success": True,
                "time_ms": elapsed_ms,
                "response_length": len(response)
            })
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            print(f"   ❌ Error ({elapsed_ms:.0f}ms): {e}")
            
            results.append({
                "test": test_case['name'],
                "success": False,
                "time_ms": elapsed_ms,
                "error": str(e)
            })
        
        print()
        await asyncio.sleep(1)  # Rate limiting
    
    # Print summary
    print_separator("📊 Test Results Summary")
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    avg_time = sum(r["time_ms"] for r in results if r["success"]) / successful_tests if successful_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Average Response Time: {avg_time:.0f}ms")
    print()
    
    return results


async def test_traditional_workflow():
    """Test the traditional 2-call workflow for comparison"""
    
    print_separator("🐢 Traditional Workflow Test (2 API Calls)")
    
    # Load config
    config = Config()
    
    # Create traditional system
    system = HomeAISystem(config)
    
    # Test user
    user_id = "test_user_traditional"
    
    # Same test cases
    test_cases = [
        {
            "name": "Low Familiarity - Device Control Request",
            "familiarity": 20,
            "input": "帮我开灯"
        },
        {
            "name": "Medium Familiarity - Simple Device Control",
            "familiarity": 50,
            "input": "开灯"
        },
        {
            "name": "High Familiarity - Complex Device Control",
            "familiarity": 80,
            "input": "把客厅的灯调亮一点，然后打开空调"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"📝 Test Case {i}: {test_case['name']}")
        print(f"   Familiarity: {test_case['familiarity']}/100")
        print(f"   Input: \"{test_case['input']}\"")
        
        # Set user familiarity
        system.db_service.get_or_create_user(user_id)
        system.db_service.update_user_familiarity(user_id, test_case['familiarity'])
        
        # Measure time
        start_time = time.time()
        
        try:
            response = await system.process_user_input(
                user_input=test_case['input'],
                user_id=user_id
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            print(f"   ✅ Response ({elapsed_ms:.0f}ms): {response}")
            
            results.append({
                "test": test_case['name'],
                "success": True,
                "time_ms": elapsed_ms,
                "response_length": len(response)
            })
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            print(f"   ❌ Error ({elapsed_ms:.0f}ms): {e}")
            
            results.append({
                "test": test_case['name'],
                "success": False,
                "time_ms": elapsed_ms,
                "error": str(e)
            })
        
        print()
        await asyncio.sleep(1)  # Rate limiting
    
    # Print summary
    print_separator("📊 Test Results Summary")
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    avg_time = sum(r["time_ms"] for r in results if r["success"]) / successful_tests if successful_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Average Response Time: {avg_time:.0f}ms")
    print()
    
    return results


async def compare_workflows():
    """Compare optimized vs traditional workflow"""
    
    print_separator("⚡ Workflow Performance Comparison")
    
    print("Running Optimized Workflow Tests...")
    optimized_results = await test_optimized_workflow()
    
    await asyncio.sleep(2)
    
    print("Running Traditional Workflow Tests...")
    traditional_results = await test_traditional_workflow()
    
    # Compare results
    print_separator("📈 Performance Comparison")
    
    opt_avg = sum(r["time_ms"] for r in optimized_results if r["success"]) / len([r for r in optimized_results if r["success"]])
    trad_avg = sum(r["time_ms"] for r in traditional_results if r["success"]) / len([r for r in traditional_results if r["success"]])
    
    improvement = ((trad_avg - opt_avg) / trad_avg) * 100
    
    print(f"Optimized Workflow Average: {opt_avg:.0f}ms")
    print(f"Traditional Workflow Average: {trad_avg:.0f}ms")
    print(f"Performance Improvement: {improvement:.1f}%")
    print(f"Time Saved: {trad_avg - opt_avg:.0f}ms per request")
    print()


async def test_familiarity_awareness():
    """Test that familiarity score is properly used"""
    
    print_separator("🔍 Familiarity Score Awareness Test")
    
    config = Config()
    system = OptimizedHomeAISystem(config)
    
    user_id = "familiarity_test_user"
    
    # Test at different familiarity levels
    familiarity_levels = [10, 30, 50, 70, 90]
    
    print("Testing device control request at different familiarity levels:")
    print()
    
    for familiarity in familiarity_levels:
        # Set familiarity
        system.db_service.get_or_create_user(user_id)
        system.db_service.update_user_familiarity(user_id, familiarity)
        
        # Request device control
        user_input = "开灯"
        
        print(f"📊 Familiarity: {familiarity}/100")
        print(f"   Request: \"{user_input}\"")
        
        try:
            response = await system.process_user_input(
                user_input=user_input,
                user_id=user_id
            )
            
            print(f"   Response: {response}")
            
            # Analyze response
            if any(word in response for word in ["不", "拒绝", "不能", "不行"]):
                print(f"   ❌ Request REJECTED (as expected for low familiarity)")
            elif any(word in response for word in ["好", "明白", "完成", "可以"]):
                print(f"   ✅ Request ACCEPTED (as expected for high familiarity)")
            else:
                print(f"   ⚠️ Unclear response")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        await asyncio.sleep(1)


async def main():
    """Main test runner"""
    
    print("\n" + "="*60)
    print("  Optimized Workflow Test Suite")
    print("  Testing Single-Call Unified Responder")
    print("="*60 + "\n")
    
    # Run tests
    print("Select test to run:")
    print("1. Optimized Workflow Test")
    print("2. Traditional Workflow Test")
    print("3. Performance Comparison")
    print("4. Familiarity Awareness Test")
    print("5. Run All Tests")
    print()
    
    choice = input("Enter choice (1-5): ").strip()
    
    if choice == "1":
        await test_optimized_workflow()
    elif choice == "2":
        await test_traditional_workflow()
    elif choice == "3":
        await compare_workflows()
    elif choice == "4":
        await test_familiarity_awareness()
    elif choice == "5":
        await test_optimized_workflow()
        await asyncio.sleep(2)
        await test_familiarity_awareness()
        await asyncio.sleep(2)
        await compare_workflows()
    else:
        print("Invalid choice. Running all tests...")
        await test_optimized_workflow()
    
    print_separator("✅ All Tests Complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()

