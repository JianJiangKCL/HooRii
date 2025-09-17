# HooRii JSON 导入导出接口使用指南

## 概述

HooRii 智能家居系统提供了完整的 JSON 格式数据导入导出接口，支持用户和设备数据的批量管理。

## API 端点

### 用户管理
- `POST /users/import/json` - 导入用户数据
- `POST /users/export/json` - 导出用户数据

### 设备管理
- `POST /devices/import/json` - 导入设备数据
- `POST /devices/export/json` - 导出设备数据

---

## 用户数据格式

### 导入用户数据

**端点**: `POST /users/import/json`

**请求格式**:
```json
{
    "users": [
        {
            "id": "user_001",                    // 用户ID (必填)
            "username": "张三",                  // 用户名 (必填)
            "email": "zhangsan@example.com",     // 邮箱 (可选)
            "familiarity_score": 75,             // 熟悉度分数 0-100 (可选，默认25)
            "preferred_tone": "casual",          // 语调偏好 (可选，默认polite)
            "preferences": {                     // 用户偏好设置 (可选)
                "theme": "dark",
                "language": "zh-CN",
                "notification": true
            },
            "is_active": true                    // 是否活跃 (可选，默认true)
        },
        {
            "id": "user_002",
            "username": "李四",
            "email": "lisi@example.com",
            "familiarity_score": 45,
            "preferred_tone": "polite",
            "preferences": {
                "theme": "light",
                "language": "zh-CN"
            },
            "is_active": true
        }
    ],
    "overwrite_existing": false                  // 是否覆盖已存在的用户 (可选，默认false)
}
```

**语调偏好选项**:
- `formal` - 正式
- `polite` - 礼貌 (默认)
- `casual` - 随意
- `intimate` - 亲密

**响应示例**:
```json
{
    "success": true,
    "imported_count": 2,
    "updated_count": 0,
    "processed_users": ["user_001", "user_002"],
    "errors": [],
    "message": "成功导入 2 个用户，更新 0 个用户"
}
```

### 导出用户数据

**端点**: `POST /users/export/json`

**请求格式** (可选参数):
```json
{
    "include_inactive": false,               // 是否包含非活跃用户 (默认false)
    "user_ids": ["user_001", "user_002"]    // 指定导出的用户ID (可选，为空则导出所有)
}
```

**响应示例**:
```json
{
    "users": [
        {
            "id": "user_001",
            "username": "张三",
            "email": "zhangsan@example.com",
            "familiarity_score": 75,
            "preferred_tone": "casual",
            "preferences": {
                "theme": "dark",
                "language": "zh-CN",
                "notification": true
            },
            "interaction_count": 150,
            "is_active": true,
            "created_at": "2025-01-13T10:30:00Z",
            "updated_at": "2025-01-13T15:45:00Z",
            "last_seen": "2025-01-13T16:00:00Z"
        }
    ],
    "export_info": {
        "total_count": 1,
        "export_time": "2025-01-13T16:05:00Z",
        "include_inactive": false,
        "filtered_user_ids": ["user_001", "user_002"]
    }
}
```

---

## 设备数据格式

### 导入设备数据

**端点**: `POST /devices/import/json`

**请求格式**:
```json
{
    "devices": [
        {
            "id": "living_room_light_001",      // 设备ID (必填)
            "name": "客厅主灯",                  // 设备名称 (必填)
            "device_type": "lights",             // 设备类型 (必填)
            "room": "客厅",                      // 房间 (可选)
            "supported_actions": [               // 支持的操作 (可选，会自动设置)
                "turn_on", "turn_off", "set_brightness"
            ],
            "capabilities": {                    // 设备能力 (可选，会自动设置)
                "brightness": {"min": 0, "max": 100}
            },
            "current_state": {                   // 当前状态 (可选)
                "status": "off",
                "brightness": 0
            },
            "min_familiarity_required": 30,     // 所需最低熟悉度 (可选，默认40)
            "requires_auth": false,             // 是否需要认证 (可选，默认false)
            "is_active": true                   // 是否活跃 (可选，默认true)
        },
        {
            "id": "living_room_tv",
            "name": "客厅电视",
            "device_type": "tv",
            "room": "客厅",
            "min_familiarity_required": 40
            // supported_actions 和 capabilities 会自动设置为TV默认值
        },
        {
            "id": "bedroom_ac",
            "name": "卧室空调",
            "device_type": "air_conditioner",
            "room": "卧室",
            "min_familiarity_required": 60,
            "supported_actions": ["turn_on", "turn_off", "set_temperature", "set_mode"],
            "capabilities": {
                "temperature": {"min": 16, "max": 30},
                "modes": ["cool", "heat", "auto", "fan"]
            }
        }
    ],
    "overwrite_existing": false                 // 是否覆盖已存在的设备 (可选，默认false)
}
```

**设备类型**:
- `lights` - 灯具 (默认操作: turn_on, turn_off, set_brightness)
- `tv` - 电视 (默认操作: turn_on, turn_off, set_volume, set_channel)
- `speaker` - 音响 (默认操作: turn_on, turn_off, set_volume)
- `air_conditioner` - 空调 (默认操作: turn_on, turn_off)
- `curtains` - 窗帘 (默认操作: turn_on, turn_off)
- `other` - 其他 (默认操作: turn_on, turn_off)

