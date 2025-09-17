#!/usr/bin/env python3
"""
User and Device Management CLI Tool
智能家居系统的用户和设备管理工具
"""
import asyncio
import json
from typing import Dict, List, Optional
from datetime import datetime

from config import load_config
from database_service import DatabaseService
from models import User, Device, UserMemory

class UserDeviceManager:
    """用户和设备管理类"""
    
    def __init__(self):
        self.config = load_config()
        self.db_service = DatabaseService(self.config)
        
    def create_user(self, user_id: str, username: str, email: str = None, familiarity_score: int = 25) -> User:
        """创建新用户"""
        user = self.db_service.get_or_create_user(
            user_id=user_id,
            username=username,
            email=email
        )
        
        # 设置熟悉度分数
        self.db_service.update_user_familiarity(user_id, familiarity_score)
        
        print(f"✅ 创建用户成功:")
        print(f"   用户ID: {user_id}")
        print(f"   用户名: {username}")
        print(f"   邮箱: {email or '未设置'}")
        print(f"   熟悉度: {familiarity_score}/100")
        
        return user
    
    def list_users(self):
        """列出所有用户"""
        session = self.db_service.get_session()
        try:
            users = session.query(User).filter_by(is_active=True).all()
            
            print(f"\n📋 系统用户列表 (共 {len(users)} 个):")
            print("-" * 80)
            
            for user in users:
                stats = self.db_service.get_user_statistics(user.id)
                print(f"👤 用户ID: {user.id}")
                print(f"   用户名: {user.username}")
                print(f"   熟悉度: {user.familiarity_score}/100 ({self._get_familiarity_level(user.familiarity_score)})")
                print(f"   对话数: {stats.get('conversation_count', 0)}")
                print(f"   消息数: {stats.get('message_count', 0)}")
                print(f"   记忆数: {stats.get('memory_count', 0)}")
                print(f"   创建时间: {user.created_at}")
                print(f"   最后活跃: {user.last_seen}")
                print("-" * 40)
        finally:
            session.close()
    
    def update_user_familiarity(self, user_id: str, new_score: int):
        """更新用户熟悉度"""
        if not (0 <= new_score <= 100):
            print("❌ 熟悉度分数必须在0-100之间")
            return
        
        success = self.db_service.update_user_familiarity(user_id, new_score)
        if success:
            level = self._get_familiarity_level(new_score)
            print(f"✅ 已更新用户 {user_id} 的熟悉度为 {new_score}/100 ({level})")
        else:
            print(f"❌ 用户 {user_id} 不存在")
    
    def _get_familiarity_level(self, score: int) -> str:
        """获取熟悉度等级"""
        if score <= 30:
            return "陌生人 - Formal"
        elif score <= 60:
            return "熟人 - Polite"
        elif score <= 80:
            return "朋友 - Casual"
        else:
            return "家人 - Intimate"
    
    def add_device(self, device_id: str, name: str, device_type: str, room: str = None,
                   supported_actions: List[str] = None, capabilities: Dict = None,
                   min_familiarity: int = 40):
        """添加新设备"""
        session = self.db_service.get_session()
        try:
            # 检查设备是否已存在
            existing_device = session.query(Device).filter_by(id=device_id).first()
            if existing_device:
                print(f"❌ 设备 {device_id} 已存在")
                return
            
            # 设置默认支持的操作
            if supported_actions is None:
                if device_type == "lights":
                    supported_actions = ["turn_on", "turn_off", "set_brightness"]
                elif device_type == "tv":
                    supported_actions = ["turn_on", "turn_off", "set_volume", "set_channel"]
                elif device_type == "speaker":
                    supported_actions = ["turn_on", "turn_off", "set_volume"]
                else:
                    supported_actions = ["turn_on", "turn_off"]
            
            # 设置默认能力
            if capabilities is None:
                if device_type == "lights":
                    capabilities = {"brightness": {"min": 0, "max": 100}}
                elif device_type in ["tv", "speaker"]:
                    capabilities = {"volume": {"min": 0, "max": 100}}
                else:
                    capabilities = {}
            
            # 创建设备
            device = Device(
                id=device_id,
                name=name,
                device_type=device_type,
                room=room,
                supported_actions=supported_actions,
                capabilities=capabilities,
                current_state={"status": "off"},
                min_familiarity_required=min_familiarity
            )
            
            session.add(device)
            session.commit()
            
            print(f"✅ 添加设备成功:")
            print(f"   设备ID: {device_id}")
            print(f"   设备名: {name}")
            print(f"   类型: {device_type}")
            print(f"   房间: {room or '未指定'}")
            print(f"   支持操作: {', '.join(supported_actions)}")
            print(f"   所需熟悉度: {min_familiarity}/100")
            
        except Exception as e:
            session.rollback()
            print(f"❌ 添加设备失败: {e}")
        finally:
            session.close()
    
    def list_devices(self):
        """列出所有设备"""
        devices = self.db_service.get_all_devices(active_only=True)
        
        print(f"\n🏠 智能设备列表 (共 {len(devices)} 个):")
        print("-" * 80)
        
        for device in devices:
            print(f"🔌 设备ID: {device.id}")
            print(f"   设备名: {device.name}")
            print(f"   类型: {device.device_type}")
            print(f"   房间: {device.room or '未指定'}")
            print(f"   当前状态: {json.dumps(device.current_state, ensure_ascii=False)}")
            print(f"   支持操作: {', '.join(device.supported_actions)}")
            print(f"   所需熟悉度: {device.min_familiarity_required}/100")
            print(f"   最后更新: {device.last_updated}")
            print("-" * 40)
    
    def update_device_state(self, device_id: str, new_state: Dict):
        """更新设备状态"""
        success = self.db_service.update_device_state(device_id, new_state)
        if success:
            print(f"✅ 已更新设备 {device_id} 状态: {json.dumps(new_state, ensure_ascii=False)}")
        else:
            print(f"❌ 设备 {device_id} 不存在")
    
    def delete_device(self, device_id: str):
        """删除设备"""
        session = self.db_service.get_session()
        try:
            device = session.query(Device).filter_by(id=device_id).first()
            if device:
                device.is_active = False
                session.commit()
                print(f"✅ 已删除设备 {device_id}")
            else:
                print(f"❌ 设备 {device_id} 不存在")
        finally:
            session.close()
    
    def add_user_memory(self, user_id: str, content: str, memory_type: str = "manual", 
                       keywords: List[str] = None, importance: float = 1.0):
        """为用户添加记忆"""
        try:
            memory = self.db_service.save_user_memory(
                user_id=user_id,
                content=content,
                memory_type=memory_type,
                keywords=keywords or [],
                importance_score=importance
            )
            print(f"✅ 已为用户 {user_id} 添加记忆:")
            print(f"   内容: {content}")
            print(f"   类型: {memory_type}")
            print(f"   重要性: {importance}")
        except Exception as e:
            print(f"❌ 添加记忆失败: {e}")
    
    def search_user_memories(self, user_id: str, query: str, limit: int = 10):
        """搜索用户记忆"""
        memories = self.db_service.search_user_memories(user_id, query, limit)
        
        print(f"\n🧠 用户 {user_id} 的记忆搜索结果 ('{query}'):")
        print(f"找到 {len(memories)} 条相关记忆:")
        print("-" * 60)
        
        for i, memory in enumerate(memories, 1):
            print(f"{i}. {memory.content}")
            print(f"   类型: {memory.memory_type} | 重要性: {memory.importance_score}")
            print(f"   创建时间: {memory.created_at}")
            print("-" * 30)
    
    def show_langfuse_info(self):
        """显示Langfuse观测信息"""
        print("\n📊 Langfuse观测平台信息:")
        print("=" * 50)
        
        if self.config.langfuse.enabled:
            print("✅ Langfuse已启用")
            print(f"🔗 访问地址: {self.config.langfuse.host}")
            print(f"🔑 Public Key: {self.config.langfuse.public_key[:20]}...")
            print("\n📈 在Langfuse中可以查看的数据:")
            print("  • 用户的熟悉度分数 (familiarity_score)")
            print("  • 每次对话的语调选择 (tone)")
            print("  • 设备控制操作记录")
            print("  • LLM调用的token使用量")
            print("  • 对话上下文和历史")
            print("  • 系统性能指标")
            
            print("\n🔍 查看familiarity数据的方法:")
            print("  1. 登录Langfuse控制台")
            print("  2. 进入 'Traces' 页面")
            print("  3. 选择任意对话trace")
            print("  4. 查看 Input/Output 中的 familiarity_score 字段")
            print("  5. 在 'check_familiarity' observation中可见用户熟悉度")
        else:
            print("❌ Langfuse未启用")
            print("💡 启用方法: 在.env文件中配置Langfuse密钥")

