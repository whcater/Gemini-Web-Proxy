#!/bin/bash
# 启动 Chrome 并开启远程调试端口 - 修复版

# 关闭所有 Chrome 进程
echo "关闭现有 Chrome 进程..."
killall "Google Chrome" 2>/dev/null
sleep 2

# 创建临时用户数据目录（确保端口正确开启）
TEMP_DIR="/tmp/chrome-cdp-profile"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

echo "启动 Chrome 并开启远程调试..."
echo "使用临时Profile: $TEMP_DIR"

# 启动Chrome - 使用临时Profile确保端口开启
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --remote-debugging-port=9222 \
    --remote-debugging-address=127.0.0.1 \
    --user-data-dir="$TEMP_DIR" \
    --no-first-run \
    --no-default-browser-check \
    --disable-background-timer-throttling \
    --disable-backgrounding-occluded-windows \
    --disable-renderer-backgrounding \
    https://gemini.google.com/app &

sleep 2

echo "Chrome 已启动"
echo "远程调试端口: 9222"
echo "临时Profile: $TEMP_DIR"
echo ""
echo "测试连接中..."
sleep 1

# 测试连接
if curl -s http://127.0.0.1:9222/json/version > /dev/null 2>&1; then
    echo "✅ CDP端口已开启！"
    echo ""
    echo "请在Chrome中："
    echo "1. 登录 Google 账号"
    echo "2. 确保能访问 Gemini"
    echo "3. 然后运行: python main.py"
else
    echo "❌ CDP端口未开启，请检查Chrome进程"
fi