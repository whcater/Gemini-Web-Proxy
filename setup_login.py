#!/usr/bin/env python3
"""
测试并设置 Gemini 登录
"""
import asyncio
from playwright.async_api import async_playwright
import sys
import os
import json

async def test_and_setup():
    """测试登录并设置"""
    playwright = await async_playwright().start()

    print("🚀 启动浏览器...")
    print(f"   Profile: /Users/ylp/Library/Application Support/Google/Chrome")

    try:
        # 启动浏览器 - 使用与 gemini_client.py 相同的参数
        browser = await playwright.chromium.launch_persistent_context(
            user_data_dir="/Users/ylp/Library/Application Support/Google/Chrome",
            headless=False,  # 显示窗口
            channel="chrome",
            args=[
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-popup-blocking',
                '--disable-translate',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-device-discovery-notifications',
                '--window-size=1280,720',
                '--start-maximized',
                '--profile-directory=Profile 2'
            ],
            ignore_default_args=[
                "--enable-automation",
                "--no-sandbox"
            ],
            timeout=30000
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()

        print("📱 访问 Gemini...")
        await page.goto("https://gemini.google.com/app", wait_until="domcontentloaded")
        await asyncio.sleep(5)  # 等待页面加载

        # 检查登录状态
        is_logged_in = await page.evaluate('''() => {
            // 多种方式检查登录状态
            const signInButton = document.querySelector('a[aria-label*="Sign in"]') ||
                               document.querySelector('a[href*="accounts.google.com"]');

            const avatar = document.querySelector('img[alt*="Google Account"]') ||
                          document.querySelector('[aria-label*="Google Account"]') ||
                          document.querySelector('.gb_D');  // Google账号头像

            const inputBox = document.querySelector('div.ql-editor[contenteditable="true"]') ||
                           document.querySelector('textarea');

            return {
                hasSignInButton: !!signInButton,
                hasAvatar: !!avatar,
                hasInputBox: !!inputBox,
                url: window.location.href
            };
        }''')

        print("\n📊 检查结果：")
        print(f"   当前 URL: {is_logged_in['url']}")
        print(f"   发现登录按钮: {is_logged_in['hasSignInButton']}")
        print(f"   发现用户头像: {is_logged_in['hasAvatar']}")
        print(f"   发现输入框: {is_logged_in['hasInputBox']}")

        # 判断登录状态
        if is_logged_in['hasAvatar'] or is_logged_in['hasInputBox']:
            print("\n✅ 已登录 Gemini！")

            # 测试发送消息
            print("\n📝 测试发送消息...")
            input_selector = 'div.ql-editor[contenteditable="true"]'
            try:
                input_element = await page.wait_for_selector(input_selector, timeout=5000)

                # 输入测试消息
                await input_element.evaluate('''(element, text) => {
                    element.textContent = text;
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                }''', "Hello, this is a test")

                print("✅ 可以输入消息")

                # 清空输入框
                await input_element.evaluate('element => element.textContent = ""')

            except Exception as e:
                print(f"⚠️  输入测试失败: {e}")

        else:
            print("\n⚠️  未登录 Gemini")
            print("\n请手动登录：")
            print("1. 在浏览器窗口中登录 Google 账号")
            print("2. 确保可以访问 Gemini")
            print("3. 登录完成后，再次运行本脚本")

        # 保持浏览器打开一会儿
        print("\n浏览器将在 5 秒后关闭...")
        await asyncio.sleep(5)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await browser.close()
        await playwright.stop()

    return True

if __name__ == "__main__":
    success = asyncio.run(test_and_setup())
    if success:
        print("\n✅ 测试成功！")
        print("\n现在可以重启服务器：")
        print("1. 停止当前服务器 (Ctrl+C)")
        print("2. 运行: python main.py")
    else:
        print("\n❌ 测试失败，请检查问题")
        sys.exit(1)