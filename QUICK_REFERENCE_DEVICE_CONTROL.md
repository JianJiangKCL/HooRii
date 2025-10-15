# 设备控制系统 - 快速参考

## 🚀 快速开始

### 初始化设备
```bash
python scripts/init_real_devices.py
```

### 运行测试
```bash
# 设备控制器测试
python debug/device_controller_real_devices_test.py

# 完整 workflow 测试
python debug/workflow_device_control_test.py
```

## 📋 支持的设备

| 设备 | 类型ID | 命令 |
|-----|--------|------|
| 调光灯 | `57D56F4D-3302-41F7-AB34-5365AA180E81` | turn_on, turn_off, set_brightness, set_hue, set_saturation, set_color |
| 窗帘 | `2FB9EE1F-1C21-4D0B-9383-9B65F64DBF0E` | open_curtain, close_curtain, set_position |
| 普通灯 | `light` | turn_on, turn_off, set_brightness |
| 空调 | `air_conditioner` | turn_on, turn_off, set_temperature, set_mode, set_fan_speed |
| 电视 | `tv` | turn_on, turn_off, set_volume, set_channel, set_input |
| 音响 | `speaker` | turn_on, turn_off, set_volume, play_music, pause, next, previous |

## 🎨 调光灯色值对照

| 颜色 | 色值(hue) | 示例用法 |
|-----|----------|---------|
| 红色 | 0° | "把灯设置成红色" |
| 橙色 | 30° | "橙色灯光" |
| 黄色 | 60° | "黄色暖光" |
| 绿色 | 120° | "绿色灯光" |
| 青色 | 180° | "青色" |
| 蓝色 | 240° | "蓝色灯光" |
| 紫色 | 270° | "紫色" |
| 品红 | 300° | "品红色" |

## 📝 使用示例

### 通过 Workflow 控制
```python
from src.workflows.langraph_workflow import LangGraphHomeAISystem
from src.utils.config import load_config

system = LangGraphHomeAISystem(load_config())

# 控制调光灯
result = await system.process_message(
    "把调光灯调到80%亮度，设置成蓝色",
    user_id="user_123"
)

# 获取控制输出
control_output = result["device_actions"][0]["control_output"]
```

### 直接使用 DeviceController
```python
from src.core.device_controller import DeviceController

controller = DeviceController(config)

intent = {
    "intent_type": "device_control",
    "involves_hardware": True,
    "entities": {"device": "演示调光灯", "brightness": 80}
}

result = await controller.process_device_intent(intent, context)
```

## 📤 标准输出格式

```json
{
  "control_output": {
    "device_id": "8CD5C5AD-CB2C-5ECB-9C73-9EF3AEF69A1D",
    "device_name": "演示调光灯",
    "device_type": "57D56F4D-3302-41F7-AB34-5365AA180E81",
    "command": "set_color",
    "parameters": {
      "isOn": true,
      "brightness": 80,
      "hue": 240,
      "saturation": 80
    },
    "timestamp": "2025-10-14T12:34:56.789Z",
    "user_id": "user_123",
    "familiarity_score": 60
  }
}
```

## ➕ 添加新设备

编辑 `/config/device_specifications.json`:

```json
{
  "devices": {
    "your_device": {
      "device_type_id": "YOUR-UUID",
      "device_type_name": "your_device",
      "display_name": "你的设备",
      "min_familiarity": 40,
      "supported_commands": ["turn_on", "turn_off"],
      "parameters": {
        "param1": {
          "type": "integer",
          "range": [0, 100],
          "default": 50
        }
      }
    }
  }
}
```

无需修改代码，系统会自动加载！

## 🔍 Familiarity 要求

| 设备 | 最低熟悉度 |
|-----|----------|
| 调光灯 | 30 |
| 窗帘 | 30 |
| 普通灯 | 30 |
| 音响 | 40 |
| 电视 | 40 |
| 空调 | 60 |

## 📊 Langfuse 监控

### 监控链路
```
langgraph_workflow (trace)
├── task_plan_node
├── execute_device_actions_node
│   └── device_controller (generation)
├── generate_audio_node
└── finalize_response_node
```

### 查看追踪
1. 访问 Langfuse UI
2. 搜索 trace: `langgraph_workflow`
3. 查看设备控制 span: `execute_device_actions_node`
4. 查看 LLM 调用: `device_controller`

## 🐛 调试

### 查看日志
```python
import logging
logging.getLogger("src.core.device_controller").setLevel(logging.DEBUG)
```

### 常见问题

**Q: Familiarity 不足被拒绝？**
```python
# 检查用户 familiarity
db_service.get_user_familiarity(user_id)

# 查看设备要求
device_spec["min_familiarity"]
```

**Q: 设备未找到？**
```python
# 列出所有设备
db_service.get_all_devices(active_only=True)

# 初始化真实设备
python scripts/init_real_devices.py
```

**Q: 参数超出范围？**
```python
# 查看设备规格
device_spec = controller._get_device_spec(device_type)
print(device_spec["parameters"])
```

## 📚 完整文档

- [完整系统总结](DEVICE_SYSTEM_COMPLETE_SUMMARY.md)
- [真实设备文档](docs/DEVICE_CONTROLLER_REAL_DEVICES.md)
- [Workflow 验证](docs/DEVICE_CONTROL_WORKFLOW_VALIDATION.md)
- [测试指南](debug/README.md)

## 🎯 测试场景

```bash
# 场景 1: 调光灯控制
"把调光灯调到50%"
"把灯设置成红色"
"灯光调亮一点"

# 场景 2: 窗帘控制
"打开窗帘"
"把窗帘开到一半"
"关闭窗帘"

# 场景 3: 组合控制
"把调光灯调到80%亮度，设置成蓝色，饱和度70%"
```

---

**需要帮助？** 查看 [完整文档](DEVICE_SYSTEM_COMPLETE_SUMMARY.md)

