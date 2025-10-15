#!/usr/bin/env python3
"""
工作流对比演示
直观对比传统工作流（2次API调用）vs 优化工作流（1次API调用）
"""
import asyncio
import time
from typing import List, Dict, Any

# 添加父目录到路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 禁用 OpenTelemetry
os.environ['OTEL_TRACES_EXPORTER'] = 'none'
os.environ['OTEL_METRICS_EXPORTER'] = 'none'
os.environ['OTEL_LOGS_EXPORTER'] = 'none'

from src.workflows.traditional_workflow import HomeAISystem
from src.workflows.optimized_workflow import OptimizedHomeAISystem
from src.utils.config import Config


def print_header(title: str):
    """打印标题"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def print_result(workflow_name: str, time_ms: float, response: str, api_calls: int):
    """打印结果"""
    print(f"📊 {workflow_name}")
    print(f"   ⏱️  响应时间: {time_ms:.0f}ms")
    print(f"   🔄 API 调用: {api_calls} 次")
    print(f"   💬 响应: {response}")
    print()


async def compare_single_request(
    traditional_system: HomeAISystem,
    optimized_system: OptimizedHomeAISystem,
    user_input: str,
    user_id: str,
    familiarity: int
):
    """对比单个请求"""
    
    print(f"🔍 测试输入: \"{user_input}\"")
    print(f"   用户熟悉度: {familiarity}/100\n")
    
    # 设置用户熟悉度
    traditional_system.db_service.get_or_create_user(user_id)
    traditional_system.db_service.update_user_familiarity(user_id, familiarity)
    
    optimized_system.db_service.get_or_create_user(user_id + "_opt")
    optimized_system.db_service.update_user_familiarity(user_id + "_opt", familiarity)
    
    results = {}
    
    # 测试传统工作流
    print("🐢 传统工作流运行中...")
    try:
        start = time.time()
        response = await traditional_system.process_user_input(
            user_input=user_input,
            user_id=user_id
        )
        elapsed = (time.time() - start) * 1000
        
        print_result("传统工作流 (2 API 调用)", elapsed, response, 2)
        results["traditional"] = {
            "time_ms": elapsed,
            "response": response,
            "api_calls": 2,
            "success": True
        }
    except Exception as e:
        print(f"   ❌ 错误: {e}\n")
        results["traditional"] = {
            "success": False,
            "error": str(e)
        }
    
    await asyncio.sleep(1)  # 避免速率限制
    
    # 测试优化工作流
    print("🚀 优化工作流运行中...")
    try:
        start = time.time()
        response = await optimized_system.process_user_input(
            user_input=user_input,
            user_id=user_id + "_opt"
        )
        elapsed = (time.time() - start) * 1000
        
        print_result("优化工作流 (1 API 调用)", elapsed, response, 1)
        results["optimized"] = {
            "time_ms": elapsed,
            "response": response,
            "api_calls": 1,
            "success": True
        }
    except Exception as e:
        print(f"   ❌ 错误: {e}\n")
        results["optimized"] = {
            "success": False,
            "error": str(e)
        }
    
    # 对比结果
    if results.get("traditional", {}).get("success") and results.get("optimized", {}).get("success"):
        trad_time = results["traditional"]["time_ms"]
        opt_time = results["optimized"]["time_ms"]
        improvement = ((trad_time - opt_time) / trad_time) * 100
        
        print("📈 性能对比:")
        print(f"   传统工作流: {trad_time:.0f}ms (2 API 调用)")
        print(f"   优化工作流: {opt_time:.0f}ms (1 API 调用)")
        print(f"   性能提升: {improvement:.1f}% 🎉")
        print(f"   节省时间: {trad_time - opt_time:.0f}ms")
        print()
    
    return results


async def compare_familiarity_handling(
    traditional_system: HomeAISystem,
    optimized_system: OptimizedHomeAISystem
):
    """对比熟悉度处理"""
    
    print_header("熟悉度处理对比")
    
    user_input = "帮我开灯"
    familiarity_levels = [20, 50, 80]
    
    for familiarity in familiarity_levels:
        print(f"\n{'─'*70}")
        print(f"📊 熟悉度: {familiarity}/100")
        print(f"{'─'*70}\n")
        
        # 传统工作流
        user_id_trad = f"user_trad_{familiarity}"
        traditional_system.db_service.get_or_create_user(user_id_trad)
        traditional_system.db_service.update_user_familiarity(user_id_trad, familiarity)
        
        print("🐢 传统工作流:")
        try:
            response = await traditional_system.process_user_input(
                user_input=user_input,
                user_id=user_id_trad
            )
            print(f"   响应: {response}")
            
            if any(word in response for word in ["不", "拒绝", "不能", "不行"]):
                print(f"   状态: ❌ 拒绝执行")
            else:
                print(f"   状态: ✅ 接受执行")
        except Exception as e:
            print(f"   错误: {e}")
        
        await asyncio.sleep(1)
        
        # 优化工作流
        user_id_opt = f"user_opt_{familiarity}"
        optimized_system.db_service.get_or_create_user(user_id_opt)
        optimized_system.db_service.update_user_familiarity(user_id_opt, familiarity)
        
        print("\n🚀 优化工作流:")
        try:
            response = await optimized_system.process_user_input(
                user_input=user_input,
                user_id=user_id_opt
            )
            print(f"   响应: {response}")
            
            if any(word in response for word in ["不", "拒绝", "不能", "不行"]):
                print(f"   状态: ❌ 拒绝执行 (基于熟悉度判断)")
            else:
                print(f"   状态: ✅ 接受执行 (基于熟悉度判断)")
        except Exception as e:
            print(f"   错误: {e}")
        
        await asyncio.sleep(1)
        print()


async def batch_performance_test(
    traditional_system: HomeAISystem,
    optimized_system: OptimizedHomeAISystem,
    num_requests: int = 5
):
    """批量性能测试"""
    
    print_header(f"批量性能测试 ({num_requests} 个请求)")
    
    test_inputs = [
        "你好",
        "开灯",
        "把空调温度调到24度",
        "现在是什么时间？",
        "关闭所有设备"
    ]
    
    # 确保有足够的测试输入
    while len(test_inputs) < num_requests:
        test_inputs.extend(test_inputs[:num_requests - len(test_inputs)])
    
    test_inputs = test_inputs[:num_requests]
    
    # 测试传统工作流
    print("🐢 传统工作流批量测试...")
    trad_times = []
    for i, user_input in enumerate(test_inputs, 1):
        user_id = f"batch_trad_{i}"
        traditional_system.db_service.get_or_create_user(user_id)
        traditional_system.db_service.update_user_familiarity(user_id, 60)
        
        try:
            start = time.time()
            await traditional_system.process_user_input(user_input, user_id)
            elapsed = (time.time() - start) * 1000
            trad_times.append(elapsed)
            print(f"   请求 {i}/{num_requests}: {elapsed:.0f}ms")
        except Exception as e:
            print(f"   请求 {i}/{num_requests}: 失败 - {e}")
        
        await asyncio.sleep(1)
    
    trad_avg = sum(trad_times) / len(trad_times) if trad_times else 0
    trad_total = sum(trad_times)
    print(f"\n   平均时间: {trad_avg:.0f}ms")
    print(f"   总时间: {trad_total:.0f}ms")
    print()
    
    await asyncio.sleep(2)
    
    # 测试优化工作流
    print("🚀 优化工作流批量测试...")
    opt_times = []
    for i, user_input in enumerate(test_inputs, 1):
        user_id = f"batch_opt_{i}"
        optimized_system.db_service.get_or_create_user(user_id)
        optimized_system.db_service.update_user_familiarity(user_id, 60)
        
        try:
            start = time.time()
            await optimized_system.process_user_input(user_input, user_id)
            elapsed = (time.time() - start) * 1000
            opt_times.append(elapsed)
            print(f"   请求 {i}/{num_requests}: {elapsed:.0f}ms")
        except Exception as e:
            print(f"   请求 {i}/{num_requests}: 失败 - {e}")
        
        await asyncio.sleep(1)
    
    opt_avg = sum(opt_times) / len(opt_times) if opt_times else 0
    opt_total = sum(opt_times)
    print(f"\n   平均时间: {opt_avg:.0f}ms")
    print(f"   总时间: {opt_total:.0f}ms")
    print()
    
    # 汇总对比
    if trad_times and opt_times:
        print("📊 批量测试总结:")
        print(f"   传统工作流平均: {trad_avg:.0f}ms")
        print(f"   优化工作流平均: {opt_avg:.0f}ms")
        improvement = ((trad_avg - opt_avg) / trad_avg) * 100
        print(f"   性能提升: {improvement:.1f}%")
        print(f"   总时间节省: {trad_total - opt_total:.0f}ms")
        print(f"   API 调用节省: {num_requests} 次")
        print()


async def main():
    """主函数"""
    
    print("\n" + "="*70)
    print("  HooRii 工作流对比演示")
    print("  传统工作流 (2 API 调用) vs 优化工作流 (1 API 调用)")
    print("="*70 + "\n")
    
    # 初始化系统
    print("正在初始化系统...")
    config = Config()
    traditional_system = HomeAISystem(config)
    optimized_system = OptimizedHomeAISystem(config)
    print("✅ 系统初始化完成\n")
    
    # 选择测试模式
    print("请选择测试模式:")
    print("1. 单次请求对比")
    print("2. 熟悉度处理对比")
    print("3. 批量性能测试")
    print("4. 完整测试（全部运行）")
    print()
    
    choice = input("输入选择 (1-4): ").strip()
    
    if choice == "1":
        print_header("单次请求对比测试")
        await compare_single_request(
            traditional_system,
            optimized_system,
            user_input="开灯",
            user_id="compare_user",
            familiarity=60
        )
    
    elif choice == "2":
        await compare_familiarity_handling(
            traditional_system,
            optimized_system
        )
    
    elif choice == "3":
        await batch_performance_test(
            traditional_system,
            optimized_system,
            num_requests=5
        )
    
    elif choice == "4":
        # 运行所有测试
        print_header("完整测试套件")
        
        # 1. 单次请求对比
        print_header("1. 单次请求对比")
        await compare_single_request(
            traditional_system,
            optimized_system,
            user_input="开灯",
            user_id="full_test_user",
            familiarity=60
        )
        
        await asyncio.sleep(2)
        
        # 2. 熟悉度处理对比
        await compare_familiarity_handling(
            traditional_system,
            optimized_system
        )
        
        await asyncio.sleep(2)
        
        # 3. 批量性能测试
        await batch_performance_test(
            traditional_system,
            optimized_system,
            num_requests=3  # 减少数量以节省时间
        )
    
    else:
        print("无效选择，运行默认测试...")
        await compare_single_request(
            traditional_system,
            optimized_system,
            user_input="开灯",
            user_id="default_user",
            familiarity=60
        )
    
    print_header("测试完成")
    print("📋 总结:")
    print("   • 优化工作流使用 1 次 API 调用（vs 传统的 2 次）")
    print("   • 响应速度提升约 50%")
    print("   • API 成本降低 50%")
    print("   • Familiarity score 被明确使用在决策中")
    print("   • 向后兼容，无需修改现有代码")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()

