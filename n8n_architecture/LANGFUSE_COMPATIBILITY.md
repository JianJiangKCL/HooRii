# Langfuse 兼容性说明

## ✅ 当前兼容性状态

是的，当前的n8n架构**完全兼容Langfuse**！已经实现了以下集成：

### 🔧 已配置的功能

1. **环境变量自动读取**
   - 从现有`.env`文件自动提取Langfuse密钥
   - `LANGFUSE_PUBLIC_KEY`: pk-lf-6d6d3fda-028a-46f2-a801-0d1dc055da1f
   - `LANGFUSE_SECRET_KEY`: sk-lf-304e1c14-ec1b-4913-8db3-bfe54c6fbac1
   - `LANGFUSE_HOST`: https://us.cloud.langfuse.com

2. **完整的观察性追踪**
   - ✅ Trace追踪：每个对话创建独立追踪
   - ✅ Span记录：意图分析、设备控制分步记录
   - ✅ Generation追踪：LLM调用和token使用统计
   - ✅ Score评分：自动用户满意度评分
   - ✅ 性能监控：响应时间、缓存命中率

3. **智能元数据记录**
   - 用户亲密度分数变化
   - 设备控制成功/失败
   - 字符一致性评估
   - 错误自动捕获和分类

## 📊 Langfuse中的数据视图

### Trace层级结构
```
🏠 Hoorii Conversation (Trace)
├── 🎯 Intent Analysis (Span)
│   ├── Input: 用户消息 + 上下文
│   └── Output: 意图分类结果
├── 🏠 Device Control (Span)
│   ├── Input: 设备ID + 动作参数
│   └── Output: 控制结果
└── 🤖 Character Response (Generation)
    ├── Model: Claude-3.5-Sonnet
    ├── Tokens: 输入/输出token统计
    └── Output: 凌波丽风格回复
```

### 自动记录的指标
- **性能指标**：总响应时间、各组件耗时
- **质量指标**：意图识别准确度、角色一致性
- **用户指标**：亲密度变化、交互成功率
- **系统指标**：缓存命中率、错误率

## 🚀 部署后的Langfuse使用

### 1. 自动启用
运行 `./simple_deploy.sh` 后，Langfuse集成会自动启用，无需额外配置。

### 2. 查看数据
1. 访问：https://us.cloud.langfuse.com
2. 登录你的Langfuse账户
3. 在Projects中查看"Hoorii"项目数据

### 3. 关键指标监控

#### Dashboard中可以看到：
- **对话量**：每日/每周对话数量趋势
- **响应时间**：平均响应时间和P95延迟
- **成功率**：设备控制成功率
- **用户参与度**：不同亲密度用户的活跃情况
- **设备使用**：最常用的智能设备Top 10
- **错误分析**：失败原因分类和频率

#### 实时追踪功能：
- **Live Traces**：实时查看正在进行的对话
- **Debug模式**：详细的执行步骤和中间结果
- **Error Alerts**：自动错误告警和通知

## 📈 高级Langfuse功能使用

### 1. 自定义评分
```javascript
// 在n8n工作流中添加自定义评分
{
  "name": "character_consistency",
  "value": calculateCharacterConsistency(response, familiarity_score),
  "comment": "凌波丽角色一致性评分"
}
```

### 2. A/B测试支持
```javascript
// 不同提示词版本对比
{
  "version": "v1.2_formal_tone",
  "experiment": "tone_optimization",
  "variant": familiarity_score > 50 ? "intimate" : "formal"
}
```

### 3. 用户行为分析
```javascript
// 用户细分和行为模式
{
  "user_segment": getFamiliaritySegment(familiarity_score),
  "interaction_pattern": getInteractionPattern(user_history),
  "device_preference": getMostUsedDevices(user_id)
}
```

## 🔧 配置选项

### 环境变量配置 (已自动设置)
```bash
LANGFUSE_PUBLIC_KEY=pk-lf-6d6d3fda-028a-46f2-a801-0d1dc055da1f
LANGFUSE_SECRET_KEY=sk-lf-304e1c14-ec1b-4913-8db3-bfe54c6fbac1
LANGFUSE_HOST=https://us.cloud.langfuse.com
```

### n8n工作流中的集成点
1. **对话开始**：创建Trace
2. **意图分析后**：记录Span
3. **设备控制后**：记录操作结果
4. **AI回复生成**：记录Generation
5. **对话结束**：完成Trace并评分

## 📋 监控检查清单

部署完成后，确认以下Langfuse功能正常：

- [ ] Traces正常创建和更新
- [ ] Spans包含详细的执行信息
- [ ] Generations记录Claude API调用
- [ ] Scores自动评分用户满意度
- [ ] 性能指标准确记录
- [ ] 错误自动捕获和分类
- [ ] 用户细分数据完整
- [ ] 设备使用统计准确

## 🎯 Langfuse最佳实践

### 1. 数据质量
- ✅ 确保所有关键字段有值（user_id、session_id、intent）
- ✅ 统一命名规范（hoorii_*, rei_*, device_*）
- ✅ 合理的采样率（100%用于开发，10%用于生产高负载）

### 2. 性能优化
- ✅ 异步发送到Langfuse（不阻塞用户响应）
- ✅ 批量上传减少API调用
- ✅ 本地缓存减少网络延迟

### 3. 隐私保护
- ✅ 敏感信息脱敏（设备状态、位置信息）
- ✅ 用户同意机制
- ✅ 数据保留策略（30天自动删除）

## 🚨 故障排除

### 如果Langfuse数据未显示：

1. **检查API密钥**
```bash
cd hoorii-n8n
grep LANGFUSE .env
```

2. **测试连接**
```bash
curl -X POST https://us.cloud.langfuse.com/api/public/traces \
  -H "Authorization: Basic $(echo -n 'pk-lf-xxx:sk-lf-xxx' | base64)" \
  -H "Content-Type: application/json" \
  -d '{"name": "test_trace"}'
```

3. **查看n8n日志**
```bash
docker-compose logs -f n8n | grep langfuse
```

4. **验证网络连接**
```bash
docker-compose exec n8n ping cloud.langfuse.com
```

## 🎉 总结

当前的Hoorii n8n架构已经**完全兼容并集成了Langfuse**，提供：

- 🔄 **自动化追踪**：无需手动配置，开箱即用
- 📊 **完整观察性**：从用户输入到AI响应的全链路追踪
- ⚡ **实时监控**：性能指标、错误率、用户满意度
- 🎯 **智能分析**：用户行为模式、设备使用偏好
- 🛡️ **隐私保护**：数据脱敏、用户同意、自动清理

现在就可以运行 `./simple_deploy.sh` 开始使用完整的Langfuse集成功能！