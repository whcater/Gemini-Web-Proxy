/**
 * 跨平台工具函数
 */

const { execSync, spawn } = require('child_process');
const os = require('os');
const path = require('path');
const fs = require('fs');

/**
 * 获取操作系统类型
 */
function getOS() {
  const platform = os.platform();
  if (platform === 'win32') return 'windows';
  if (platform === 'darwin') return 'macos';
  return 'linux';
}

/**
 * 检查命令是否存在
 */
function commandExists(command) {
  try {
    const os = getOS();
    const checkCmd = os === 'windows' ? `where ${command}` : `which ${command}`;
    execSync(checkCmd, { stdio: 'ignore' });
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * 执行命令并实时输出
 */
function execCommand(command, args = [], options = {}) {
  return new Promise((resolve, reject) => {
    const isWindows = getOS() === 'windows';

    // Windows 需要特殊处理
    const spawnOptions = {
      stdio: 'inherit',
      shell: true,
      ...options
    };

    const child = spawn(command, args, spawnOptions);

    child.on('close', (code) => {
      if (code === 0) {
        resolve(code);
      } else {
        reject(new Error(`Command failed with exit code ${code}`));
      }
    });

    child.on('error', (error) => {
      reject(error);
    });
  });
}

/**
 * 执行命令并返回输出
 */
function execCommandSync(command) {
  try {
    return execSync(command, { encoding: 'utf8' }).trim();
  } catch (error) {
    return null;
  }
}

/**
 * 获取 Chrome 用户数据目录
 */
function getChromeUserDataDir() {
  const os = getOS();
  const homeDir = require('os').homedir();

  switch (os) {
    case 'windows':
      return path.join(homeDir, 'AppData', 'Local', 'Google', 'Chrome', 'User Data');
    case 'macos':
      return path.join(homeDir, 'Library', 'Application Support', 'Google', 'Chrome');
    case 'linux':
      return path.join(homeDir, '.config', 'google-chrome');
    default:
      throw new Error('Unsupported operating system');
  }
}

/**
 * 获取 Chrome 可执行文件路径
 */
function getChromePath() {
  const os = getOS();

  switch (os) {
    case 'windows':
      const windowsPaths = [
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
        path.join(process.env.LOCALAPPDATA || '', 'Google\\Chrome\\Application\\chrome.exe')
      ];
      for (const p of windowsPaths) {
        if (fs.existsSync(p)) return p;
      }
      throw new Error('Chrome not found on Windows');

    case 'macos':
      return '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

    case 'linux':
      const linuxPaths = [
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable',
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser'
      ];
      for (const p of linuxPaths) {
        if (fs.existsSync(p)) return p;
      }
      throw new Error('Chrome not found on Linux');

    default:
      throw new Error('Unsupported operating system');
  }
}

/**
 * 关闭所有 Chrome 进程
 */
function killChromeProcesses() {
  const os = getOS();

  try {
    if (os === 'windows') {
      execSync('taskkill /F /IM chrome.exe /T', { stdio: 'ignore' });
    } else {
      execSync('killall "Google Chrome" 2>/dev/null || killall chrome 2>/dev/null || true', {
        stdio: 'ignore',
        shell: '/bin/bash'
      });
    }
    console.log('✅ Chrome 进程已关闭');
  } catch (error) {
    // 忽略错误（可能没有 Chrome 进程在运行）
  }
}

/**
 * 等待指定毫秒数
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 打印彩色文本
 */
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

function printColor(text, color = 'reset') {
  const colorCode = colors[color] || colors.reset;
  console.log(`${colorCode}${text}${colors.reset}`);
}

function printSuccess(text) {
  printColor(`✅ ${text}`, 'green');
}

function printError(text) {
  printColor(`❌ ${text}`, 'red');
}

function printWarning(text) {
  printColor(`⚠️  ${text}`, 'yellow');
}

function printInfo(text) {
  printColor(`💡 ${text}`, 'cyan');
}

/**
 * 检查端口是否开放
 */
async function checkPort(port, host = '127.0.0.1') {
  const net = require('net');

  return new Promise((resolve) => {
    const socket = new net.Socket();

    socket.setTimeout(1000);

    socket.on('connect', () => {
      socket.destroy();
      resolve(true);
    });

    socket.on('timeout', () => {
      socket.destroy();
      resolve(false);
    });

    socket.on('error', () => {
      resolve(false);
    });

    socket.connect(port, host);
  });
}

/**
 * 获取 Python 命令
 */
function getPythonCommand() {
  const commands = ['python', 'python3', 'py'];

  for (const cmd of commands) {
    if (commandExists(cmd)) {
      return cmd;
    }
  }

  throw new Error('Python not found. Please install Python 3.11 or 3.12');
}

module.exports = {
  getOS,
  commandExists,
  execCommand,
  execCommandSync,
  getChromeUserDataDir,
  getChromePath,
  killChromeProcesses,
  sleep,
  printColor,
  printSuccess,
  printError,
  printWarning,
  printInfo,
  checkPort,
  getPythonCommand
};
