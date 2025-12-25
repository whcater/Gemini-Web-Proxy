# 环境配置指南

本文档详细说明如何使用 `uv` 工具管理 Python 版本和项目环境。

## 🚀 快速开始（推荐）

如果你已经安装了 **Node.js**，可以使用我们提供的跨平台脚本，一键完成所有配置：

```bash
# 一键配置环境（安装 uv、Python 3.12、创建虚拟环境、安装依赖）
npm run setup

# 启动 Chrome CDP（可选）
npm run start-chrome        # 普通模式
npm run start-chrome-cdp    # CDP 无痕模式

# 启动服务
npm start
```

这些脚本会自动处理 Windows、macOS、Linux 的差异，无需手动执行不同的命令。

---

## 为什么使用 uv？

`uv` 是一个极速的 Python 包管理器和环境管理工具，相比传统的 pip + venv 方案有以下优势：

- **极快的速度**：比 pip 快 10-100 倍
- **统一管理**：同时管理 Python 版本和虚拟环境
- **更好的依赖解析**：避免依赖冲突
- **跨平台支持**：Windows、macOS、Linux 统一体验

## Python 版本要求

本项目推荐使用 **Python 3.11** 或 **Python 3.12**。

**不支持 Python 3.14+**，因为某些依赖（如 greenlet）尚未完全支持新版本的内部 API。

---

## 配置方式选择

### 方式 1：使用 Node.js 脚本（推荐）

**优点**：
- ✅ 跨平台统一命令
- ✅ 自动处理系统差异
- ✅ 更简洁易用
- ✅ 无需维护多个 .sh/.bat 文件