**响应示例**:
```json
{
    "success": true,
    "imported_count": 3,
    "updated_count": 0,
    "processed_devices": ["living_room_light_001", "living_room_tv", "bedroom_ac"],
    "errors": [],
    "message": "成功导入 3 个设备，更新 0 个设备"
}
```

### 导出设备数据

**端点**: `POST /devices/export/json`

**请求格式** (可选参数):
```json
{
    "include_inactive": false,                           // 是否包含非活跃设备 (默认false)
    "device_ids": ["living_room_light_001", "living_room_tv"]  // 指定导出的设备ID (可选)
}
```

**响应示例**:
```json
{
    "devices": [
        {
            "id": "living_room_light_001",
            "name": "客厅主灯",
            "device_type": "lights",
            "room": "客厅",
            "supported_actions": ["turn_on", "turn_off", "set_brightness"],
            "capabilities": {"brightness": {"min": 0, "max": 100}},
            "current_state": {"status": "off", "brightness": 0},
            "min_familiarity_required": 30,
            "requires_auth": false,
            "is_active": true,
            "last_updated": "2025-01-13T16:00:00Z"
        }
    ],
    "export_info": {
        "total_count": 1,
        "export_time": "2025-01-13T16:05:00Z",
        "include_inactive": false,
        "filtered_device_ids": ["living_room_light_001", "living_room_tv"]
    }
}
```

---

## 使用示例

### 1. 使用 curl 导入用户数据

```bash
curl -X POST "http://localhost:8000/users/import/json" \
  -H "Content-Type: application/json" \
  -d '{
    "users": [
      {
        "id": "family_dad",
        "username": "爸爸",
        "email": "dad@family.com",
        "familiarity_score": 80,
        "preferred_tone": "casual",
        "preferences": {
          "wake_up_time": "07:00",
          "sleep_time": "23:00"
        }
      }
    ],
    "overwrite_existing": false
  }'
```

### 2. 使用 curl 导出所有用户数据

```bash
curl -X POST "http://localhost:8000/users/export/json" \
  -H "Content-Type: application/json" \
  -d '{
    "include_inactive": true
  }'
```

### 3. 使用 curl 导入设备数据

```bash
curl -X POST "http://localhost:8000/devices/import/json" \
  -H "Content-Type: application/json" \
  -d '{
    "devices": [
      {
        "id": "smart_home_hub",
        "name": "智能家居中枢",
        "device_type": "other",
        "room": "客厅",
        "min_familiarity_required": 70,
        "supported_actions": ["status", "restart", "update"],
        "capabilities": {
          "wifi": true,
          "zigbee": true,
          "bluetooth": true
        }
      }
    ]
  }'
```

### 4. 使用 Python 导出设备数据

```python
import requests
import json

# 导出特定房间的设备
response = requests.post(
    "http://localhost:8000/devices/export/json",
    headers={"Content-Type": "application/json"},
    json={
        "include_inactive": False
    }
)

if response.status_code == 200:
    data = response.json()
    
    # 保存到文件
    with open("devices_backup.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"导出了 {data['export_info']['total_count']} 个设备")
else:
    print(f"导出失败: {response.text}")
```

---

## 错误处理

### 常见错误情况

1. **必填字段缺失**
```json
{
    "success": false,
    "errors": ["用户数据缺少必填字段 id 或 username"]
}
```

2. **数据冲突**
```json
{
    "success": false,
    "errors": ["用户 user_001 已存在，跳过"]
}
```

3. **数据格式错误**
```json
{
    "success": false,
    "errors": ["处理用户 user_001 时出错: 'familiarity_score' must be between 0 and 100"]
}
```

### 最佳实践

1. **导入前备份**: 在导入大量数据前，先导出现有数据作为备份
2. **分批导入**: 对于大量数据，建议分批导入以避免超时
3. **验证数据**: 导入前验证JSON格式和必填字段
4. **使用覆盖选项**: 需要更新现有数据时，设置 `overwrite_existing: true`
5. **检查响应**: 总是检查API响应中的错误信息

---

## 完整的数据迁移示例

### 1. 导出现有数据
```bash
# 导出用户数据
curl -X POST "http://localhost:8000/users/export/json" \
  -H "Content-Type: application/json" \
  -d '{"include_inactive": true}' \
  -o users_backup.json

# 导出设备数据
curl -X POST "http://localhost:8000/devices/export/json" \
  -H "Content-Type: application/json" \
  -d '{"include_inactive": true}' \
  -o devices_backup.json
```

### 2. 修改数据格式 (如需要)
```python
import json

# 读取导出的数据
with open("users_backup.json", "r", encoding="utf-8") as f:
    user_data = json.load(f)

# 修改数据格式以适应导入格式
import_data = {
    "users": user_data["users"],
    "overwrite_existing": True
}

# 保存修改后的数据
with open("users_import.json", "w", encoding="utf-8") as f:
    json.dump(import_data, f, ensure_ascii=False, indent=2)
```

### 3. 导入修改后的数据
```bash
curl -X POST "http://localhost:8000/users/import/json" \
  -H "Content-Type: application/json" \
  -d @users_import.json
```

这样你就有了完整的JSON格式数据导入导出功能！
