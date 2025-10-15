#!/usr/bin/env python3
"""
Optimized Workflow Usage Example
Demonstrates how to use the new single-call optimized workflow
"""
import asyncio
import logging
from src.workflows.optimized_workflow import OptimizedHomeAISystem
from src.utils.config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Main example function"""
    
    print("\n" + "="*60)
    print("  Optimized Workflow Usage Example")
    print("  Single LLM Call for Intent + Response")
    print("="*60 + "\n")
    
    # 1. Initialize the optimized system
    print("1️⃣ Initializing optimized system...")
    config = Config()
    system = OptimizedHomeAISystem(config)
    print("   ✅ System initialized\n")
    
    # 2. Create a test user with specific familiarity
    print("2️⃣ Setting up test user...")
    user_id = "demo_user"
    system.db_service.get_or_create_user(user_id, username="Demo User")
    system.db_service.update_user_familiarity(user_id, 60)  # Medium-high familiarity
    print(f"   ✅ User created with familiarity: 60/100\n")
    
    # 3. Test different types of inputs
    test_inputs = [
        "你好",
        "开灯",
        "把客厅的灯调亮一点",
        "现在温度是多少度？",
        "关掉空调"
    ]
    
    print("3️⃣ Testing various inputs:\n")
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"   Test {i}: \"{user_input}\"")
        
        try:
            # Process user input (single API call!)
            response = await system.process_user_input(
                user_input=user_input,
                user_id=user_id
            )
            
            print(f"   Response: {response}")
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
        
        # Small delay between requests
        await asyncio.sleep(1)
    
    # 4. Demonstrate familiarity impact
    print("4️⃣ Demonstrating familiarity impact:\n")
    
    familiarity_levels = [20, 50, 80]
    test_command = "帮我开灯"
    
    for familiarity in familiarity_levels:
        print(f"   Familiarity: {familiarity}/100")
        
        # Update user familiarity
        system.db_service.update_user_familiarity(user_id, familiarity)
        
        try:
            response = await system.process_user_input(
                user_input=test_command,
                user_id=user_id
            )
            
            print(f"   Input: \"{test_command}\"")
            print(f"   Response: {response}")
            
            # Analyze response
            if any(word in response for word in ["不", "拒绝", "不能", "不行"]):
                print(f"   📊 Status: REJECTED ❌")
            else:
                print(f"   📊 Status: ACCEPTED ✅")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
        
        await asyncio.sleep(1)
    
    print("="*60)
    print("  Example Complete!")
    print("="*60 + "\n")
    
    print("📝 Key Takeaways:")
    print("   • Single LLM call for intent + response")
    print("   • Familiarity score explicitly used in prompt")
    print("   • ~50% faster than traditional 2-call workflow")
    print("   • Device control depends on familiarity level")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Example interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Example error: {e}")
        import traceback
        traceback.print_exc()

