# 🚀 HooRii 用户管理面板快速开始

## 5分钟快速上手

### 第一步：初始化示例数据（可选）

如果你想快速体验管理面板的功能，可以运行以下命令创建一些示例用户和设备：

```bash
cd /data/jj/proj/hoorii/user_control_interface
./init_sample_data.py
```

这将创建：
- ✅ 4个示例用户（张三、李四、王五、测试用户）
- ✅ 7个示例设备（客厅灯、电视、音响、卧室灯、厨房灯、空调、窗帘等）
- ✅ 预配置的用户-设备关联

### 第二步：启动管理面板

运行启动脚本：

```bash
./start_admin_panel.sh
```

这个脚本会：
1. 🚀 自动启动API服务器（在后台运行）
2. 🌐 在浏览器中打开管理面板

### 第三步：开始使用

管理面板会自动在浏览器中打开，你可以看到三个标签页：

#### 1. 👥 用户管理
- 查看所有用户列表
- 添加新用户（点击"+ 添加用户"）
- 编辑用户信息（点击"编辑"按钮）
- 删除用户（点击"删除"按钮）
- 查看用户的设备（点击"设备"按钮）

#### 2. 🏠 设备管理
- 查看所有设备列表
- 添加新设备（点击"+ 添加设备"）
- 删除设备（点击"删除"按钮）

#### 3. 🔗 用户设备配置
- 选择用户查看其设备
- 为用户添加设备（点击"+ 为用户添加设备"）
- 移除用户的设备（点击"移除"按钮）
- 设置设备为收藏

### 第四步：停止服务

当你完成操作后，可以停止API服务器：

```bash
./stop_admin_panel.sh
```

## 详细使用示例

### 示例1：创建新用户

1. 打开管理面板
2. 在"用户管理"标签页，点击"+ 添加用户"
3. 填写信息：
   ```
   用户名: 小明
   邮箱: xiaoming@example.com
   熟悉度分数: 50
   语调偏好: 礼貌
   ```
4. 点击"创建用户"
5. ✅ 用户创建成功！

### 示例2：为用户添加设备

1. 切换到"用户设备配置"标签页
2. 从下拉菜单选择"小明"
3. 点击"+ 为用户添加设备"
4. 选择设备（例如：客厅灯）
5. 设置自定义名称（可选）："我的客厅灯"
6. 勾选"设为收藏"（如果需要）
7. 点击"添加设备"
8. ✅ 设备添加成功！

### 示例3：创建新设备

1. 切换到"设备管理"标签页
2. 点击"+ 添加设备"
3. 填写信息：
   ```
   设备ID: study_light
   设备名称: 书房灯
   设备类型: 灯光
   房间: 书房
   最低熟悉度要求: 30
   ```
4. 点击"创建设备"
5. ✅ 设备创建成功！

## 命令行快速参考

```bash
# 初始化示例数据
./init_sample_data.py

# 启动管理面板
./start_admin_panel.sh

# 停止API服务器
./stop_admin_panel.sh

# 查看API服务器日志
tail -f api_server.log

# 手动启动API服务器（前台运行）
python3 -m src.api.server

# 检查API服务器状态
curl http://localhost:10020/health

# 当前数据库路径（由启动脚本设置）
echo $DATABASE_URL  # 预期: sqlite:////data/jj/proj/hoorii/data/hoorii.db
```

## API地址配置

默认API地址是 `http://localhost:10020`

如果你的API服务器运行在其他地址或端口，可以在管理面板右上角的输入框中修改。

## 常见问题

### Q: 管理面板显示"加载失败"
A: 
1. 确认API服务器是否已启动：`lsof -i :10020`
2. 检查API地址是否正确（右上角输入框）
3. 查看浏览器控制台的错误信息

### Q: 如何重置数据库？
A:
```bash
# 备份当前数据库
cp hoorii.db hoorii.db.backup

# 删除数据库文件
rm hoorii.db

# 重新初始化
./init_sample_data.py
```

### Q: 如何导入大量用户？
A: 可以使用API的批量导入功能，准备一个JSON文件：
```json
{
  "users": [
    {
      "id": "user001",
      "username": "用户1",
      "email": "user1@example.com",
      "familiarity_score": 50
    }
  ]
}
```

然后使用curl或Postman发送到 `/users/import/json`

### Q: 管理面板可以远程访问吗？
A: 
- 管理面板HTML文件可以部署到任何Web服务器
- 需要确保API服务器的CORS配置允许远程访问
- 建议在生产环境中添加认证和授权机制

## 数据库位置

SQLite数据库文件位置：`/data/jj/proj/hoorii/hoorii.db`

你可以使用任何SQLite客户端查看和管理数据：
```bash
# 使用SQLite命令行
sqlite3 hoorii.db

# 查看所有表
.tables

# 查看用户
SELECT * FROM users;

# 查看设备
SELECT * FROM devices;
```

## 架构说明

```
┌─────────────────────┐
│  管理面板 (HTML)     │
│  admin_panel.html   │
└──────────┬──────────┘
           │ HTTP/REST
           ▼
┌─────────────────────┐
│  API服务器          │
│  FastAPI (Python)   │
└──────────┬──────────┘
           │ SQLAlchemy
           ▼
┌─────────────────────┐
│  数据库             │
│  SQLite            │
└─────────────────────┘
```

## 下一步

- 📖 阅读完整文档：[ADMIN_PANEL_GUIDE.md](ADMIN_PANEL_GUIDE.md)
- 🔧 了解API接口：访问 http://localhost:10020/docs（Swagger文档）
- 💡 查看项目架构：阅读根目录下的文档

## 技术支持

如有问题，请：
1. 查看日志文件：`api_server.log`
2. 检查数据库：使用SQLite工具
3. 查看浏览器控制台错误
4. 参考完整文档

---

祝使用愉快！ 🎉

