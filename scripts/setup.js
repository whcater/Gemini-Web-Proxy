#!/usr/bin/env node

/**
 * 跨平台环境配置脚本
 * 使用 uv 管理 Python 版本和依赖
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

const fs = require('fs');
const path = require('path');

async function main() {
  console.log('========================================');
  console.log('  Gemini Web Proxy - 环境配置');
  console.log('  使用 uv 管理 Python 版本');
  console.log('========================================');
  console.log('');

  const os = getOS();
  console.log(`检测到系统: ${os}`);
  console.log('');

  try {
    // 步骤 1: 检查/安装 uv
    await checkAndInstallUV();

    // 步骤 2: 安装 Python 3.12
    await installPython();

    // 步骤 3: 创建虚拟环境
    await createVirtualEnv();

    // 步骤 4: 安装依赖
    await installDependencies();

    // 步骤 5: 安装 Playwright
    await installPlaywright();

    // 显示完成信息
    showCompletionMessage();

  } catch (error) {
    printError(`配置失败: ${error.message}`);
    process.exit(1);
  }
}

/**
 * 检查并安装 uv
 */
async function checkAndInstallUV() {
  console.log('[1/5] 检查 uv...');

  if (commandExists('uv')) {
    printSuccess('uv 已安装');
    const version = execCommandSync('uv --version');
    console.log(`      版本: ${version}`);
    console.log('');
    return;
  }

  printWarning('未检测到 uv，正在安装...');
  console.log('');

  const os = getOS();

  try {
    if (os === 'windows') {
      // Windows: 使用 PowerShell 安装
      await execCommand('powershell', [
        '-ExecutionPolicy',
        'ByPass',
        '-c',
        'irm https://astral.sh/uv/install.ps1 | iex'
      ]);
    } else {
      // macOS/Linux: 使用 curl 安装
      await execCommand('sh', [
        '-c',
        'curl -LsSf https://astral.sh/uv/install.sh | sh'
      ]);
    }

    printSuccess('uv 安装成功');
    console.log('');
  } catch (error) {
    throw new Error(`uv 安装失败: ${error.message}\n请参考文档 ENVIRONMENT_SETUP.md 手动安装`);
  }
}

/**
 * 安装 Python 3.12
 */
async function installPython() {
  console.log('[2/5] 检查 Python 3.12...');

  try {
    await execCommand('uv', ['python', 'install', '3.12']);
    printSuccess('Python 3.12 就绪');
    console.log('');
  } catch (error) {
    throw new Error(`Python 3.12 安装失败: ${error.message}`);
  }
}

/**
 * 创建虚拟环境
 */
async function createVirtualEnv() {
  console.log('[3/5] 创建虚拟环境...');

  const venvPath = path.join(process.cwd(), '.venv');

  // 删除旧的虚拟环境
  if (fs.existsSync(venvPath)) {
    printWarning('检测到旧的虚拟环境，正在删除...');
    fs.rmSync(venvPath, { recursive: true, force: true });
    printSuccess('旧环境已清理');
  }

  console.log('正在创建基于 Python 3.12 的虚拟环境...');

  try {
    await execCommand('uv', ['venv', '--python', '3.12']);
    printSuccess('虚拟环境创建成功');
    console.log('');
  } catch (error) {
    throw new Error(`虚拟环境创建失败: ${error.message}`);
  }
}

/**
 * 安装项目依赖
 */
async function installDependencies() {
  console.log('[4/5] 安装项目依赖...');

  try {
    // 使用 uv pip 安装依赖
    await execCommand('uv', ['pip', 'install', '-r', 'requirements.txt']);
    printSuccess('依赖安装成功');
    console.log('');
  } catch (error) {
    throw new Error(`依赖安装失败: ${error.message}`);
  }
}

/**
 * 安装 Playwright 浏览器
 */
async function installPlaywright() {
  console.log('[5/5] 安装 Playwright Chromium...');

  const os = getOS();
  const activateScript = os === 'windows'
    ? path.join('.venv', 'Scripts', 'activate.bat')
    : path.join('.venv', 'bin', 'activate');

  try {
    // 在虚拟环境中安装 Playwright
    if (os === 'windows') {
      await execCommand('cmd', ['/c', `${activateScript} && playwright install chromium`]);
    } else {
      await execCommand('sh', ['-c', `source ${activateScript} && playwright install chromium`]);
    }

    printSuccess('Playwright Chromium 安装成功');
    console.log('');

    // Linux 可能需要额外的系统依赖
    if (os === 'linux') {
      printInfo('Linux 系统可能需要额外依赖，如遇问题请运行:');
      console.log('      playwright install-deps chromium');
      console.log('');
    }
  } catch (error) {
    printWarning('Playwright 安装失败，请稍后手动运行:');
    console.log('      playwright install chromium');
    console.log('');
  }
}

/**
 * 显示完成信息
 */
function showCompletionMessage() {
  const os = getOS();

  console.log('========================================');
  console.log('  环境配置完成！');
  console.log('========================================');
  console.log('');

  // 显示 Python 版本
  try {
    const pythonCmd = os === 'windows'
      ? path.join('.venv', 'Scripts', 'python.exe')
      : path.join('.venv', 'bin', 'python');

    const version = execCommandSync(`"${pythonCmd}" --version`);
    console.log(`Python 版本: ${version}`);
  } catch (error) {
    // 忽略错误
  }

  console.log('');
  console.log('💡 下一步:');

  if (os === 'windows') {
    console.log('   1. 激活虚拟环境: .venv\\Scripts\\activate');
  } else {
    console.log('   1. 激活虚拟环境: source .venv/bin/activate');
  }

  console.log('   2. 运行服务: python main.py');
  console.log('   3. 或使用 npm: npm start');
  console.log('');
  console.log('📖 详细文档请查看: ENVIRONMENT_SETUP.md');
  console.log('');
}

// 运行主函数
main().catch((error) => {
  printError(error.message);
  process.exit(1);
});
