# Hoorii to n8n Migration Guide

## 架构概览

基于你的模板和Hoorii项目，我设计了一个完整的n8n AI Agent架构：

### 核心组件映射

| Hoorii组件 | n8n实现方式 | 说明 |
|------------|------------|------|
| main.py | Main Workflow | 主工作流协调所有操作 |
| intent_analyzer.py | Intent Analyzer Tool | 子工作流工具节点 |
| device_controller.py | Device Control Workflow | 设备控制子工作流 |
| character_system.py | Claude Agent Node | 集成在主Agent节点 |
| context_manager.py | PostgreSQL Memory | n8n原生记忆管理 |
| api.py | Webhook/WebSocket Triggers | 多触发器支持 |
| models.py | PostgreSQL/Supabase | 数据持久化 |
| Langfuse | HTTP Request Node | 观察性分析 |

## 需要准备的资源

### 1. **环境变量配置**
```env
# Claude API
ANTHROPIC_API_KEY=sk-ant-api03-xxx

# Database
DATABASE_URL=postgresql://user:pass@localhost/hoorii

# Smart Home API (你需要提供)
SMART_HOME_API=http://your-home-assistant-url/api

# Langfuse (可选)
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx

# Notifications (可选)
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx
EMAIL_SMTP_HOST=smtp.gmail.com
```

### 2. **数据库迁移脚本**
```sql
-- PostgreSQL schema for n8n
CREATE TABLE users (
    user_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    familiarity_score INTEGER DEFAULT 0,
    interaction_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    preferences JSONB DEFAULT '{}'
);

CREATE TABLE conversations (
    session_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id),
    context_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE devices (
    device_id VARCHAR(50) PRIMARY KEY,
    device_type VARCHAR(50),
    name VARCHAR(100),
    current_state JSONB,
    required_familiarity INTEGER DEFAULT 0
);

CREATE TABLE device_interactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    device_id VARCHAR(50),
    action VARCHAR(50),
    parameters JSONB,
    success BOOLEAN,
    timestamp TIMESTAMP DEFAULT NOW(),
    session_id VARCHAR(50)
);

CREATE TABLE user_memories (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    memory_type VARCHAR(50),
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 3. **自定义节点代码**

创建文件 `/data/jj/proj/hoorii/n8n_architecture/custom_nodes/HooriiIntentAnalyzer.node.ts`:

```typescript
import {
  IExecuteFunctions,
  INodeExecutionData,
  INodeType,
  INodeTypeDescription,
} from 'n8n-workflow';

export class HooriiIntentAnalyzer implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'Hoorii Intent Analyzer',
    name: 'hooriiIntentAnalyzer',
    group: ['transform'],
    version: 1,
    description: 'Analyze user intent for Hoorii assistant',
    defaults: {
      name: 'Hoorii Intent Analyzer',
    },
    inputs: ['main'],
    outputs: ['main'],
    credentials: [
      {
        name: 'anthropicApi',
        required: true,
      },
    ],
    properties: [
      {
        displayName: 'User Message',
        name: 'userMessage',
        type: 'string',
        default: '',
        required: true,
      },
      {
        displayName: 'Context',
        name: 'context',
        type: 'json',
        default: '{}',
      },
    ],
  };

  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
    const items = this.getInputData();
    const returnData: INodeExecutionData[] = [];

    for (let i = 0; i < items.length; i++) {
      const userMessage = this.getNodeParameter('userMessage', i) as string;
      const context = this.getNodeParameter('context', i) as object;

      // Intent analysis logic using Claude
      const intent = await analyzeWithClaude(userMessage, context);

      returnData.push({
        json: {
          intent: intent.type,
          entities: intent.entities,
          confidence: intent.confidence,
          original_message: userMessage,
        },
      });
    }

    return [returnData];
  }
}
```

### 4. **工作流导入步骤**

1. **导入主工作流**
   - 打开n8n界面
   - 创建新工作流
   - 导入 `main_workflow.json`
   - 配置Anthropic API凭证

2. **创建子工作流**
   - Device Control Workflow
   - User Management Workflow
   - Memory Management Workflow
   - Intent Analyzer Workflow

3. **配置数据库连接**
   - 添加PostgreSQL凭证
   - 测试连接
   - 运行数据库初始化脚本

4. **设置WebSocket支持**
   ```javascript
   // WebSocket handler node
   const ws = require('ws');
   const wss = new ws.Server({ port: 8080 });

   wss.on('connection', (ws) => {
     ws.on('message', async (message) => {
       // Trigger main workflow
       const response = await $execution.workflow(
         'hoorii-main-workflow',
         { message: message.toString() }
       );
       ws.send(JSON.stringify(response));
     });
   });
   ```

## 实时性实现方案

### 1. **WebSocket实时通信**
- 使用n8n的WebSocket节点接收消息
- 通过Webhook Response节点实时返回
- 支持双向通信

### 2. **流式响应**
```javascript
// Stream response node
const response = $execution.item.json.agent_response;
const chunks = response.split(' ');

for (const chunk of chunks) {
  await $execution.emit('chunk', chunk);
  await new Promise(r => setTimeout(r, 50));
}
```

### 3. **设备状态实时同步**
- MQTT订阅设备状态变化
- WebSocket推送更新给客户端
- Redis缓存当前状态

## 性能优化建议

### 1. **提示词缓存**
```javascript
// Cache prompts in Redis
const redis = require('redis');
const client = redis.createClient();

const cacheKey = `prompt:${userId}:${intentType}`;
const cached = await client.get(cacheKey);

if (!cached) {
  const prompt = await generatePrompt(context);
  await client.setex(cacheKey, 3600, prompt);
}
```

### 2. **并行处理**
- 使用Split In Batches节点并行处理
- 多个设备操作并发执行
- 异步更新用户统计

### 3. **连接池管理**
```javascript
// PostgreSQL connection pool
const pool = new Pool({
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});
```

## 部署建议

### 1. **Docker Compose部署**
```yaml
version: '3.8'
services:
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=password
    volumes:
      - ./n8n_data:/home/node/.n8n
      - ./custom_nodes:/home/node/.n8n/custom

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=hoorii
      - POSTGRES_USER=hoorii
      - POSTGRES_PASSWORD=password
    volumes:
      - ./postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### 2. **监控设置**
- Prometheus指标收集
- Grafana仪表板
- Langfuse追踪分析

## 迁移检查清单

- [ ] 导出现有用户数据
- [ ] 导出设备配置
- [ ] 备份对话历史
- [ ] 配置API密钥
- [ ] 设置数据库
- [ ] 导入工作流
- [ ] 配置触发器
- [ ] 测试设备控制
- [ ] 验证权限系统
- [ ] 测试实时通信
- [ ] 性能基准测试
- [ ] 部署到生产环境

## 下一步行动

1. **提供以下信息**：
   - 智能家居API端点和认证方式
   - 设备ID列表和类型
   - 是否需要保留历史数据
   - 部署环境（云/本地）
   - 性能要求（QPS、延迟）

2. **我可以帮你生成**：
   - 完整的工作流JSON文件
   - 自定义节点TypeScript代码
   - 数据迁移脚本
   - API适配器代码
   - 部署配置文件

这个架构保留了Hoorii的所有核心功能，同时利用n8n的优势实现了更好的可视化、可维护性和扩展性。