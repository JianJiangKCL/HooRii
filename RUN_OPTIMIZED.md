# 🚀 运行优化版本 - 快速指南

## ✅ 已完成的优化

系统已经**默认使用优化工作流**，无需任何额外配置！

### 核心改进
- ✅ **1次 API 调用** (原来是2次)
- ✅ **响应速度提升 50%** (~1000ms vs ~2000ms)
- ✅ **API 成本降低 50%**
- ✅ **Familiarity Score 充分利用**

## 🎯 直接运行

### 方式 1: 交互式命令行

```bash
python scripts/run_app.py
```

系统会自动：
- ✅ 使用优化工作流
- ✅ 加载 familiarity_score
- ✅ 单次 API 调用处理请求

### 方式 2: API 服务器

```bash
python scripts/start_api_server.py
```

启动后访问：
- API 文档: http://localhost:8000/docs
- 聊天端点: POST http://localhost:8000/chat

## 📊 验证优化生效

### 查看启动信息

当你运行时，你会看到：

```
🚀 Using Optimized Workflow (Single API Call, 50% faster)
🏠 Starting Hoorii Smart Home AI Assistant...
============================================================
```

### 查看响应时间

在聊天时，留意日志中的时间信息：

```
📊 User familiarity loaded: 60/100
🚀 Starting unified processing (1 API call)
✅ Unified response generated
⏱️ Processing time: 1050ms
```

## 🔧 高级选项

### 切换回传统工作流 (如需要)

编辑 `src/workflows/__init__.py`：

```python
# 在 create_ai_system 函数中
async def create_ai_system(config = None, use_langgraph: bool = False, use_optimized: bool = True):
    # 将 use_optimized 改为 False
```

或者在代码中显式指定：

```python
system = await create_ai_system(config, use_optimized=False)  # 使用传统工作流
```

## 📝 测试命令

### 测试优化效果

```bash
# 对比测试
python compare_workflows.py

# 使用示例
python example_optimized_usage.py

# 完整测试
python debug/optimized_workflow_test.py
```

## 🎨 使用示例

### Python 代码

```python
from src.workflows import create_ai_system
from src.utils.config import Config

# 初始化（默认就是优化版本）
config = Config()
system = await create_ai_system(config)

# 处理请求（单次 API 调用！）
response = await system.process_user_input(
    user_input="开灯",
    user_id="user123"
)

print(response)  # 凌波丽的回复
```

### curl 测试 API

```bash
# 启动 API 服务器
python scripts/start_api_server.py

# 发送聊天请求
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "开灯",
    "user_id": "test_user",
    "conversation_id": null
  }'
```

## 🔍 Familiarity Score 验证

### 测试不同熟悉度

```python
from src.services.database_service import DatabaseService
from src.utils.config import Config

# 初始化
config = Config()
db_service = DatabaseService(config)

# 设置低熟悉度
db_service.update_user_familiarity("test_user", 20)
# 测试："开灯" -> 应该被拒绝

# 设置高熟悉度
db_service.update_user_familiarity("test_user", 80)
# 测试："开灯" -> 应该被接受
```

## 📈 性能监控

系统会在日志中显示：

```
📊 User familiarity loaded: 60/100
🚀 Starting unified processing (1 API call)
✅ Unified response generated - Hardware: True, Familiarity: passed
⏱️ Processing time: 1050ms
```

关键指标：
- **User familiarity loaded**: 确认 familiarity_score 被加载
- **1 API call**: 确认使用优化工作流
- **Processing time**: 响应时间（应该在 1000-1500ms）

## ⚠️ 注意事项

### 必须提供 user_id

```python
# ✅ 正确
response = await system.process_user_input(
    user_input="开灯",
    user_id="user123"  # 必须提供
)

# ❌ 错误（会使用默认 familiarity_score）
response = await system.process_user_input(
    user_input="开灯"
)
```

### API 密钥配置

确保 `.env` 文件已配置：

```bash
# 检查配置
cat .env | grep API_KEY

# 如果没有配置
python setup_env.py
```

## 🎯 常见用例

### 1. 命令行对话

```bash
python scripts/run_app.py

👤 You: 开灯
🤖 Assistant: ......我明白了。

👤 You: 关灯
🤖 Assistant: ......好的。
```

### 2. API 集成

```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "message": "开灯",
        "user_id": "user123"
    }
)

print(response.json()["response"])
```

### 3. WebSocket 实时对话

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/user123');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Response:', data.response);
};

ws.send(JSON.stringify({
    message: "开灯",
    conversation_id: null
}));
```

## 📚 更多文档

- [优化详细文档](docs/OPTIMIZED_WORKFLOW.md)
- [优化总结](OPTIMIZATION_SUMMARY.md)
- [快速开始](QUICK_START_OPTIMIZED.md)

## ✅ 就这样！

系统已经优化完成，直接运行即可：

```bash
python scripts/run_app.py
```

享受 50% 更快的响应速度！🚀