**前置要求**：安装 Node.js 14+ ([下载地址](https://nodejs.org/))

**使用方法**：
```bash
npm run setup          # 配置环境
npm run start-chrome   # 启动 Chrome（可选）
npm start              # 启动服务
```

### 方式 2：手动配置

如果你不想安装 Node.js，可以按照下面的操作系统特定指南手动配置。

---

## Windows 环境配置

### 1. 安装 uv

使用 PowerShell 安装：

```powershell
# 使用官方安装脚本
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

或者使用 pip 安装（如果你已经有 Python）：

```powershell
pip install uv
```

### 2. 使用 uv 安装 Python 3.12

```powershell
# 安装 Python 3.12
uv python install 3.12

# 查看已安装的 Python 版本
uv python list
```

### 3. 创建虚拟环境

```powershell
# 进入项目目录
cd C:\dev\lab\Gemini-Web-Proxy

# 删除旧的虚拟环境（如果存在）
Remove-Item -Recurse -Force .venv

# 使用 uv 创建基于 Python 3.12 的虚拟环境
uv venv --python 3.12

# 激活虚拟环境
.venv\Scripts\activate
```

### 4. 安装项目依赖

```powershell
# 使用 uv pip 安装依赖（比 pip 快得多）
uv pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 5. 验证安装

```powershell
# 检查 Python 版本
python --version
# 应该显示: Python 3.12.x

# 检查已安装的包
uv pip list

# 测试运行
python main.py
```

---

## macOS 环境配置

### 1. 安装 uv

```bash
# 使用官方安装脚本
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 Homebrew
brew install uv
```

### 2. 使用 uv 安装 Python 3.12

```bash
# 安装 Python 3.12
uv python install 3.12

# 查看已安装的 Python 版本
uv python list
```

### 3. 创建虚拟环境

```bash
# 进入项目目录
cd ~/path/to/Gemini-Web-Proxy

# 删除旧的虚拟环境（如果存在）
rm -rf .venv

# 使用 uv 创建基于 Python 3.12 的虚拟环境
uv venv --python 3.12

# 激活虚拟环境
source .venv/bin/activate
```

### 4. 安装项目依赖

```bash
# 使用 uv pip 安装依赖
uv pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 5. 验证安装

```bash
# 检查 Python 版本
python --version
# 应该显示: Python 3.12.x

# 检查已安装的包
uv pip list

# 测试运行
python main.py
```

---

## Linux 环境配置

### 1. 安装 uv

```bash
# 使用官方安装脚本
curl -LsSf https://astral.sh/uv/install.sh | sh

# 重新加载 shell 配置
source ~/.bashrc  # 或 ~/.zshrc
```

### 2. 使用 uv 安装 Python 3.12

```bash
# 安装 Python 3.12
uv python install 3.12

# 查看已安装的 Python 版本
uv python list
```

### 3. 创建虚拟环境

```bash
# 进入项目目录
cd ~/path/to/Gemini-Web-Proxy

# 删除旧的虚拟环境（如果存在）
rm -rf .venv

# 使用 uv 创建基于 Python 3.12 的虚拟环境
uv venv --python 3.12

# 激活虚拟环境
source .venv/bin/activate
```

### 4. 安装项目依赖

```bash
# 使用 uv pip 安装依赖
uv pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium

# 如果遇到依赖问题，安装系统依赖
playwright install-deps chromium
```

### 5. 验证安装

```bash
# 检查 Python 版本
python --version
# 应该显示: Python 3.12.x

# 检查已安装的包
uv pip list

# 测试运行
python main.py
```

---

## 常见问题

### Q1: uv 找不到命令

**解决方案：**

重新加载 shell 配置或重启终端：

```bash
# Bash
source ~/.bashrc

# Zsh
source ~/.zshrc

# 或直接重启终端
```

### Q2: greenlet 编译失败

**原因：** Python 版本太新（如 3.14+）或太旧（< 3.8）

**解决方案：**

使用推荐的 Python 3.11 或 3.12：

```bash
# 删除当前虚拟环境
rm -rf .venv  # macOS/Linux
Remove-Item -Recurse -Force .venv  # Windows

# 重新创建虚拟环境
uv venv --python 3.12
```

### Q3: 如何切换 Python 版本？

```bash
# 列出可用的 Python 版本
uv python list

# 安装其他版本
uv python install 3.11

# 创建使用特定版本的虚拟环境
uv venv --python 3.11
```

### Q4: 如何更新依赖？

```bash
# 激活虚拟环境后
uv pip install --upgrade -r requirements.txt

# 或更新单个包
uv pip install --upgrade flask
```

### Q5: uv 和 pip 的区别？

- `uv pip` 是 uv 提供的 pip 兼容接口，速度更快
- 在虚拟环境中可以直接使用 `pip`，但推荐使用 `uv pip`
- 所有 pip 命令都可以替换为 `uv pip`

---

## uv 常用命令速查

```bash
# Python 版本管理
uv python list              # 列出已安装的 Python 版本
uv python install 3.12      # 安装 Python 3.12
uv python install 3.11      # 安装 Python 3.11

# 虚拟环境管理
uv venv                     # 创建虚拟环境（使用默认 Python）
uv venv --python 3.12       # 创建使用 Python 3.12 的虚拟环境
uv venv .venv               # 指定虚拟环境目录名称

# 包管理
uv pip install package      # 安装包
uv pip install -r requirements.txt  # 安装依赖文件
uv pip list                 # 列出已安装的包
uv pip freeze               # 导出已安装的包
uv pip uninstall package    # 卸载包
uv pip install --upgrade package  # 更新包

# 项目管理
uv run python main.py       # 自动创建/激活环境并运行脚本
uv sync                     # 同步依赖（需要 pyproject.toml）
```

---

## 进阶：使用 pyproject.toml 管理项目

如果你想更现代化的项目管理，可以创建 `pyproject.toml` 文件：

```toml
[project]
name = "gemini-web-proxy"
version = "1.0.0"
description = "Gemini to OpenAI API Proxy"
requires-python = ">=3.11,<3.14"
dependencies = [
    "flask==3.0.0",
    "playwright==1.40.0",
    "aiohttp==3.9.1",
    "html2text==2024.2.26",
    "requests==2.31.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

然后使用：

```bash
# 自动创建环境并安装依赖
uv sync

# 运行脚本（自动激活环境）
uv run python main.py
```

---

## 参考资源

- [uv 官方文档](https://docs.astral.sh/uv/)
- [uv GitHub 仓库](https://github.com/astral-sh/uv)
- [Python 版本支持策略](https://devguide.python.org/versions/)
