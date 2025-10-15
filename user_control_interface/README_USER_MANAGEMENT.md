# 🏠 HooRii 用户管理面板

> 一个功能完整、美观易用的智能家居用户管理系统

## ✨ 功能特性

- 👥 **用户管理**: 创建、编辑、查看、删除用户
- 🏠 **设备管理**: 管理智能家居设备
- 🔗 **权限配置**: 为用户分配设备访问权限
- 📊 **统计信息**: 查看用户和设备使用情况
- 🎨 **现代UI**: 美观的界面设计，流畅的交互体验

## 🚀 快速开始（3步上手）

### 第一步：初始化示例数据

```bash
cd /data/jj/proj/hoorii/user_control_interface
./init_sample_data.py
```

这会创建一些示例用户和设备，方便你快速体验功能。

### 第二步：启动管理面板

```bash
./start_admin_panel.sh
```

这个脚本会：
- 🚀 自动启动API服务器
- 🌐 在浏览器中打开管理面板

### 第三步：开始管理

管理面板会自动打开，你可以：
- 查看和管理用户
- 添加和配置设备
- 为用户分配设备权限

## 📸 界面预览

管理面板包含三个主要功能模块：

1. **👥 用户管理**: 查看所有用户，管理用户信息
2. **🏠 设备管理**: 管理智能家居设备
3. **🔗 用户设备配置**: 为用户分配设备和设置权限

## 📚 文档

- [📖 完整使用指南](ADMIN_PANEL_GUIDE.md) - 详细的功能说明和使用方法
- [🚀 快速开始指南](QUICK_START_ADMIN.md) - 5分钟快速上手教程
- [📋 实现总结](USER_MANAGEMENT_SUMMARY.md) - 技术实现和架构说明

## 💡 使用示例

### 创建新用户

1. 打开管理面板
2. 点击"用户管理"标签
3. 点击"+ 添加用户"按钮
4. 填写用户信息并保存

### 为用户添加设备

1. 切换到"用户设备配置"标签
2. 选择用户
3. 点击"+ 为用户添加设备"
4. 选择设备并配置选项

### 创建新设备

1. 切换到"设备管理"标签
2. 点击"+ 添加设备"
3. 填写设备信息
4. 选择设备类型（灯光、电视、音响等）

## 🛠️ 技术栈

- **前端**: HTML5 + CSS3 + JavaScript (零依赖)
- **后端**: Python + FastAPI
- **数据库**: SQLite + SQLAlchemy ORM
- **API**: RESTful API

## 📦 主要文件

```
hoorii/user_control_interface/
├── admin_panel.html           # Web管理面板
├── start_admin_panel.sh       # 启动脚本
├── stop_admin_panel.sh        # 停止脚本
├── init_sample_data.py        # 示例数据初始化
├── QUICK_START_ADMIN.md       # 快速开始指南
├── ADMIN_PANEL_GUIDE.md       # 详细使用指南
└── USER_MANAGEMENT_SUMMARY.md # 技术实现总结
```

## 🎯 常用命令

```bash
# 启动管理面板（包含API服务器）
./start_admin_panel.sh

# 停止API服务器
./stop_admin_panel.sh

# 初始化示例数据
./init_sample_data.py

# 查看API服务器日志
tail -f api_server.log

# 测试API是否运行
curl http://localhost:10020/health
```

## 📞 API访问

- **API地址**: http://localhost:10020
- **API文档**: http://localhost:10020/docs (Swagger UI)
- **管理面板**: 打开 `admin_panel.html`

## ❓ 常见问题

### Q: 如何修改API服务器地址？
A: 在管理面板右上角的输入框中修改API地址。

### Q: 如何重置数据？
A: 删除 `hoorii.db` 文件，然后重新运行 `./init_sample_data.py`

### Q: 管理面板显示"无法连接"？
A: 确认API服务器是否已启动：`lsof -i :10020`

### Q: 如何查看详细日志？
A: 查看 `api_server.log` 文件

## 🔄 更新日志

**v1.0.0** (2025-10-15)
- ✅ 完整的用户管理功能
- ✅ 设备管理功能
- ✅ 用户设备关联配置
- ✅ Web管理面板
- ✅ 自动化启动脚本
- ✅ 示例数据初始化

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

请参考项目主LICENSE文件

---

**享受使用 HooRii 用户管理面板！** 🎉

如有问题，请查看[详细使用指南](ADMIN_PANEL_GUIDE.md)或[快速开始指南](QUICK_START_ADMIN.md)。

