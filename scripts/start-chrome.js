#!/usr/bin/env node

/**
 * 跨平台 Chrome CDP 启动脚本
 * 支持 Windows、macOS、Linux
 */

const {
  getOS,
  getChromeUserDataDir,
  getChromePath,
  killChromeProcesses,
  sleep,
  checkPort,
  printSuccess,
  printError,
  printWarning,
  printInfo
} = require('./utils');

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');

// 配置选项
const CDP_PORT = 9222;
const CDP_HOST = '127.0.0.1';
const GEMINI_URL = 'https://gemini.google.com/app';

// 检查是否使用 CDP 模式（无痕模式）
const useCDP = process.argv.includes('--cdp') || process.argv.includes('-c');

async function main() {
  console.log('========================================');
  console.log('  启动 Chrome 远程调试');
  console.log(`  模式: ${useCDP ? 'CDP (无痕模式)' : '普通模式'}`);
  console.log('========================================');
  console.log('');

  const os = getOS();
  console.log(`系统: ${os}`);
  console.log('');

  try {
    // 步骤 1: 关闭现有 Chrome 进程
    console.log('[1/4] 关闭现有 Chrome 进程...');
    killChromeProcesses();
    await sleep(2000);
    console.log('');

    // 步骤 2: 准备启动参数
    console.log('[2/4] 准备启动参数...');
    const chromeArgs = await prepareChromeArgs(useCDP);
    console.log('');

    // 步骤 3: 启动 Chrome
    console.log('[3/4] 启动 Chrome...');
    await launchChrome(chromeArgs);
    await sleep(2000);
    console.log('');

    // 步骤 4: 验证 CDP 连接
    console.log('[4/4] 验证 CDP 连接...');
    await verifyCDPConnection();
    console.log('');

    // 显示完成信息
    showCompletionMessage(useCDP);

  } catch (error) {
    printError(`启动失败: ${error.message}`);
    process.exit(1);
  }
}

/**
 * 准备 Chrome 启动参数
 */
async function prepareChromeArgs(useCDP) {
  const userDataDir = getChromeUserDataDir();

  // 基础参数
  const args = [
    `--remote-debugging-port=${CDP_PORT}`,
    `--remote-debugging-address=${CDP_HOST}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding'
  ];

  if (useCDP) {
    // CDP 模式：使用临时目录（无痕模式）
    const os = getOS();
    const tempDir = os === 'windows'
      ? path.join(process.env.TEMP || 'C:\\Temp', 'chrome-cdp-profile')
      : '/tmp/chrome-cdp-profile';

    // 创建临时目录
    try {
      if (!fs.existsSync(tempDir)) {
        fs.mkdirSync(tempDir, { recursive: true });
        printInfo(`创建临时目录: ${tempDir}`);
      }
    } catch (error) {
      throw new Error(`无法创建临时目录 ${tempDir}: ${error.message}`);
    }

    // 可选：从现有 Profile 复制数据
    const profileName = 'Default'; // 可以根据需要修改
    const sourceProfile = path.join(userDataDir, profileName);
    const targetProfile = path.join(tempDir, profileName);

    if (fs.existsSync(sourceProfile) && !fs.existsSync(targetProfile)) {
      try {
        printInfo(`复制现有 Profile 数据到临时目录...`);
        fs.mkdirSync(targetProfile, { recursive: true });
        // 注意：完整复制可能较慢，这里仅创建目录
      } catch (error) {
        printWarning(`无法创建 Profile 目录: ${error.message}`);
      }
    }

    // 注意：参数不要加引号，spawn 会自动处理空格
    args.push(
      '--incognito',
      `--user-data-dir=${tempDir}`,
      `--profile-directory=${profileName}`
    );

    printInfo(`使用临时 Profile: ${tempDir}`);
  } else {
    // 普通模式：使用默认用户数据目录
    const profileName = 'Default'; // 可以根据需要修改为 "Profile 2" 等

    // 注意：参数不要加引号，spawn 会自动处理空格
    args.push(
      `--user-data-dir=${userDataDir}`,
      `--profile-directory=${profileName}`
    );

    printInfo(`使用用户 Profile: ${userDataDir}/${profileName}`);
  }

  // 添加启动 URL
  args.push(GEMINI_URL);

  printSuccess('启动参数准备完成');

  return args;
}

/**
 * 启动 Chrome
 */
async function launchChrome(args) {
  const chromePath = getChromePath();

  console.log(`Chrome 路径: ${chromePath}`);

  // 启动 Chrome 进程
  const chrome = spawn(chromePath, args, {
    detached: true,
    stdio: 'ignore'
  });

  chrome.unref(); // 让 Chrome 在后台运行

  printSuccess('Chrome 已启动');
}

/**
 * 验证 CDP 连接
 */
async function verifyCDPConnection() {
  console.log('测试 CDP 连接...');

  // 等待端口开放
  let attempts = 0;
  const maxAttempts = 10;

  while (attempts < maxAttempts) {
    const isOpen = await checkPort(CDP_PORT, CDP_HOST);

    if (isOpen) {
      // 尝试访问 CDP API
      try {
        await fetchCDPVersion();
        printSuccess('CDP 端口已开启！');
        return;
      } catch (error) {
        // 继续等待
      }
    }

    attempts++;
    await sleep(500);
  }

  throw new Error('CDP 端口未开启，请检查 Chrome 进程');
}

/**
 * 获取 CDP 版本信息
 */
function fetchCDPVersion() {
  return new Promise((resolve, reject) => {
    const req = http.get(`http://${CDP_HOST}:${CDP_PORT}/json/version`, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          const version = JSON.parse(data);
          console.log(`      Browser: ${version.Browser}`);
          console.log(`      Protocol: ${version['Protocol-Version']}`);
          resolve(version);
        } catch (error) {
          reject(error);
        }
      });
    });

    req.on('error', reject);
    req.setTimeout(2000, () => {
      req.destroy();
      reject(new Error('Timeout'));
    });
  });
}

/**
 * 显示完成信息
 */
function showCompletionMessage(useCDP) {
  console.log('========================================');
  console.log('  Chrome 启动成功！');
  console.log('========================================');
  console.log('');
  console.log(`远程调试端口: ${CDP_PORT}`);
  console.log(`模式: ${useCDP ? 'CDP 无痕模式' : '普通模式'}`);
  console.log('');
  console.log('💡 下一步：');
  console.log('   1. 在 Chrome 中登录 Google 账号');
  console.log('   2. 确保能访问 Gemini');
  console.log('   3. 运行服务: python main.py');
  console.log('   4. 或使用 npm: npm start');
  console.log('');

  if (useCDP) {
    printWarning('注意: 无痕模式下登录信息不会被保存');
    console.log('');
  }

  console.log('🔍 测试连接:');
  console.log(`   curl http://${CDP_HOST}:${CDP_PORT}/json/version`);
  console.log('');
}

// 运行主函数
main().catch((error) => {
  printError(error.message);
  process.exit(1);
});