def main():
    """主菜单"""
    manager = UserDeviceManager()
    
    print("🏠 智能家居系统 - 用户设备管理工具")
    print("=" * 50)
    
    while True:
        print("\n📋 请选择操作:")
        print("1. 👤 用户管理")
        print("2. 🔌 设备管理") 
        print("3. 🧠 记忆管理")
        print("4. 📊 查看Langfuse信息")
        print("5. 🚪 退出")
        
        try:
            choice = input("\n请输入选项 (1-5): ").strip()
            
            if choice == "1":
                user_menu(manager)
            elif choice == "2":
                device_menu(manager)
            elif choice == "3":
                memory_menu(manager)
            elif choice == "4":
                manager.show_langfuse_info()
            elif choice == "5":
                print("👋 再见!")
                break
            else:
                print("❌ 无效选项，请重新选择")
                
        except KeyboardInterrupt:
            print("\n👋 再见!")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")

def user_menu(manager: UserDeviceManager):
    """用户管理菜单"""
    print("\n👤 用户管理")
    print("1. 创建用户")
    print("2. 查看所有用户") 
    print("3. 更新用户熟悉度")
    print("4. 返回主菜单")
    
    choice = input("请选择操作: ").strip()
    
    if choice == "1":
        user_id = input("输入用户ID: ").strip()
        username = input("输入用户名: ").strip()
        email = input("输入邮箱 (可选): ").strip() or None
        
        try:
            familiarity = int(input("输入熟悉度分数 (0-100, 默认25): ").strip() or "25")
        except ValueError:
            familiarity = 25
            
        manager.create_user(user_id, username, email, familiarity)
        
    elif choice == "2":
        manager.list_users()
        
    elif choice == "3":
        user_id = input("输入用户ID: ").strip()
        try:
            new_score = int(input("输入新的熟悉度分数 (0-100): ").strip())
            manager.update_user_familiarity(user_id, new_score)
        except ValueError:
            print("❌ 请输入有效的数字")

