# 快速命令参考

## Node.js 跨平台脚本（推荐）

```bash
# 环境配置
npm run setup              # 一键配置环境（uv + Python 3.12 + 依赖）

# 启动服务
npm start                  # 启动 Gemini Proxy 服务

# 启动 Chrome
npm run start-chrome       # 普通模式（使用默认 Profile）
npm run start-chrome-cdp   # CDP 无痕模式（临时 Profile）
```

## 传统脚本（特定平台）

### Windows
```powershell
# 环境配置
.\setup_uv.bat

# 启动服务
run.bat
```

### macOS/Linux
```bash
# 环境配置
./setup_uv.sh

# 启动服务
./run.sh

# 启动 Chrome CDP
./start_chrome_cdp.sh
```

## 手动命令

### 使用 uv
```bash
# 安装 Python 3.12
uv python install 3.12

# 创建虚拟环境
uv venv --python 3.12

# 激活虚拟环境
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux

# 安装依赖
uv pip install -r requirements.txt

# 安装 Playwright
playwright install chromium
```

### 使用 pip
```bash
# 安装依赖
pip install -r requirements.txt

# 安装 Playwright
playwright install chromium
```

## API 测试

```bash
# 健康检查
curl http://127.0.0.1:5000/health

# 列出模型
curl http://127.0.0.1:5000/v1/models

# 发送聊天请求
curl http://127.0.0.1:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini-pro","messages":[{"role":"user","content":"你好"}],"stream":false}'
```

## 故障排查

```bash
# 检查 Python 版本
python --version

# 检查依赖
pip list

# 检查 CDP 连接
curl http://127.0.0.1:9222/json/version

# 查看 uv 版本
uv --version

# 重新配置环境
npm run setup
```

## 文档导航

- [README.md](README.md) - 项目主文档
- [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) - 环境配置详细指南
- [SCRIPTS_README.md](SCRIPTS_README.md) - Node.js 脚本详细说明
- [FUNCTION_CALLING_README.md](FUNCTION_CALLING_README.md) - Function Calling 功能
