#!/bin/bash

# HooRii 管理面板启动脚本

echo "🏠 HooRii 用户管理面板启动脚本"
echo "================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python3 未安装"
    echo "请先安装 Python 3.7 或更高版本"
    exit 1
fi

# 获取脚本所在目录和项目根目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 检查API服务器是否已经在运行
API_PORT=10020
if lsof -Pi :$API_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "✅ API服务器已在端口 $API_PORT 上运行"
else
    echo "🚀 启动API服务器..."
    
    # 进入项目根目录
    cd "$PROJECT_ROOT"
    
    # 指定数据库到 data/hoorii.db
    export DATABASE_URL=sqlite:////data/jj/proj/hoorii/data/hoorii.db
    echo "   使用数据库: $DATABASE_URL"

    # 检查虚拟环境
    if [ -d "venv" ]; then
        echo "   激活虚拟环境..."
        source venv/bin/activate
    fi
    
    # 启动API服务器（后台运行）——使用uvicorn CLI并指定导入路径
    nohup python3 -m uvicorn src.api.server:app --host 0.0.0.0 --port $API_PORT --reload > user_control_interface/api_server.log 2>&1 &
    API_PID=$!
    echo "   API服务器已启动 (PID: $API_PID)"
    echo "   日志文件: api_server.log"
    
    # 等待服务器启动
    echo "   等待服务器启动..."
    # 最长等待10秒，期间轮询端口
    for i in $(seq 1 10); do
        if lsof -Pi :$API_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
            break
        fi
        sleep 1
    done
    
    # 检查服务器是否成功启动
    if lsof -Pi :$API_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "   ✅ API服务器启动成功"
    else
        echo "   ❌ API服务器启动失败，请查看日志: api_server.log"
        exit 1
    fi
fi

echo ""
echo "📊 正在打开管理面板..."
echo ""

# 回到脚本目录打开HTML文件
cd "$SCRIPT_DIR"

# 检查并打开浏览器
if command -v xdg-open &> /dev/null; then
    xdg-open admin_panel.html
elif command -v open &> /dev/null; then
    open admin_panel.html
elif command -v start &> /dev/null; then
    start admin_panel.html
else
    echo "⚠️  无法自动打开浏览器"
    echo "请手动打开: $SCRIPT_DIR/admin_panel.html"
fi

echo ""
echo "================================"
echo "✅ 启动完成！"
echo ""
echo "📋 信息:"
echo "   API服务器: http://localhost:$API_PORT"
echo "   管理面板: file://$SCRIPT_DIR/admin_panel.html"
echo "   日志文件: $SCRIPT_DIR/api_server.log"
echo ""
echo "📝 使用说明:"
echo "   - 管理面板已在浏览器中打开"
echo "   - API服务器运行在后台"
echo ""
echo "🛑 停止服务:"
echo "   运行: cd $SCRIPT_DIR && ./stop_admin_panel.sh"
echo "   或者: kill \$(lsof -t -i:$API_PORT)"
echo ""

