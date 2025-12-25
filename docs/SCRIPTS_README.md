# Node.js 跨平台脚本说明

本项目提供了一套基于 Node.js 的跨平台脚本，可以在 Windows、macOS、Linux 上使用统一的命令进行环境配置和服务管理。

## 为什么使用 Node.js 脚本？

相比传统的 `.sh` 和 `.bat` 脚本：

- ✅ **跨平台统一**：一套代码，所有平台都能运行
- ✅ **无需维护多个脚本**：不需要分别维护 Windows 和 Unix 的脚本
- ✅ **更好的错误处理**：提供更友好的错误信息和颜色输出
- ✅ **自动检测系统**：自动识别操作系统并使用对应的命令
- ✅ **更容易扩展**：使用 JavaScript 可以轻松添加新功能

## 前置要求

- **Node.js 14+**（[下载地址](https://nodejs.org/)）
- 无需安装额外的 npm 包（所有脚本都使用 Node.js 内置模块）

## 可用命令

### 1. 环境配置

```bash
npm run setup
```

**功能**：
- 自动检测并安装 `uv` 工具
- 安装 Python 3.12
- 创建虚拟环境
- 安装项目依赖
- 安装 Playwright Chromium

**跨平台支持**：
- Windows：使用 PowerShell 安装 uv
- macOS/Linux：使用 curl 安装 uv

---

### 2. 启动服务

```bash
npm start
```

**功能**：
- 检查 Python 是否安装
- 检查依赖是否完整（如果缺失会自动安装）
- 启动 Flask 服务

**等价命令**：
- `python main.py`
- `./run.sh` (macOS/Linux)
- `run.bat` (Windows)

---

### 3. 启动 Chrome（普通模式）

```bash
npm run start-chrome
```

**功能**：
- 关闭现有 Chrome 进程
- 使用默认用户 Profile 启动 Chrome
- 开启远程调试端口 (9222)
- 自动打开 Gemini 网页
- 验证 CDP 连接

**适用场景**：
- 需要使用已登录的 Google 账号
- 希望保留浏览历史和 Cookie

---

### 4. 启动 Chrome（CDP 无痕模式）

```bash
npm run start-chrome-cdp
```

**功能**：
- 关闭现有 Chrome 进程
- 使用临时 Profile 启动 Chrome（无痕模式）
- 开启远程调试端口 (9222)
- 自动打开 Gemini 网页
- 验证 CDP 连接

**适用场景**：
- 需要使用独立的临时环境
- 不希望影响主账号的浏览数据
- 测试和调试

**注意**：无痕模式下登录信息不会被保存

---

## 脚本文件说明

```
scripts/
├── utils.js          # 工具函数库
│   ├── getOS()                    # 检测操作系统
│   ├── commandExists()            # 检查命令是否存在
│   ├── execCommand()              # 执行命令并实时输出
│   ├── getChromeUserDataDir()     # 获取 Chrome 用户目录
│   ├── getChromePath()            # 获取 Chrome 可执行文件路径
│   ├── killChromeProcesses()      # 关闭 Chrome 进程
│   ├── checkPort()                # 检查端口是否开放
│   └── printSuccess/Error/...     # 彩色输出函数
│
├── setup.js          # 环境配置脚本
│   └── 自动安装 uv、Python、依赖
│
├── start-chrome.js   # Chrome 启动脚本
│   ├── 支持普通模式和 CDP 模式
│   └── 跨平台 Chrome 路径检测
│
└── run.js            # 服务启动脚本
    └── 自动检查依赖并启动服务
```

## 使用示例

### 完整的工作流程

```bash
# 1. 首次配置环境
npm run setup

# 2. 启动 Chrome（可选）
npm run start-chrome-cdp

# 3. 在 Chrome 中登录 Google 账号并访问 Gemini

# 4. 启动服务
npm start
```

### 日常使用

```bash
# 直接启动服务（会自动检查依赖）
npm start
```

### 重新配置环境

```bash
# 如果遇到 Python 版本问题或依赖冲突
npm run setup
```

---

## 技术细节

### 跨平台路径处理

脚本会自动检测操作系统并使用正确的路径：

- **Chrome 用户目录**：
  - Windows: `C:\Users\{用户}\AppData\Local\Google\Chrome\User Data`
  - macOS: `~/Library/Application Support/Google/Chrome`
  - Linux: `~/.config/google-chrome`

- **Chrome 可执行文件**：
  - Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe`
  - macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
  - Linux: `/usr/bin/google-chrome` 或 `/usr/bin/chromium`

### 进程管理

- **Windows**：使用 `taskkill /F /IM chrome.exe`
- **macOS/Linux**：使用 `killall "Google Chrome"`

### 命令执行

- 使用 Node.js 的 `child_process.spawn()` 实现实时输出
- 所有命令都有超时和错误处理
- 支持 `stdio: 'inherit'` 继承标准输入输出

---

## 常见问题

### Q1: 为什么不使用 npm 包？

**A:** 为了简化安装流程，所有脚本都使用 Node.js 内置模块（`child_process`, `fs`, `path`, `os`, `http`, `net`），无需安装任何 npm 依赖。

### Q2: 脚本可以离线运行吗？

**A:** `setup.js` 需要网络连接来下载 uv 和 Python，但其他脚本（`run.js`, `start-chrome.js`）可以离线运行（假设依赖已安装）。

### Q3: 如何自定义 Chrome 启动参数？

**A:** 编辑 `scripts/start-chrome.js` 文件，在 `prepareChromeArgs()` 函数中修改参数数组。

例如，添加代理：
```javascript
args.push('--proxy-server=127.0.0.1:8080');
```

### Q4: 如何更改 CDP 端口？

**A:** 编辑 `scripts/start-chrome.js`，修改顶部的 `CDP_PORT` 常量：
```javascript
const CDP_PORT = 9223; // 修改为你想要的端口
```

### Q5: Windows PowerShell 执行策略错误

**A:** 如果遇到 PowerShell 执行策略错误，运行：
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

---

## 扩展开发

### 添加新的脚本

1. 在 `scripts/` 目录创建新的 `.js` 文件
2. 引入 `utils.js` 中的工具函数
3. 在 `package.json` 的 `scripts` 中添加新命令

示例：
```javascript
// scripts/my-script.js
#!/usr/bin/env node

const { printSuccess, execCommand } = require('./utils');

async function main() {
  console.log('Running my custom script...');
  // 你的代码
  printSuccess('Done!');
}

main().catch(console.error);
```

```json
// package.json
{
  "scripts": {
    "my-command": "node scripts/my-script.js"
  }
}
```

### 使用 TypeScript（可选）

如果你想使用 TypeScript，可以：

1. 安装依赖：
```bash
npm install --save-dev typescript @types/node
```

2. 创建 `tsconfig.json`
3. 将 `.js` 文件重命名为 `.ts`
4. 使用 `ts-node` 或编译后运行

---

## 对比：Shell vs Node.js

| 特性 | Shell 脚本 | Node.js 脚本 |
|------|-----------|-------------|
| 跨平台 | ❌ 需要 .sh 和 .bat | ✅ 一套代码 |
| 语法统一 | ❌ Bash vs Batch 差异大 | ✅ JavaScript 统一 |
| 错误处理 | ⚠️ 较为简陋 | ✅ 完善的异常处理 |
| 代码复用 | ⚠️ 函数支持有限 | ✅ 模块化设计 |
| 调试体验 | ⚠️ 较为困难 | ✅ 易于调试 |
| 依赖要求 | ✅ 系统自带 | ⚠️ 需要安装 Node.js |
| 性能 | ✅ 原生执行 | ✅ 足够快 |

---

## 参考资源

- [Node.js 官方文档](https://nodejs.org/docs/)
- [child_process 模块](https://nodejs.org/api/child_process.html)
- [跨平台 Node.js 最佳实践](https://nodejs.org/en/docs/guides/)

---

## 贡献

如果你想改进这些脚本，欢迎提交 PR！

主要改进方向：
- 添加更多的错误处理
- 支持更多的配置选项
- 优化性能和用户体验
- 添加单元测试
