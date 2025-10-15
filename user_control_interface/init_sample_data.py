#!/usr/bin/env python3
"""
初始化示例数据
用于快速体验管理面板功能
"""

import sys
import os

# Add project root directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.utils.config import load_config
from src.services.database_service import DatabaseService
from src.models.database import User, Device, UserDevice

def init_sample_data():
    """初始化示例数据"""
    print("🚀 初始化示例数据...")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    db_service = DatabaseService(config)
    
    # 创建数据库表
    print("\n📦 创建数据库表...")
    db_service.db_manager.create_tables()
    print("✅ 数据库表创建完成")
    
    # 初始化默认数据（设备）
    print("\n🔧 初始化默认设备...")
    db_service.initialize_default_data()
    
    # 创建示例用户
    print("\n👤 创建示例用户...")
    sample_users = [
        {
            "username": "张三",
            "email": "zhangsan@example.com",
            "familiarity_score": 75,
            "preferred_tone": "casual"
        },
        {
            "username": "李四",
            "email": "lisi@example.com",
            "familiarity_score": 45,
            "preferred_tone": "polite"
        },
        {
            "username": "王五",
            "email": "wangwu@example.com",
            "familiarity_score": 30,
            "preferred_tone": "formal"
        },
        {
            "username": "测试用户",
            "email": "test@example.com",
            "familiarity_score": 90,
            "preferred_tone": "intimate"
        }
    ]
    
    created_users = []
    for user_data in sample_users:
        username = user_data["username"]
        try:
            user = db_service.get_or_create_user(
                user_id=username,
                username=username,
                email=user_data.get("email")
            )
            
            # 更新用户信息
            db_service.update_user(
                user_id=username,
                familiarity_score=user_data["familiarity_score"],
                preferred_tone=user_data["preferred_tone"]
            )
            
            created_users.append(username)
            print(f"   ✅ 创建用户: {username} (熟悉度: {user_data['familiarity_score']})")
        except Exception as e:
            print(f"   ⚠️  用户 {username} 已存在或创建失败: {e}")
    
    # 创建额外的示例设备
    print("\n🏠 创建示例设备...")
    sample_devices = [
        {
            "id": "bedroom_light",
            "name": "卧室灯",
            "device_type": "lights",
            "room": "bedroom",
            "supported_actions": ["turn_on", "turn_off", "set_brightness"],
            "capabilities": {"brightness": {"min": 0, "max": 100}},
            "current_state": {"status": "off", "brightness": 0},
            "default_min_familiarity": 20
        },
        {
            "id": "kitchen_light",
            "name": "厨房灯",
            "device_type": "lights",
            "room": "kitchen",
            "supported_actions": ["turn_on", "turn_off", "set_brightness"],
            "capabilities": {"brightness": {"min": 0, "max": 100}},
            "current_state": {"status": "off", "brightness": 0},
            "default_min_familiarity": 25
        },
        {
            "id": "bedroom_ac",
            "name": "卧室空调",
            "device_type": "air_conditioner",
            "room": "bedroom",
            "supported_actions": ["turn_on", "turn_off", "set_temperature", "set_mode"],
            "capabilities": {
                "temperature": {"min": 16, "max": 30},
                "modes": ["cool", "heat", "fan", "dry"]
            },
            "current_state": {"status": "off", "temperature": 26, "mode": "cool"},
            "default_min_familiarity": 35
        },
        {
            "id": "living_room_curtains",
            "name": "客厅窗帘",
            "device_type": "curtains",
            "room": "living_room",
            "supported_actions": ["open", "close", "set_position"],
            "capabilities": {"position": {"min": 0, "max": 100}},
            "current_state": {"status": "closed", "position": 0},
            "default_min_familiarity": 30
        }
    ]
    
    created_devices = []
    for device_data in sample_devices:
        device_id = device_data["id"]
        try:
            device = db_service.create_device(device_data)
            if device:
                created_devices.append(device_id)
                print(f"   ✅ 创建设备: {device_data['name']} ({device_id})")
            else:
                print(f"   ⚠️  设备 {device_id} 已存在")
        except Exception as e:
            print(f"   ⚠️  设备 {device_id} 创建失败: {e}")
    
    # 为用户分配设备
    print("\n🔗 为用户分配设备...")
    
    # 张三 - 高熟悉度用户，可以访问所有设备
    if "张三" in created_users:
        user_devices = [
            ("living_room_lights", "我的客厅灯", True),
            ("tv", "我的电视", True),
            ("bedroom_light", "卧室主灯", False),
            ("bedroom_ac", "卧室空调", False),
        ]
        
        for device_id, custom_name, is_favorite in user_devices:
            try:
                result = db_service.add_user_device(
                    user_id="张三",
                    device_id=device_id,
                    custom_name=custom_name,
                    is_favorite=is_favorite
                )
                if result:
                    print(f"   ✅ 为张三添加设备: {custom_name}")
            except Exception as e:
                print(f"   ⚠️  为张三添加设备失败: {e}")
    
    # 李四 - 中等熟悉度用户
    if "李四" in created_users:
        user_devices = [
            ("living_room_lights", "客厅灯", True),
            ("kitchen_light", "厨房灯", False),
        ]
        
        for device_id, custom_name, is_favorite in user_devices:
            try:
                result = db_service.add_user_device(
                    user_id="李四",
                    device_id=device_id,
                    custom_name=custom_name,
                    is_favorite=is_favorite
                )
                if result:
                    print(f"   ✅ 为李四添加设备: {custom_name}")
            except Exception as e:
                print(f"   ⚠️  为李四添加设备失败: {e}")
    
    # 测试用户 - 最高熟悉度用户，所有设备
    if "测试用户" in created_users:
        all_devices = db_service.get_all_devices()
        for device in all_devices[:5]:  # 只添加前5个设备
            try:
                result = db_service.add_user_device(
                    user_id="测试用户",
                    device_id=device.id,
                    is_favorite=(device.id == "tv")
                )
                if result:
                    print(f"   ✅ 为测试用户添加设备: {device.name}")
            except Exception as e:
                pass
    
    # 显示统计信息
    print("\n" + "=" * 60)
    print("📊 数据统计:")
    
    session = db_service.get_session()
    try:
        user_count = session.query(User).filter_by(is_active=True).count()
        device_count = session.query(Device).filter_by(is_active=True).count()
        user_device_count = session.query(UserDevice).count()
        
        print(f"   👥 活跃用户: {user_count}")
        print(f"   🏠 活跃设备: {device_count}")
        print(f"   🔗 用户设备关联: {user_device_count}")
    finally:
        session.close()
    
    print("\n" + "=" * 60)
    print("✅ 示例数据初始化完成!")
    print("\n📝 接下来你可以:")
    print("   1. 运行 ./start_admin_panel.sh 启动管理面板")
    print("   2. 在浏览器中打开 admin_panel.html")
    print("   3. 开始管理用户和设备")
    print()

if __name__ == "__main__":
    try:
        init_sample_data()
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