def device_menu(manager: UserDeviceManager):
    """设备管理菜单"""
    print("\n🔌 设备管理")
    print("1. 添加设备")
    print("2. 查看所有设备")
    print("3. 更新设备状态")
    print("4. 删除设备")
    print("5. 返回主菜单")
    
    choice = input("请选择操作: ").strip()
    
    if choice == "1":
        device_id = input("输入设备ID: ").strip()
        name = input("输入设备名称: ").strip()
        device_type = input("输入设备类型 (lights/tv/speaker/other): ").strip()
        room = input("输入房间名 (可选): ").strip() or None
        
        try:
            min_familiarity = int(input("输入所需最低熟悉度 (默认40): ").strip() or "40")
        except ValueError:
            min_familiarity = 40
            
        manager.add_device(device_id, name, device_type, room, min_familiarity=min_familiarity)
        
    elif choice == "2":
        manager.list_devices()
        
    elif choice == "3":
        device_id = input("输入设备ID: ").strip()
        state_str = input("输入新状态 (JSON格式, 如 {\"status\": \"on\"}): ").strip()
        
        try:
            new_state = json.loads(state_str)
            manager.update_device_state(device_id, new_state)
        except json.JSONDecodeError:
            print("❌ 无效的JSON格式")
            
    elif choice == "4":
        device_id = input("输入要删除的设备ID: ").strip()
        confirm = input(f"确认删除设备 {device_id}? (y/N): ").strip().lower()
        if confirm == 'y':
            manager.delete_device(device_id)

def memory_menu(manager: UserDeviceManager):
    """记忆管理菜单"""
    print("\n🧠 记忆管理")
    print("1. 添加用户记忆")
    print("2. 搜索用户记忆")
    print("3. 返回主菜单")
    
    choice = input("请选择操作: ").strip()
    
    if choice == "1":
        user_id = input("输入用户ID: ").strip()
        content = input("输入记忆内容: ").strip()
        memory_type = input("输入记忆类型 (preference/habit/general): ").strip() or "general"
        keywords = input("输入关键词 (用逗号分隔): ").strip()
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else []
        
        try:
            importance = float(input("输入重要性 (0.0-1.0, 默认1.0): ").strip() or "1.0")
        except ValueError:
            importance = 1.0
            
        manager.add_user_memory(user_id, content, memory_type, keyword_list, importance)
        
    elif choice == "2":
        user_id = input("输入用户ID: ").strip()
        query = input("输入搜索关键词: ").strip()
        manager.search_user_memories(user_id, query)

if __name__ == "__main__":
    main()



