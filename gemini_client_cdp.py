"""
Gemini 浏览器自动化客户端 - 使用连接到已运行的 Chrome
修改版本：连接到已存在的 Chrome 实例，保持登录状态
"""
import asyncio
import time
from typing import AsyncGenerator, Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import config
from parser import GeminiResponseParser
import html2text


class GeminiClientCDP:
    """使用 CDP 连接到已运行的 Chrome"""

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.is_initialized = False
        self.parser = GeminiResponseParser()
        self._response_chunks = []
        self._response_complete = False
        self.html_converter = html2text.HTML2Text()
        self.html_converter.body_width = 0
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.ignore_emphasis = False

    async def initialize(self):
        """连接到已运行的 Chrome 浏览器"""
        if self.is_initialized:
            return

        print("🚀 初始化 Playwright...")
        self.playwright = await async_playwright().start()

        print(f"🌐 连接到已运行的 Chrome 浏览器...")
        print(f"   确保 Chrome 已通过以下命令启动：")
        print(f"   ./start_chrome.sh")

        try:
            # 连接到已运行的 Chrome（通过 CDP）- 使用IPv4地址
            self.browser = await self.playwright.chromium.connect_over_cdp(
                endpoint_url="http://127.0.0.1:9222",  # 使用IPv4而不是IPv6
                timeout=config.TIMEOUT
            )

            print("✅ 成功连接到 Chrome！")

            # 获取所有上下文
            contexts = self.browser.contexts
            if contexts:
                context = contexts[0]  # 使用第一个上下文
                pages = context.pages
                if pages:
                    # 使用现有页面
                    self.page = pages[0]
                    print(f"✅ 使用现有标签页: {self.page.url}")
                else:
                    # 创建新页面
                    self.page = await context.new_page()
                    print("📄 创建新标签页")
            else:
                print("❌ 没有找到浏览器上下文")
                raise Exception("没有找到浏览器上下文，请确保 Chrome 已启动")

            # 设置默认超时
            self.page.set_default_timeout(config.TIMEOUT)

            # 导航到 Gemini（如果还没有）
            if "gemini.google.com" not in self.page.url:
                print(f"📱 导航到 Gemini 页面...")
                await self.page.goto(config.GEMINI_URL, wait_until="domcontentloaded")
                await asyncio.sleep(3)

            # 检查登录状态
            print("🔍 检查登录状态...")

            # 查找用户头像或登录按钮
            is_logged_in = await self.page.evaluate('''() => {
                // 检查是否有用户头像
                const avatar = document.querySelector('img[alt*="Google Account"]') ||
                             document.querySelector('[aria-label*="Google Account"]') ||
                             document.querySelector('.gb_Ka');

                // 检查是否有登录按钮
                const signInButton = document.querySelector('a[aria-label*="Sign in"]') ||
                                   document.querySelector('a[href*="accounts.google.com"]');

                return {
                    isLoggedIn: !!avatar,
                    hasSignInButton: !!signInButton
                };
            }''')

            if is_logged_in['isLoggedIn']:
                print("✅ 已登录 Gemini！")
            elif is_logged_in['hasSignInButton']:
                print("⚠️  未登录，请在浏览器中手动登录")
                print("   登录后重新运行程序")
            else:
                print("⚠️  无法确定登录状态")

            self.is_initialized = True
            print("✅ 初始化完成！")

        except Exception as e:
            print(f"❌ 连接失败: {e}")
            print(f"💡 解决方案：")
            print(f"   1. 运行 ./start_chrome.sh 启动 Chrome")
            print(f"   2. 在 Chrome 中手动登录 Gemini")
            print(f"   3. 重新运行本程序")
            raise

    async def send_message(self, messages: list, model: str = "gemini-pro") -> AsyncGenerator[str, None]:
        """发送消息（简化版本）"""
        if not self.is_initialized:
            await self.initialize()

        # 格式化消息
        last_message = messages[-1].get('content', '') if messages else ""

        print(f"📝 发送消息: {last_message[:100]}...")

        # 在当前页面发送消息
        try:
            # 清空输入框并输入新消息
            input_selector = 'div.ql-editor[contenteditable="true"]'
            await self.page.wait_for_selector(input_selector, timeout=5000)

            # 清空并输入
            input_element = await self.page.query_selector(input_selector)
            await input_element.evaluate('''(element, text) => {
                element.textContent = text;
                element.dispatchEvent(new Event('input', { bubbles: true }));
            }''', last_message)

            # 发送
            send_button = await self.page.query_selector('button[aria-label*="Send"], button[aria-label*="发送"]')
            if send_button:
                await send_button.click()
                print("✅ 消息已发送")
            else:
                await self.page.keyboard.press('Enter')
                print("✅ 已按 Enter 发送")

            # 等待响应
            await asyncio.sleep(2)

            # 简单返回响应（这里简化处理）
            yield {"content": "Response from Gemini (CDP mode)"}

        except Exception as e:
            print(f"❌ 发送失败: {e}")
            yield {"content": f"Error: {e}"}

    async def close(self):
        """断开连接（不关闭浏览器）"""
        if self.browser:
            await self.browser.close()  # 只是断开连接，不关闭 Chrome
        if self.playwright:
            await self.playwright.stop()
        self.is_initialized = False
        print("👋 已断开连接（Chrome 仍在运行）")


# 使用 CDP 版本替代原来的客户端
_client = None

async def get_client() -> GeminiClientCDP:
    """获取全局客户端实例"""
    global _client
    if _client is None:
        _client = GeminiClientCDP()
        await _client.initialize()
    return _client