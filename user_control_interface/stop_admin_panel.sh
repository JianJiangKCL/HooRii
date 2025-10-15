#!/bin/bash

# HooRii 管理面板停止脚本

echo "🛑 停止 HooRii API 服务器..."
echo ""

API_PORT=10020

# 查找运行在指定端口的进程
PID=$(lsof -t -i:$API_PORT)

if [ -z "$PID" ]; then
    echo "ℹ️  没有发现运行在端口 $API_PORT 的服务"
else
    echo "📍 找到进程 PID: $PID"
    echo "🔪 正在终止进程..."
    kill $PID
    
    # 等待进程结束
    sleep 2
    
    # 检查进程是否已终止
    if lsof -Pi :$API_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "⚠️  进程未能正常终止，尝试强制终止..."
        kill -9 $PID
        sleep 1
    fi
    
    # 最终检查
    if lsof -Pi :$API_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "❌ 无法停止服务"
    else
        echo "✅ API服务器已停止"
    fi
fi

echo ""
echo "完成！"

