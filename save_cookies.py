#!/usr/bin/env python3
"""
保存和恢复 Google 登录 Cookies
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def save_cookies():
    """从正常浏览器保存 cookies"""
    playwright = await async_playwright().start()

    print("📱 打开浏览器，请手动登录...")
    browser = await playwright.chromium.launch(
        headless=False,
        channel="chrome"
    )

    page = await browser.new_page()
    await page.goto("https://gemini.google.com")

    print("请在浏览器中登录 Google 账号")
    print("登录完成后，按 Enter 保存 cookies...")
    input()

    # 保存 cookies
    cookies = await page.context.cookies()
    with open("cookies.json", "w") as f:
        json.dump(cookies, f, indent=2)

    print(f"✅ 已保存 {len(cookies)} 个 cookies 到 cookies.json")

    await browser.close()
    await playwright.stop()

async def load_cookies(page):
    """加载保存的 cookies"""
    try:
        with open("cookies.json", "r") as f:
            cookies = json.load(f)

        await page.context.add_cookies(cookies)
        print(f"✅ 已加载 {len(cookies)} 个 cookies")
        return True
    except FileNotFoundError:
        print("⚠️  未找到 cookies.json")
        return False

if __name__ == "__main__":
    asyncio.run(save_cookies())