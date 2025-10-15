#!/usr/bin/env python3
"""
Initialize Real Devices in Database
Adds the two real devices (dimmable light and curtain) to the database
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import Config
from src.services.database_service import DatabaseService


def init_real_devices():
    """Initialize real devices in database"""
    
    print("\n" + "="*60)
    print("Initializing Real Devices")
    print("="*60 + "\n")
    
    config = Config()
    db_service = DatabaseService(config)
    
    # Device 1: Dimmable Light (调光灯)
    dimmable_light = {
        "id": "8CD5C5AD-CB2C-5ECB-9C73-9EF3AEF69A1D",  # Using sn as id
        "name": "演示调光灯",
        "device_type": "57D56F4D-3302-41F7-AB34-5365AA180E81",
        "room": "卧室",
        "supported_actions": [
            "turn_on",
            "turn_off",
            "set_brightness",
            "set_hue",
            "set_saturation",
            "set_color"
        ],
        "capabilities": {
            "brightness": {"min": 0, "max": 100},
            "hue": {"min": 0, "max": 360},
            "saturation": {"min": 0, "max": 100}
        },
        "current_state": {
            "isOn": True,
            "status": "on",
            "brightness": 30,
            "hue": 330,  # 紫红色
            "saturation": 50
        },
        "is_active": True,
        "requires_auth": False,
        "default_min_familiarity": 30,
        "description": "HomeKit调光灯，支持亮度和颜色调节",
        "manufacturer": "HomeKit",
        "model": "Dimmable Light"
    }
    
    # Device 2: Curtain (窗帘)
    curtain = {
        "id": "7EF787F0-DED1-58AD-9876-27C2CB27E237",  # Using sn as id
        "name": "演示窗帘",
        "device_type": "2FB9EE1F-1C21-4D0B-9383-9B65F64DBF0E",
        "room": "卧室",
        "supported_actions": [
            "open_curtain",
            "close_curtain",
            "set_position",
            "set_curtain_position"
        ],
        "capabilities": {
            "targetPosition": {"min": 0, "max": 100},
            "currentPosition": {"min": 0, "max": 100, "readonly": True}
        },
        "current_state": {
            "isOn": False,
            "status": "off",
            "targetPosition": 0,
            "currentPosition": 0
        },
        "is_active": True,
        "requires_auth": False,
        "default_min_familiarity": 30,
        "description": "HomeKit窗帘，支持位置调节",
        "manufacturer": "HomeKit",
        "model": "Curtain"
    }
    
    # Add devices to database
    devices = [dimmable_light, curtain]
    
    for device_data in devices:
        try:
            # Try to create or update device
            device = db_service.get_device(device_data["id"])
            
            if device:
                print(f"📝 Updating existing device: {device_data['name']}")
                db_service.update_device(device_data["id"], device_data)
            else:
                print(f"➕ Creating new device: {device_data['name']}")
                db_service.create_device(device_data)
            
            print(f"   ✅ Device ID: {device_data['id']}")
            print(f"   📍 Room: {device_data['room']}")
            print(f"   🔧 Type: {device_data['device_type']}")
            print(f"   ⚙️  Supported actions: {', '.join(device_data['supported_actions'])}")
            print()
            
        except Exception as e:
            print(f"   ❌ Error processing {device_data['name']}: {e}")
            print()
    
    print("="*60)
    print("✅ Real devices initialization completed!")
    print("="*60 + "\n")
    
    # Display summary
    print("📋 Device Summary:")
    print()
    print("1. 演示调光灯 (Dimmable Light)")
    print(f"   - ID: {dimmable_light['id']}")
    print(f"   - Current state: Brightness {dimmable_light['current_state']['brightness']}%, "
          f"Hue {dimmable_light['current_state']['hue']}°, "
          f"Saturation {dimmable_light['current_state']['saturation']}%")
    print()
    
    print("2. 演示窗帘 (Curtain)")
    print(f"   - ID: {curtain['id']}")
    print(f"   - Current state: Position {curtain['current_state']['currentPosition']}%")
    print()
    
    print("🎉 You can now control these devices using the Device Controller!")
    print()


if __name__ == "__main__":
    init_real_devices()

