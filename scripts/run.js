#!/usr/bin/env node

/**
 * 跨平台服务启动脚本
 * 自动检测并安装依赖，然后启动服务
 */

const {
  getOS,
  commandExists,
  execCommand,
  execCommandSync,
  getPythonCommand,
  printSuccess,
  printError,
  printWarning,
  printInfo
} = require('./utils');

const path = require('path');
const fs = require('fs');

async function main() {
  console.log('==============================');
  console.log('  Gemini Web Proxy');
  console.log('==============================');
  console.log('');

  try {
    // 步骤 1: 检查 Python
    checkPython();

    // 步骤 2: 检查依赖
    await checkDependencies();

    // 步骤 3: 启动服务
    await startService();

  } catch (error) {
    printError(`启动失败: ${error.message}`);
    process.exit(1);
  }
}

/**
 * 检查 Python 是否安装
 */
function checkPython() {
  console.log('[检查] Python...');

  try {
    const pythonCmd = getPythonCommand();
    const version = execCommandSync(`${pythonCmd} --version`);

    printSuccess(`Python 已安装: ${version}`);
    console.log('');

    return pythonCmd;
  } catch (error) {
    printError('未找到 Python，请先安装 Python 3.11 或 3.12');
    console.log('');
    printInfo('使用 uv 安装：npm run setup');
    printInfo('或参考文档：ENVIRONMENT_SETUP.md');
    throw error;
  }
}

/**
 * 检查依赖是否安装
 */
async function checkDependencies() {
  console.log('[检查] 依赖包...');

  const os = getOS();
  const pythonCmd = getPythonCommand();

  // 检查 flask 是否安装
  const checkCmd = os === 'windows'
    ? `${pythonCmd} -c "import flask" 2>nul`
    : `${pythonCmd} -c "import flask" 2>/dev/null`;

  const flaskInstalled = execCommandSync(checkCmd) !== null;

  if (flaskInstalled) {
    printSuccess('依赖已安装');
    console.log('');
    return;
  }

  // 依赖未安装，开始安装
  printWarning('检测到依赖未安装，开始自动安装...');
  console.log('');

  await installDependencies();
}

/**
 * 安装依赖
 */
async function installDependencies() {
  console.log('[安装] Python 依赖...');

  // 检查是否有虚拟环境
  const venvPath = path.join(process.cwd(), '.venv');
  const hasVenv = fs.existsSync(venvPath);

  if (hasVenv && commandExists('uv')) {
    // 使用 uv 安装（更快）
    try {
      await execCommand('uv', ['pip', 'install', '-r', 'requirements.txt']);
      printSuccess('Python 依赖安装完成');
    } catch (error) {
      throw new Error('依赖安装失败，请运行: npm run setup');
    }
  } else {
    // 使用 pip 安装
    const pythonCmd = getPythonCommand();
    const pipCmd = pythonCmd === 'python3' ? 'pip3' : 'pip';

    try {
      await execCommand(pipCmd, ['install', '-r', 'requirements.txt']);
      printSuccess('Python 依赖安装完成');
    } catch (error) {
      throw new Error('依赖安装失败');
    }
  }

  console.log('');

  // 安装 Playwright 浏览器
  console.log('[安装] Playwright 浏览器...');

  try {
    await execCommand('playwright', ['install', 'chromium']);
    printSuccess('Playwright 浏览器安装完成');
  } catch (error) {
    printWarning('Playwright 安装失败，部分功能可能无法使用');
  }

  console.log('');
  printSuccess('依赖安装完成！');
  console.log('');
}

/**
 * 启动服务
 */
async function startService() {
  console.log('==============================');
  console.log('[启动] Gemini Proxy 服务...');
  console.log('==============================');
  console.log('');

  printInfo('按 Ctrl+C 可停止服务');
  console.log('');

  console.log('[配置信息]');
  console.log('   API Base URL: http://127.0.0.1:5000/v1');
  console.log('   Model: gemini-pro');
  console.log('');
  console.log('==============================');
  console.log('');

  // 启动主程序
  const pythonCmd = getPythonCommand();

  try {
    await execCommand(pythonCmd, ['main.py']);
  } catch (error) {
    // Ctrl+C 会触发错误，这是正常的
    if (error.message.includes('130') || error.message.includes('SIGINT')) {
      console.log('');
      printInfo('服务已停止');
      process.exit(0);
    }
    throw error;
  }
}

// 运行主函数
main().catch((error) => {
  if (error.message && !error.message.includes('130')) {
    printError(error.message);
  }
  process.exit(1);
});
