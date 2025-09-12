#!/usr/bin/env python3
"""
Device Controller 测试
移动自 test_device_controller.py
"""
import asyncio
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 禁用 OpenTelemetry
os.environ['OTEL_TRACES_EXPORTER'] = 'none'
os.environ['OTEL_METRICS_EXPORTER'] = 'none'
os.environ['OTEL_LOGS_EXPORTER'] = 'none'

from main import HomeAITaskPlanner

async def test_device_controller():
    """测试设备控制器架构"""
    print("🧪 测试 Device Controller 架构...")
    
    planner = HomeAITaskPlanner()
    
    # 测试用例
    test_cases = [
        {
            "device_id": "living_room_lights",
            "action": "turn_on", 
            "parameters": {"brightness": 80},
            "user_intent": "打开客厅灯并调到80%亮度"
        },
        {
            "device_id": "tv",
            "action": "turn_on",
            "parameters": {"channel": "Netflix"},
            "user_intent": "打开电视看Netflix"
        },
        {
            "device_id": "air_conditioner",
            "action": "set_temperature",
            "parameters": {"temperature": 24, "mode": "cool"},
            "user_intent": "空调调到24度制冷模式"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 测试 {i}: {test_case['user_intent']}")
        
        try:
            # Step 1: Device Controller
            controller_result = await planner.device_controller(**test_case)
            print(f"✅ Controller 输出: {controller_result}")
            
            # Step 2: Execute Command  
            if controller_result.get("validation_result", {}).get("valid", True):
                execution_result = planner.execute_device_command(controller_result)
                print(f"✅ 执行结果: {execution_result}")
            else:
                print(f"❌ 验证失败: {controller_result.get('validation_result', {}).get('error_message')}")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    print("\n✅ Device Controller架构测试完成!")

if __name__ == "__main__":
    asyncio.run(test_device_controller())
