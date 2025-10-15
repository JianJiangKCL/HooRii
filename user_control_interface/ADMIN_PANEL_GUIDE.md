# HooRii 用户管理面板使用指南

## 概述

这是一个全功能的Web管理面板，用于管理HooRii智能家居AI助手的用户和设备。

## 功能特性

### 1. 用户管理
- ✅ 查看所有用户列表
- ✅ 添加新用户
- ✅ 编辑用户信息（用户名、邮箱、熟悉度、语调偏好）
- ✅ 删除用户（软删除）
- ✅ 查看用户统计信息

### 2. 设备管理
- ✅ 查看所有设备列表
- ✅ 添加新设备
- ✅ 编辑设备信息
- ✅ 删除设备
- ✅ 支持多种设备类型（灯光、电视、音响、空调等）

### 3. 用户设备配置
- ✅ 为用户分配设备
- ✅ 自定义设备名称
- ✅ 设置收藏设备
- ✅ 配置设备访问权限
- ✅ 设置设备熟悉度要求
- ✅ 移除用户设备

## 使用方法

### 1. 启动API服务器

首先需要启动HooRii的API服务器：

```bash
cd /data/jj/proj/hoorii
python -m src.api.server
```

默认情况下，API服务器会在 `http://localhost:10020` 上运行。

### 2. 打开管理面板

在浏览器中打开 `admin_panel.html` 文件：

```bash
# 使用默认浏览器打开
xdg-open admin_panel.html

# 或者使用特定浏览器
firefox admin_panel.html
google-chrome admin_panel.html
```

或者直接在文件管理器中双击 `admin_panel.html` 文件。

### 3. 配置API地址

如果API服务器不是运行在默认的 `http://localhost:10020`，可以在管理面板右上角的输入框中修改API地址。

## 使用场景示例

### 场景1：添加新用户

1. 点击"用户管理"标签页
2. 点击"+ 添加用户"按钮
3. 填写用户信息：
   - **用户名**：例如"张三"（必填）
   - **邮箱**：例如"zhangsan@example.com"（可选）
   - **熟悉度分数**：0-100，新用户建议25（默认值）
   - **语调偏好**：选择礼貌/正式/随意/亲密
4. 点击"创建用户"

### 场景2：为用户添加设备

1. 首先确保已经有可用的设备（在"设备管理"中添加）
2. 切换到"用户设备配置"标签页
3. 从下拉菜单中选择用户
4. 点击"+ 为用户添加设备"
5. 选择要添加的设备
6. 可选设置：
   - 自定义设备名称（例如"我的卧室灯"）
   - 是否设为收藏
   - 覆盖最低熟悉度要求
7. 点击"添加设备"

### 场景3：创建设备

1. 点击"设备管理"标签页
2. 点击"+ 添加设备"按钮
3. 填写设备信息：
   - **设备ID**：唯一标识符，例如"living_room_light"（必填）
   - **设备名称**：显示名称，例如"客厅灯"（必填）
   - **设备类型**：选择合适的类型（必填）
   - **房间**：例如"客厅"（可选）
   - **最低熟悉度要求**：控制该设备所需的最低熟悉度（默认40）
4. 点击"创建设备"

## 数据模型说明

### 用户（User）
- `id`: 用户唯一标识
- `username`: 用户名
- `email`: 邮箱
- `familiarity_score`: 熟悉度分数（0-100）
- `preferred_tone`: 语调偏好（formal/polite/casual/intimate）
- `is_active`: 是否活跃

### 设备（Device）
- `id`: 设备唯一标识
- `name`: 设备名称
- `device_type`: 设备类型（lights/tv/speaker等）
- `room`: 所在房间
- `supported_actions`: 支持的操作列表
- `capabilities`: 设备能力（亮度、音量等）
- `min_familiarity_required`: 最低熟悉度要求

### 用户设备（UserDevice）
- `user_id`: 用户ID
- `device_id`: 设备ID
- `custom_name`: 用户自定义名称
- `is_favorite`: 是否收藏
- `is_accessible`: 是否可访问
- `min_familiarity_required`: 覆盖设备的默认熟悉度要求
- `allowed_actions`: 允许的操作列表

## API端点参考

### 用户管理
- `GET /users` - 获取用户列表
- `POST /users` - 创建用户
- `GET /users/{user_id}` - 获取用户详情
- `PUT /users/{user_id}` - 更新用户
- `DELETE /users/{user_id}` - 删除用户

### 设备管理
- `GET /devices` - 获取设备列表
- `POST /devices` - 创建设备
- `GET /devices/{device_id}` - 获取设备详情
- `PUT /devices/{device_id}` - 更新设备
- `DELETE /devices/{device_id}` - 删除设备

### 用户设备管理
- `GET /users/{user_id}/devices` - 获取用户的设备列表
- `POST /users/{user_id}/devices` - 为用户添加设备
- `GET /users/{user_id}/devices/{device_id}` - 获取用户设备配置
- `PUT /users/{user_id}/devices/{device_id}` - 更新用户设备配置
- `DELETE /users/{user_id}/devices/{device_id}` - 移除用户设备

## 故障排除

### 无法连接到API服务器
1. 确认API服务器是否已启动
2. 检查API地址是否正确（右上角输入框）
3. 检查防火墙设置

### 操作失败
1. 检查浏览器控制台是否有错误信息
2. 确认数据库是否正常
3. 查看API服务器日志

### 数据未显示
1. 点击"🔄 刷新"按钮重新加载数据
2. 检查API服务器是否返回正确的数据
3. 确认数据库中是否有数据

## 注意事项

1. **用户名唯一性**：每个用户名必须是唯一的
2. **设备ID唯一性**：每个设备ID必须是唯一的
3. **软删除**：删除用户和设备默认为软删除，数据仍保留在数据库中
4. **熟悉度分数**：范围为0-100，影响用户对设备的访问权限
5. **设备类型**：选择正确的设备类型以获得正确的默认配置

## 界面预览

管理面板包含三个主要标签页：

1. **用户管理**：显示所有用户的列表，支持添加、编辑、删除操作
2. **设备管理**：显示所有设备的列表，支持添加、删除操作
3. **用户设备配置**：为特定用户管理设备访问权限

## 技术栈

- **前端**：纯HTML + CSS + JavaScript（无需构建）
- **后端**：FastAPI（Python）
- **数据库**：SQLite（通过SQLAlchemy ORM）
- **API通信**：RESTful API（JSON格式）

## 扩展功能

未来可以添加的功能：

- [ ] 批量导入用户和设备（CSV/JSON）
- [ ] 用户和设备的搜索过滤
- [ ] 数据可视化（使用统计图表）
- [ ] 用户行为日志查看
- [ ] 设备状态实时监控
- [ ] 权限管理和角色系统

## 支持

如有问题或建议，请联系开发团队或查看项目文档。

