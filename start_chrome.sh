#!/bin/bash
# 启动 Chrome 并开启远程调试端口

# 关闭所有 Chrome 进程
echo "关闭现有 Chrome 进程..."
killall "Google Chrome" 2>/dev/null
sleep 1

# 使用指定的 Profile 启动 Chrome
echo "启动 Chrome 并开启远程调试..."
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --remote-debugging-port=9222 \
    --user-data-dir="/Users/ylp/Library/Application Support/Google/Chrome" \
    --profile-directory="Profile 2" \
    --no-first-run \
    --no-default-browser-check \
    https://gemini.google.com/app &

echo "Chrome 已启动"
echo "远程调试端口: 9222"
echo "Profile: Profile 2"
echo ""
echo "请在Chrome中："
echo "1. 登录 Google 账号（如果未登录）"
echo "2. 确保能访问 Gemini"
echo "3. 然后运行: python main.py"
echo ""
echo "测试连接: curl http://127.0.0.1:9222/json/version"