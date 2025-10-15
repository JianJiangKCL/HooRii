# 🎯 HooRii 用户管理面板

欢迎使用HooRii智能家居用户管理系统！

## 🚀 三步启动

### 1. 初始化示例数据
```bash
./init_sample_data.py
```

### 2. 启动管理面板
```bash
./start_admin_panel.sh
```

### 3. 开始使用
浏览器会自动打开管理面板 🌐

## 📚 文档导航

| 文档 | 说明 |
|------|------|
| **[START_HERE.md](START_HERE.md)** | ⭐ 从这里开始 - 最快速的入门指南 |
| **[QUICK_START_ADMIN.md](QUICK_START_ADMIN.md)** | 5分钟详细教程 |
| **[ADMIN_PANEL_GUIDE.md](ADMIN_PANEL_GUIDE.md)** | 完整使用指南 |
| **[USER_MANAGEMENT_SUMMARY.md](USER_MANAGEMENT_SUMMARY.md)** | 技术实现总结 |
| **[README_USER_MANAGEMENT.md](README_USER_MANAGEMENT.md)** | 项目说明 |

## ✨ 核心功能

- 👥 **用户管理** - 创建、编辑、删除用户
- 🏠 **设备管理** - 管理智能家居设备
- 🔗 **权限配置** - 为用户分配设备访问权限
- 📊 **统计查看** - 查看用户和设备使用情况
- 🎨 **美观界面** - 现代化的Web管理面板

## 📦 文件说明

```
user_control_interface/
├── admin_panel.html           # Web管理面板（主界面）
├── start_admin_panel.sh       # 启动脚本
├── stop_admin_panel.sh        # 停止脚本
├── init_sample_data.py        # 示例数据初始化
└── *.md                       # 各种文档
```

## 🛑 停止服务

```bash
./stop_admin_panel.sh
```

## 💡 快速提示

- **API地址**: http://localhost:10020
- **API文档**: http://localhost:10020/docs
- **数据库**: /data/jj/proj/hoorii/data/hoorii.db
- **日志文件**: api_server.log

## ❓ 遇到问题？

1. 查看 [START_HERE.md](START_HERE.md) 的故障排除部分
2. 检查 `api_server.log` 日志文件
3. 确认API服务器是否运行: `lsof -i :10020`

---

**开始使用**: 运行 `./init_sample_data.py` 然后 `./start_admin_panel.sh` 🚀

