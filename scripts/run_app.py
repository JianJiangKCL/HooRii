#!/usr/bin/env python3
"""
运行智能家居助手应用
"""
import subprocess
import sys

print("🚀 启动智能家居助手...")
print("-" * 50)

# 运行主程序，过滤掉 OpenTelemetry 错误
try:
    # 使用 grep -v 过滤掉 OpenTelemetry 错误信息
    process = subprocess.Popen(
        [sys.executable, "/data/jj/proj/hoorii/src/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    for line in process.stdout:
        # 过滤掉 OpenTelemetry 错误
        if "opentelemetry.exporter" not in line and "Failed to export" not in line:
            print(line, end='')
    
    process.wait()
    
except KeyboardInterrupt:
    print("\n\n👋 程序已退出")
except Exception as e:
    print(f"\n❌ 错误: {e}")
