# Device Controller - Real Devices Support

## 概述

本文档描述了 Device Controller 对真实设备的支持，包括调光灯和窗帘的完整参数配置。

## 支持的真实设备

### 1. 调光灯 (Dimmable Light)

**设备信息：**
- **设备ID (sn)**: `8CD5C5AD-CB2C-5ECB-9C73-9EF3AEF69A1D`
- **设备名称**: 演示调光灯
- **设备类型 (device_type)**: `57D56F4D-3302-41F7-AB34-5365AA180E81`
- **所属空间**: 卧室
- **鉴权来源**: HomeKit

**可控制参数：**

| 参数名 | 类型 | 范围 | 说明 |
|--------|------|------|------|
| `isOn` | Boolean | true/false | 开关状态 |
| `brightness` | Integer | 0-100 | 亮度（0=无亮度，100=最亮） |
| `hue` | Integer | 0-360 | 色值（见色值对照表） |
| `saturation` | Integer | 0-100 | 饱和度（0=最低，100=最高） |

**色值对照表：**

| 色值 (hue) | 颜色名称 |
|-----------|---------|
| 0° | 红色 |
| 30° | 橙色 |
| 60° | 黄色 |
| 90° | 黄绿 |
| 120° | 绿色 |
| 150° | 青绿 |
| 180° | 青色 |
| 210° | 靛蓝 |
| 240° | 蓝色 |
| 270° | 紫色 |
| 300° | 品红 |
| 330° | 紫红 |

**物模型示例：**
```json
{
    "user_id": 10020,
    "sn": "8CD5C5AD-CB2C-5ECB-9C73-9EF3AEF69A1D",
    "name": "演示调光灯",
    "room": "卧室",
    "device_type": "57D56F4D-3302-41F7-AB34-5365AA180E81",
    "attribute": "{\"brightness\":30,\"isOn\":true,\"hue\":330,\"saturation\":50}",
    "tsl_source": "HomeKit"
}
```

**支持的命令：**
- `turn_on` - 打开灯
- `turn_off` - 关闭灯
- `set_brightness` - 设置亮度
- `set_hue` - 设置色值
- `set_saturation` - 设置饱和度
- `set_color` - 同时设置色值和饱和度

### 2. 窗帘 (Curtain)

**设备信息：**
- **设备ID (sn)**: `7EF787F0-DED1-58AD-9876-27C2CB27E237`
- **设备名称**: 演示窗帘
- **设备类型 (device_type)**: `2FB9EE1F-1C21-4D0B-9383-9B65F64DBF0E`
- **所属空间**: 卧室
- **鉴权来源**: HomeKit

**可控制参数：**

| 参数名 | 类型 | 范围 | 说明 |
|--------|------|------|------|
| `isOn` | Boolean | true/false | 开关状态 |
| `targetPosition` | Integer | 0-100 | 目标位置（0=完全关闭，100=完全打开） |
| `currentPosition` | Integer | 0-100 | 当前位置（只读） |

**物模型示例：**
```json
{
    "user_id": 10020,
    "sn": "7EF787F0-DED1-58AD-9876-27C2CB27E237",
    "name": "演示窗帘",
    "room": "卧室",
    "device_type": "2FB9EE1F-1C21-4D0B-9383-9B65F64DBF0E",
    "attribute": "{\"currentPosition\":0,\"isOn\":false,\"targetPosition\":0\"}",
    "tsl_source": "HomeKit"
}
```

**支持的命令：**
- `open_curtain` - 完全打开窗帘（targetPosition=100）
- `close_curtain` - 完全关闭窗帘（targetPosition=0）
- `set_position` / `set_curtain_position` - 设置窗帘位置（0-100）

## 代码修改说明

### 修改的文件
- `/src/core/device_controller.py`

### 主要修改点

#### 1. `_get_device_context()` 方法
添加了对新设备类型的能力识别：
- `has_color`: 支持色值和饱和度控制（调光灯）
- `has_position`: 支持位置控制（窗帘）

```python
"capabilities": {
    "can_dim": device.device_type in ["light", "57D56F4D-3302-41F7-AB34-5365AA180E81"],
    "has_temperature": device.device_type == "air_conditioner",
    "has_volume": device.device_type == "speaker",
    "has_color": device.device_type in ["light", "57D56F4D-3302-41F7-AB34-5365AA180E81"],
    "has_position": device.device_type in ["curtain", "2FB9EE1F-1C21-4D0B-9383-9B65F64DBF0E"]
}
```

