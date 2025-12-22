#!/bin/bash

echo "========================================"
echo "  Gemini Web Proxy - 环境配置脚本"
echo "  使用 uv 管理 Python 版本"
echo "========================================"
echo ""

# 检测操作系统
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
else
    OS="Linux"
fi

echo "检测到系统: $OS"
echo ""

# 检查 uv 是否已安装
if ! command -v uv &> /dev/null; then
    echo "[1/4] 未检测到 uv，正在安装..."
    echo ""
    curl -LsSf https://astral.sh/uv/install.sh | sh

    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ uv 安装失败，请手动安装后重试"
        echo "   参考文档: ENVIRONMENT_SETUP.md"
        exit 1
    fi

    # 重新加载 shell 配置
    if [ -f ~/.bashrc ]; then
        source ~/.bashrc
    elif [ -f ~/.zshrc ]; then
        source ~/.zshrc
    fi

    echo ""
    echo "✅ uv 安装成功"
    echo ""
else
    echo "[1/4] ✅ uv 已安装"
    echo ""
fi

# 安装 Python 3.12
echo "[2/4] 正在检查 Python 3.12..."
uv python install 3.12

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Python 3.12 安装失败"
    exit 1
fi

echo "✅ Python 3.12 就绪"
echo ""

# 删除旧的虚拟环境
if [ -d ".venv" ]; then
    echo "[3/4] 检测到旧的虚拟环境，正在删除..."
    rm -rf .venv
    echo "✅ 旧环境已清理"
    echo ""
else
    echo "[3/4] 准备创建虚拟环境..."
    echo ""
fi

# 创建新的虚拟环境
echo "正在创建基于 Python 3.12 的虚拟环境..."
uv venv --python 3.12

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 虚拟环境创建失败"
    exit 1
fi

echo "✅ 虚拟环境创建成功"
echo ""

# 激活虚拟环境并安装依赖
echo "[4/4] 正在安装项目依赖..."
source .venv/bin/activate
uv pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 依赖安装失败"
    exit 1
fi

echo "✅ 依赖安装成功"
echo ""

# 安装 Playwright 浏览器
echo "正在安装 Playwright Chromium..."
playwright install chromium

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Playwright 安装失败，请稍后手动运行:"
    echo "   playwright install chromium"

    if [ "$OS" == "Linux" ]; then
        echo ""
        echo "如果是依赖问题，可以尝试:"
        echo "   playwright install-deps chromium"
    fi
    echo ""
else
    echo "✅ Playwright Chromium 安装成功"
    echo ""
fi

# 显示 Python 版本
echo "========================================"
echo "  环境配置完成！"
echo "========================================"
echo ""
python --version
echo ""
echo "💡 下一步："
echo "   1. 激活虚拟环境: source .venv/bin/activate"
echo "   2. 运行服务: python main.py"
echo "   3. 或直接运行: ./run.sh"
echo ""
echo "📖 详细文档请查看: ENVIRONMENT_SETUP.md"
echo ""
