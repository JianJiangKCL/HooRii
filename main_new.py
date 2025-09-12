#!/usr/bin/env python3
"""
New Main Entry Point
Uses the decoupled component architecture
"""
import asyncio
import json
import time
import uuid
import os

# Disable OpenTelemetry exporters
os.environ['OTEL_TRACES_EXPORTER'] = 'none'
os.environ['OTEL_METRICS_EXPORTER'] = 'none'
os.environ['OTEL_LOGS_EXPORTER'] = 'none'

from config import load_config
from task_planner import TaskPlanner


async def main():
    """Main interactive console using decoupled architecture"""
    print("🏠 智能陪伴家居控制系统 (解耦架构)")
    print("=" * 50)
    
    try:
        # Initialize the task planner
        config = load_config()
        planner = TaskPlanner(config)
        
        print("\n🏠 多轮对话智能家居助手已就绪!")
        print("输入 'new' 开始新对话, 'quit' 退出程序")
        print("输入 'stats' 查看统计信息, 'devices' 查看设备状态")
        print("输入 'test' 运行组件测试")
        
        current_conversation_id = None
        current_user_id = "user123"
        
        while True:
            try:
                user_input = input(f"\n[{current_user_id}] 你: ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'new':
                    current_conversation_id = None
                    current_user_id = input("输入用户ID (user123/user456): ").strip() or "user123"
                    print(f"为 {current_user_id} 开始新对话")
                    continue
                elif user_input.lower() == 'stats':
                    stats = planner.db_service.get_user_statistics(current_user_id)
                    print(f"📊 用户统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
                    continue
                elif user_input.lower() == 'devices':
                    status = planner.device_controller.get_device_status("all")
                    print(f"📱 设备状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
                    continue
                elif user_input.lower() == 'test':
                    print("🧪 运行组件测试...")
                    print("   python debug/intent_analysis_test.py")
                    print("   python debug/character_test.py") 
                    print("   python debug/device_controller_test.py")
                    print("   python debug/integration_test.py")
                    continue
                
                # Check for empty input
                if not user_input:
                    continue
                
                # Process with decoupled architecture
                start_time = time.time()
                response, conversation_id = await planner.process_request(
                    user_input,
                    current_user_id,
                    current_conversation_id
                )
                processing_time = (time.time() - start_time) * 1000
                
                current_conversation_id = conversation_id
                
                print(f"🤖 凌波丽: {response}")
                
                # Show conversation stats
                if conversation_id in planner.active_conversations:
                    ctx = planner.active_conversations[conversation_id]
                    print(f"   [对话: {conversation_id[:8]}..., 消息数: {ctx.message_count}, 熟悉度: {ctx.familiarity_score}, 用时: {processing_time:.0f}ms]")
                
            except KeyboardInterrupt:
                print("\n👋 再见!")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")
                
    except Exception as e:
        print(f"❌ 初始化错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