#### 2. `_execute_control()` 方法
添加了对新命令的支持：
- `set_hue`: 设置色值（0-360）
- `set_saturation`: 设置饱和度（0-100）
- `set_color`: 同时设置色值和饱和度
- `set_position` / `set_curtain_position`: 设置窗帘位置
- `open_curtain`: 完全打开窗帘
- `close_curtain`: 完全关闭窗帘

所有命令都会同时更新 `isOn` 状态字段。

#### 3. `_get_action_description()` 方法
添加了新参数的人性化描述：
- 色值描述（包括颜色名称）
- 饱和度描述
- 窗帘位置描述

新增 `_get_color_name_from_hue()` 辅助方法，将色值转换为中文颜色名称。

#### 4. `_get_status_description()` 方法
添加了对新设备状态的描述：
- 调光灯：显示亮度、色值和饱和度
- 窗帘：显示当前位置和目标位置

支持 `isOn` 字段作为开关状态的判断依据。

#### 5. `_build_device_prompt()` 方法
更新了返回 JSON 格式说明，添加了新参数的描述：
```json
"parameters": {
    "brightness": number,  // 亮度 0-100
    "hue": number,  // 色值 0-360
    "saturation": number,  // 饱和度 0-100
    "targetPosition": number,  // 窗帘位置 0-100
    "position": number  // 通用位置参数
}
```

## 使用示例

### 调光灯控制示例

**1. 打开灯并设置亮度：**
```python
intent = {
    "intent_type": "device_control",
    "involves_hardware": True,
    "entities": {"device": "演示调光灯", "brightness": 80}
}
context.user_input = "把调光灯亮度调到80%"
result = await controller.process_device_intent(intent, context)
```

**2. 设置灯光颜色：**
```python
intent = {
    "intent_type": "device_control",
    "involves_hardware": True,
    "entities": {"device": "演示调光灯", "color": "红色"}
}
context.user_input = "把调光灯设置成红色"
result = await controller.process_device_intent(intent, context)
```

**3. 设置颜色和饱和度：**
```python
intent = {
    "intent_type": "device_control",
    "involves_hardware": True,
    "entities": {
        "device": "演示调光灯",
        "hue": 240,  # 蓝色
        "saturation": 80
    }
}
context.user_input = "把调光灯设置成蓝色，饱和度80%"
result = await controller.process_device_intent(intent, context)
```

### 窗帘控制示例

**1. 完全打开窗帘：**
```python
intent = {
    "intent_type": "device_control",
    "involves_hardware": True,
    "entities": {"device": "演示窗帘", "action": "open"}
}
context.user_input = "打开窗帘"
result = await controller.process_device_intent(intent, context)
```

**2. 设置窗帘位置：**
```python
intent = {
    "intent_type": "device_control",
    "involves_hardware": True,
    "entities": {"device": "演示窗帘", "position": 50}
}
context.user_input = "把窗帘开到一半"
result = await controller.process_device_intent(intent, context)
```

**3. 完全关闭窗帘：**
```python
intent = {
    "intent_type": "device_control",
    "involves_hardware": True,
    "entities": {"device": "演示窗帘", "action": "close"}
}
context.user_input = "关闭窗帘"
result = await controller.process_device_intent(intent, context)
```

## 测试

测试文件位于：`/debug/device_controller_real_devices_test.py`

运行测试：
```bash
cd /data/jj/proj/hoorii
python debug/device_controller_real_devices_test.py
```

测试内容包括：
1. 调光灯的开关、亮度、色值、饱和度控制
2. 窗帘的开关、位置控制
3. 设备状态查询
4. 色值到颜色名称的转换

## 注意事项

1. **设备类型识别**：代码同时支持通用设备类型（如 "light", "curtain"）和具体设备类型 UUID
2. **状态字段兼容性**：同时支持 `status` 和 `isOn` 字段，以保持向后兼容
3. **参数验证**：所有参数都有范围限制，超出范围会自动调整到合法范围
4. **即时响应**：窗帘的 `currentPosition` 在模拟环境中会立即更新为 `targetPosition`
5. **颜色转换**：系统自动将色值转换为中文颜色名称，方便用户理解

## 后续扩展

如需添加更多真实设备，只需：
1. 在 `_get_device_context()` 中添加设备能力定义
2. 在 `_execute_control()` 中添加命令处理逻辑
3. 在 `_get_action_description()` 中添加操作描述
4. 在 `_get_status_description()` 中添加状态描述
5. 更新 prompt 中的参数说明

## 相关文档

- [Device Controller Architecture](./DEVICE_CONTROLLER.md)
- [API Documentation](./API.md)
- [Testing Guide](../debug/README.md)

