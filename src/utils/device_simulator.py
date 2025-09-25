#!/usr/bin/env python3
"""
Device Simulator - 模拟设备状态变化
可以手动控制设备状态，用于测试智能家居系统
"""
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime

from .config import load_config
from ..services.database_service import DatabaseService
from ..models.database import Device


class DeviceSimulator:
    """设备状态模拟器"""
    
    def __init__(self):
        self.config = load_config()
        self.db_service = DatabaseService(self.config)
        print("🔧 设备模拟器已初始化")
    
    def list_devices(self, active_only: bool = True) -> None:
        """列出所有设备及其状态"""
        devices = self.db_service.get_all_devices(active_only=active_only)
        
        if not devices:
            print("❌ 没有找到设备")
            return
        
        print("\n📱 设备列表:")
        print("-" * 80)
        
        for device in devices:
            status_emoji = "🟢" if device.current_state.get("status") == "on" else "🔴"
            print(f"\n{status_emoji} {device.name} ({device.id})")
            print(f"   类型: {device.device_type}")
            print(f"   房间: {device.room}")
            print(f"   是否激活: {'✅' if device.is_active else '❌'}")
            print(f"   当前状态: {json.dumps(device.current_state, ensure_ascii=False, indent=2)}")
    
    def update_device_state(self, device_id: str, new_state: Dict[str, Any]) -> bool:
        """更新设备状态"""
        device = self.db_service.get_device(device_id)
        if not device:
            print(f"❌ 设备 '{device_id}' 不存在")
            return False
        
        try:
            # 合并新状态到现有状态
            current_state = device.current_state.copy()
            current_state.update(new_state)
            
            # 更新数据库
            self.db_service.update_device_state(device_id, current_state)
            
            print(f"✅ 已更新 {device.name} 的状态:")
            print(f"   新状态: {json.dumps(current_state, ensure_ascii=False, indent=2)}")
            return True
            
        except Exception as e:
            print(f"❌ 更新失败: {e}")
            return False
    
    def toggle_device(self, device_id: str) -> bool:
        """切换设备开关状态"""
        device = self.db_service.get_device(device_id)
        if not device:
            print(f"❌ 设备 '{device_id}' 不存在")
            return False
        
        current_status = device.current_state.get("status", "off")
        new_status = "off" if current_status == "on" else "on"
        
        return self.update_device_state(device_id, {"status": new_status})
    
    def set_device_value(self, device_id: str, param_name: str, value: Any) -> bool:
        """设置设备参数值"""
        return self.update_device_state(device_id, {param_name: value})
    
    def simulate_all_online(self) -> None:
        """将所有设备设置为在线状态"""
        devices = self.db_service.get_all_devices(active_only=False)
        
        for device in devices:
            self.update_device_state(device.id, {"online": True, "status": "on"})
        
        print(f"✅ 已将 {len(devices)} 个设备设置为在线状态")
    
    def simulate_all_offline(self) -> None:
        """将所有设备设置为离线状态"""
        devices = self.db_service.get_all_devices(active_only=True)
        
        for device in devices:
            self.update_device_state(device.id, {"online": False, "status": "off"})
        
        print(f"✅ 已将 {len(devices)} 个设备设置为离线状态")
    
    def reset_all_devices(self) -> None:
        """重置所有设备到默认状态"""
        devices = self.db_service.get_all_devices(active_only=False)
        
        default_states = {
            "light": {"status": "off", "brightness": 50, "online": True},
            "tv": {"status": "off", "volume": 30, "channel": 1, "online": True},
            "air_conditioner": {"status": "off", "temperature": 24, "mode": "cool", "online": True},
            "speaker": {"status": "off", "volume": 50, "playing": "", "online": True},
            "curtain": {"status": "closed", "position": 0, "online": True}
        }
        
        for device in devices:
            default_state = default_states.get(device.device_type, {"status": "off", "online": True})
            self.db_service.update_device_state(device.id, default_state)
        
        print(f"✅ 已重置 {len(devices)} 个设备到默认状态")
    
    def interactive_mode(self) -> None:
        """交互式设备控制模式"""
        print("\n🎮 进入设备模拟交互模式")
        print("输入 'help' 查看可用命令, 'quit' 退出")
        
        while True:
            try:
                command = input("\n设备模拟器> ").strip().lower()
                
                if command == "quit":
                    break
                    
                elif command == "help":
                    print("""
可用命令:
  list              - 列出所有设备
  toggle <设备ID>   - 切换设备开关
  set <设备ID> <参数> <值> - 设置设备参数
  online-all        - 所有设备上线
  offline-all       - 所有设备下线
  reset             - 重置所有设备
  quit              - 退出
                    """)
                    
                elif command == "list":
                    self.list_devices()
                    
                elif command.startswith("toggle "):
                    device_id = command.split()[1]
                    self.toggle_device(device_id)
                    
                elif command.startswith("set "):
                    parts = command.split(maxsplit=3)
                    if len(parts) >= 4:
                        device_id, param, value = parts[1], parts[2], parts[3]
                        # 尝试转换数值
                        try:
                            value = int(value)
                        except ValueError:
                            try:
                                value = float(value)
                            except ValueError:
                                pass  # 保持字符串
                        self.set_device_value(device_id, param, value)
                    else:
                        print("❌ 用法: set <设备ID> <参数> <值>")
                        
                elif command == "online-all":
                    self.simulate_all_online()
                    
                elif command == "offline-all":
                    self.simulate_all_offline()
                    
                elif command == "reset":
                    self.reset_all_devices()
                    
                else:
                    print("❌ 未知命令，输入 'help' 查看帮助")
                    
            except KeyboardInterrupt:
                print("\n👋 退出设备模拟器")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="智能家居设备模拟器")
    parser.add_argument("--list", action="store_true", help="列出所有设备")
    parser.add_argument("--toggle", metavar="DEVICE_ID", help="切换设备开关")
    parser.add_argument("--set", nargs=3, metavar=("DEVICE_ID", "PARAM", "VALUE"), help="设置设备参数")
    parser.add_argument("--online-all", action="store_true", help="所有设备上线")
    parser.add_argument("--offline-all", action="store_true", help="所有设备下线")
    parser.add_argument("--reset", action="store_true", help="重置所有设备")
    parser.add_argument("-i", "--interactive", action="store_true", help="交互模式")
    
    args = parser.parse_args()
    
    simulator = DeviceSimulator()
    
    if args.list:
        simulator.list_devices()
    elif args.toggle:
        simulator.toggle_device(args.toggle)
    elif args.set:
        device_id, param, value = args.set
        # 尝试转换数值
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                pass  # 保持字符串
        simulator.set_device_value(device_id, param, value)
    elif args.online_all:
        simulator.simulate_all_online()
    elif args.offline_all:
        simulator.simulate_all_offline()
    elif args.reset:
        simulator.reset_all_devices()
    elif args.interactive or len(sys.argv) == 1:
        simulator.interactive_mode()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
