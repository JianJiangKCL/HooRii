# 智能陪伴家居控制系统 (Smart Home AI Assistant)

一个基于大语言模型的智能家居控制系统，支持连续对话、历史记录存储和个性化体验。

## 🌟 主要特性

### ✨ 核心功能
- **连续对话**: 支持多轮对话，保持上下文理解
- **个性化交互**: 基于用户熟悉度调整交互语调和权限
- **设备控制**: 智能家居设备的语音控制
- **历史记录**: 完整的对话历史和用户记忆存储
- **实时观测**: 集成 Langfuse 进行 LLM 调用监控

### 🏗️ 系统架构
- **数据存储**: PostgreSQL/SQLite 数据库存储用户数据
- **LLM引擎**: Claude-3 Sonnet 驱动的对话系统
- **API接口**: RESTful API 和 WebSocket 实时通信
- **观测平台**: Langfuse 集成用于性能监控

### 🎯 智能特性
- **熟悉度系统**: 0-100分的用户熟悉度评分
- **权限控制**: 基于熟悉度的设备控制权限
- **记忆系统**: 自动提取和存储用户偏好
- **意图识别**: 智能分析用户意图和上下文

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆或下载项目
cd hoorii

# 安装依赖
pip install -r requirements.txt

# 或安装最小依赖
pip install -r requirements-minimal.txt
```

### 2. 配置设置

```bash
# 创建环境配置
python setup_env.py

# 编辑 .env 文件，填入你的API密钥
# ANTHROPIC_API_KEY=your_anthropic_key
# LANGFUSE_SECRET_KEY=your_langfuse_secret_key  (可选)
# LANGFUSE_PUBLIC_KEY=your_langfuse_public_key  (可选)
```

### 3. 运行系统

#### 控制台模式
```bash
python main.py
```

#### API服务器模式
```bash
python start_api_server.py
# 或直接运行
uvicorn api:app --reload
```

#### 测试系统
```bash
python test_system.py
```

## 📖 使用说明

### 控制台交互

启动系统后，你可以：
- 直接输入消息与AI对话
- 输入 `new` 开始新对话
- 输入 `stats` 查看用户统计
- 输入 `devices` 查看设备状态
- 输入 `quit` 退出系统

### API接口

API服务器提供完整的RESTful接口：

- `POST /chat` - 发送消息
- `GET /devices` - 获取设备列表
- `POST /devices/control` - 控制设备
- `GET /users/{user_id}` - 获取用户信息
- `PUT /users/{user_id}/familiarity` - 更新熟悉度

详细API文档: http://localhost:8000/docs

### 设备控制示例

```python
# 高熟悉度用户 (75分)
"开客厅的灯"          # ✅ 执行控制
"把电视声音调到30"     # ✅ 执行控制
"关掉所有设备"        # ✅ 执行控制

# 低熟悉度用户 (20分)
"开灯"               # ❌ 礼貌拒绝
"你好，请问你是谁？"   # ✅ 正常对话
```

### 记忆系统示例

系统会自动识别和保存用户偏好：

```python
用户: "我喜欢晚上调暗灯光"
系统: 自动保存偏好记忆 -> "用户喜欢晚上调暗灯光"

用户: "我总是看Netflix"
系统: 自动保存习惯记忆 -> "用户总是看Netflix"
```

## 🔧 配置说明

### 数据库配置

#### SQLite (开发环境)
```env
DATABASE_URL=sqlite:///./hoorii.db
```

#### PostgreSQL (生产环境)
```env
DATABASE_URL=postgresql://user:password@localhost:5432/hoorii
```

### 熟悉度等级

| 分数范围 | 等级 | 交互语调 | 设备权限 |
|---------|------|---------|---------|
| 0-30    | 陌生人 | 正式 | 无权限 |
| 31-60   | 熟人   | 礼貌 | 需确认 |
| 61-80   | 朋友   | 随意 | 直接执行 |
| 81-100  | 家人   | 亲密 | 主动建议 |

### 系统参数

```env
# 对话超时时间（分钟）
CONVERSATION_TIMEOUT_MINUTES=30

# 设备控制最低熟悉度要求
MIN_FAMILIARITY_FOR_HARDWARE=40

# 日志等级
LOG_LEVEL=INFO
```

## 🏠 支持的设备

当前支持的智能设备：

| 设备ID | 设备名称 | 支持操作 |
|--------|---------|---------|
| `living_room_lights` | 客厅灯 | 开关、调光 |
| `tv` | 电视 | 开关、音量、频道 |
| `soundbar` | 音响 | 开关、音量 |

### 添加新设备

```python
# 在数据库中添加新设备
device = Device(
    id="bedroom_lights",
    name="卧室灯",
    device_type="lights",
    room="bedroom",
    supported_actions=["turn_on", "turn_off", "set_brightness"],
    current_state={"status": "off", "brightness": 0}
)
```

## 📊 监控和分析

### Langfuse集成

系统集成 Langfuse 提供：
- LLM调用追踪
- 性能监控
- 对话质量分析
- 成本统计

### 数据分析

```python
# 获取用户统计
stats = db_service.get_user_statistics(user_id)

# 获取设备使用情况
usage = db_service.get_device_usage_stats(device_id="tv", days=30)

# 获取系统统计
system_stats = db_service.get_system_statistics()
```

## 🔌 扩展开发

### 添加新的意图类型

1. 在 `analyze_intent` 方法中添加新的意图识别逻辑
2. 在 `process_request` 方法中添加处理分支
3. 实现对应的功能方法

### 集成新的设备平台

1. 创建设备适配器类
2. 实现设备控制接口
3. 在 `control_hardware` 方法中调用

### 添加向量搜索

系统预留了向量搜索接口：

```python
# 在 config.py 中启用
VECTOR_SEARCH_ENABLED=true

# 使用 sentence-transformers 进行语义搜索
pip install sentence-transformers faiss-cpu
```

## 📁 项目结构

```
hoorii/
├── main.py                 # 主程序和对话引擎
├── api.py                  # RESTful API服务
├── models.py               # 数据库模型定义
├── database_service.py     # 数据库操作服务
├── config.py               # 配置管理
├── setup_env.py           # 环境设置脚本
├── test_system.py         # 系统测试脚本
├── start_api_server.py    # API服务器启动脚本
├── requirements.txt       # 完整依赖列表
├── requirements-minimal.txt # 最小依赖列表
├── .env.template         # 环境变量模板
└── prompts/
    └── task_planner.txt   # 系统提示词模板
```

## 🐛 故障排除

### 常见问题

1. **ImportError: No module named 'xxx'**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration validation failed**
   ```bash
   # 检查 .env 文件是否正确配置
   python config.py
   ```

3. **Database connection error**
   ```bash
   # SQLite: 确保有写权限
   # PostgreSQL: 确保数据库服务运行且连接信息正确
   ```

4. **Langfuse connection error**
   ```bash
   # 检查密钥是否正确，或在 .env 中禁用
   LANGFUSE_SECRET_KEY=""
   LANGFUSE_PUBLIC_KEY=""
   ```

### 日志调试

```env
# 启用详细日志
DEBUG=true
LOG_LEVEL=DEBUG
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

本项目使用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Anthropic](https://anthropic.com) - Claude AI模型
- [Langfuse](https://langfuse.com) - LLM观测平台
- [FastAPI](https://fastapi.tiangolo.com) - Web框架
- [SQLAlchemy](https://sqlalchemy.org) - ORM工具

---

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 创建 GitHub Issue
- 发送邮件至项目维护者

**享受你的智能家居AI助手！** 🏠✨



