"""
Gemini 浏览器自动化客户端 - CDP完整版本
连接到已运行的 Chrome 实例，保持登录状态，具备完整功能
"""
import os
import asyncio
import time

# 确保本地 CDP 连接不走代理
os.environ.setdefault('NO_PROXY', '127.0.0.1,localhost')
from typing import AsyncGenerator, Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import config
from parser import GeminiResponseParser
import html2text
from function_calling import FunctionCallingHandler


class GeminiClientCDP:
    """使用 CDP 连接到已运行的 Chrome - 完整功能版本"""

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_initialized = False
        self.parser = GeminiResponseParser()
        self._response_chunks = []
        self._response_complete = False
        # 初始化html2text转换器
        self.html_converter = html2text.HTML2Text()
        self.html_converter.body_width = 0  # 不自动换行
        self.html_converter.ignore_links = False  # 保留链接
        self.html_converter.ignore_images = False  # 保留图片
        self.html_converter.ignore_emphasis = False  # 保留强调（加粗、斜体）
        # Function Calling 处理器
        self.function_handler = FunctionCallingHandler()

    def _format_messages_to_prompt(self, messages: list, functions: list = None, function_call: str = "auto") -> str:
        """
        将OpenAI格式的消息数组转换为单个提示词

        参数:
        - messages: OpenAI 格式的消息列表
        - functions: 可用的函数定义列表
        - function_call: 函数调用模式 ("auto", "none", "required", 或特定函数名)

        格式化策略：
        - system消息作为上下文说明
        - 对话历史按 "User: xxx\nAssistant: xxx" 格式组织
        - 最后一条用户消息单独列出
        - 如果有 functions，添加 function calling 指令
        """
        prompt_parts = []

        # 如果有 functions，先添加 function calling 指令
        if functions:
            function_prompt = self.function_handler.format_functions_to_prompt(functions, function_call)
            if function_prompt:
                prompt_parts.append(function_prompt)

        # 提取system消息
        system_messages = []
        for msg in messages:
            if msg.get('role') == 'system':
                content = msg.get('content', '')
                if content:
                    system_messages.append(content)

        if system_messages:
            system_content = '\n'.join(system_messages)
            prompt_parts.append(f"[系统说明]\n{system_content}\n")

        # 提取对话历史
        conversation_history = []
        last_user_message = None

        for msg in messages:
            role = msg.get('role')
            content = msg.get('content', '')

            if role == 'system':
                continue
            elif role == 'user':
                last_user_message = content
            elif role == 'assistant':
                if last_user_message:
                    conversation_history.append(f"User: {last_user_message}")
                    last_user_message = None
                # 处理 assistant 的响应
                if msg.get('function_call'):
                    # 如果是函数调用，显示函数调用信息
                    func_call = msg['function_call']
                    func_name = func_call.get('name', 'unknown')
                    func_args = func_call.get('arguments', '{}')
                    conversation_history.append(f"Assistant: [Called function: {func_name} with arguments: {func_args}]")
                elif content:
                    # 如果有文本内容，显示文本
                    conversation_history.append(f"Assistant: {content}")
            elif role == 'function':
                # 处理函数执行结果
                func_name = msg.get('name', 'unknown_function')
                conversation_history.append(f"Function [{func_name}] Result: {content}")

        # 添加对话历史
        if conversation_history:
            prompt_parts.append("[对话历史]")
            prompt_parts.extend(conversation_history)
            prompt_parts.append("")

        # 添加当前用户消息
        if last_user_message:
            prompt_parts.append(f"{last_user_message}")

        return '\n'.join(prompt_parts)

    async def initialize(self):
        """连接到已运行的 Chrome 浏览器"""
        if self.is_initialized:
            return

        print("🚀 初始化 Playwright...")
        self.playwright = await async_playwright().start()

        print(f"🌐 连接到已运行的 Chrome 浏览器...")
        print(f"   端口: 9222")
        print(f"   如未启动，请运行: ./start_chrome_cdp.sh")

        try:
            # 连接到已运行的 Chrome（通过 CDP）
            self.browser = await self.playwright.chromium.connect_over_cdp(
                endpoint_url="http://127.0.0.1:9222",
                timeout=config.TIMEOUT
            )

            print("✅ 成功连接到 Chrome！")

            # 获取所有上下文
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]  # 使用第一个上下文
                pages = self.context.pages

                # 查找 Gemini 页面或创建新页面
                gemini_page = None
                for page in pages:
                    if "gemini.google.com" in page.url:
                        gemini_page = page
                        print(f"✅ 找到 Gemini 页面: {page.url}")
                        break

                if gemini_page:
                    self.page = gemini_page
                else:
                    # 创建新页面并导航到 Gemini
                    self.page = await self.context.new_page()
                    print("📄 创建新标签页")
                    await self.page.goto(config.GEMINI_URL, wait_until="domcontentloaded")
                    await asyncio.sleep(3)
            else:
                print("❌ 没有找到浏览器上下文")
                raise Exception("没有找到浏览器上下文")

            # 设置默认超时
            self.page.set_default_timeout(config.TIMEOUT)

            # 设置响应监听器
            self._setup_response_listener()

            # 检查登录状态
            print("🔍 检查登录状态...")
            is_logged_in = await self._check_login_status()

            if is_logged_in:
                print("✅ 已登录 Gemini！")
            else:
                print("⚠️  未登录，请在浏览器中手动登录")

            self.is_initialized = True
            print("✅ CDP 连接初始化完成！")

        except Exception as e:
            print(f"❌ 连接失败: {e}")
            print(f"💡 解决方案：")
            print(f"   1. 运行 ./start_chrome_cdp.sh 启动 Chrome")
            print(f"   2. 在 Chrome 中手动登录 Gemini")
            print(f"   3. 重新运行本程序")
            raise

    async def _check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            result = await self.page.evaluate('''() => {
                // 查找输入框
                const inputBox = document.querySelector('div.ql-editor[contenteditable="true"]') ||
                               document.querySelector('textarea');

                // 查找登录按钮
                const signInButton = document.querySelector('a[aria-label*="Sign in"]') ||
                                   document.querySelector('a[href*="accounts.google.com"]');

                return {
                    hasInputBox: !!inputBox,
                    hasSignInButton: !!signInButton
                };
            }''')

            # 如果有输入框且没有登录按钮，认为已登录
            return result['hasInputBox'] and not result['hasSignInButton']
        except:
            return False

    def _setup_response_listener(self):
        """设置网络响应监听器"""
        async def handle_response(response):
            url = response.url

            # 只监听 StreamGenerate 请求
            if "StreamGenerate" in url:
                try:
                    text = await response.text()
                    self._response_chunks.append(text)
                    print(f"📥 收到响应块 ({len(text)} bytes)")
                    if config.DEBUG:
                        print(f"   内容预览: {text[:300]}...")
                except Exception as e:
                    if "evicted from inspector cache" in str(e):
                        print(f"ℹ️  响应体已从缓存清除（正常现象）")
                    else:
                        print(f"⚠️  响应处理错误: {e}")

        self.page.on("response", handle_response)

    async def _monitor_dom_updates(self, page: Page, use_streaming: bool = True) -> AsyncGenerator[dict, None]:
        """
        实时监控DOM更新并流式返回
        """
        print(f"🔍 开始监控DOM更新 (流式模式: {use_streaming})")

        # 等待正文容器出现
        try:
            await page.wait_for_selector('message-content .markdown', timeout=10000)
            print("✅ 正文容器已出现")
        except Exception as e:
            print(f"⚠️ 等待正文容器超时: {e}")

        last_thinking = ""
        last_content = ""
        last_canvas = ""
        stable_count = 0
        max_stable_count = int(config.DOM_STABLE_TIMEOUT / config.DOM_POLL_INTERVAL)

        thinking_button_clicked = False
        canvas_button_clicked = False
        thinking_stable_count = 0
        thinking_stable_threshold = 3

        while True:
            try:
                # 检查思维链按钮
                if not thinking_button_clicked:
                    thinking_button = await page.query_selector('button[data-test-id="thoughts-header-button"]')
                    if thinking_button:
                        is_visible = await thinking_button.is_visible()
                        if is_visible:
                            try:
                                await thinking_button.click()
                                print("✅ 已点击思维链展开按钮")
                                thinking_button_clicked = True
                                await asyncio.sleep(0.3)
                            except Exception as e:
                                if config.DEBUG:
                                    print(f"⚠️ 点击思维链按钮失败: {e}")

                # 检查Canvas打开按钮
                if not canvas_button_clicked:
                    canvas_button = await page.query_selector('button[data-test-id="view-report-button"]')
                    if canvas_button:
                        is_visible = await canvas_button.is_visible()
                        if is_visible:
                            try:
                                await canvas_button.click()
                                print("✅ 已点击Canvas打开按钮")
                                canvas_button_clicked = True
                                await asyncio.sleep(1.0)
                            except Exception as e:
                                if config.DEBUG:
                                    print(f"⚠️ 点击Canvas按钮失败: {e}")

                # 提取思维链内容
                current_thinking = None
                if thinking_button_clicked:
                    thinking_elements = await page.query_selector_all('model-thoughts[data-test-id="model-thoughts"] .thoughts-content .markdown')
                    if thinking_elements:
                        thinking_texts = []
                        for elem in thinking_elements:
                            html_content = await elem.inner_html()
                            if html_content and html_content.strip():
                                markdown_text = self.html_converter.handle(html_content).strip()
                                if markdown_text:
                                    thinking_texts.append(markdown_text)
                        if thinking_texts:
                            current_thinking = "\n\n".join(thinking_texts)

                # 检测思维链是否稳定
                if current_thinking == last_thinking and current_thinking:
                    thinking_stable_count += 1
                else:
                    thinking_stable_count = 0

                # 提取Canvas文档内容
                current_canvas = None
                thinking_is_stable = (thinking_stable_count >= thinking_stable_threshold) or not thinking_button_clicked
                canvas_panel = await page.query_selector('extended-response-panel')
                if canvas_panel and thinking_is_stable:
                    title_elem = await canvas_panel.query_selector('h2.title-text')
                    canvas_title = None
                    if title_elem:
                        canvas_title = await title_elem.inner_text()

                    content_elem = await canvas_panel.query_selector('.immersive-editor .ProseMirror')
                    if content_elem:
                        canvas_html = await content_elem.evaluate('''(element) => {
                            const clone = element.cloneNode(true);
                            const buttons = clone.querySelectorAll('button');
                            buttons.forEach(btn => btn.remove());
                            const timestamps = clone.querySelectorAll('[data-test-id="creation-timestamp"]');
                            timestamps.forEach(ts => ts.remove());
                            const unwanted = clone.querySelectorAll('.retry-without-tool-button, .creation-timestamp');
                            unwanted.forEach(el => el.remove());
                            return clone.innerHTML;
                        }''')

                        if canvas_html and canvas_html.strip():
                            markdown_text = self.html_converter.handle(canvas_html).strip()
                            if markdown_text:
                                if canvas_title:
                                    current_canvas = f"```canvas\n# {canvas_title}\n\n{markdown_text}\n```"
                                else:
                                    current_canvas = f"```canvas\n{markdown_text}\n```"

                                if config.DEBUG:
                                    print(f"📄 提取到Canvas文档: {canvas_title or '(无标题)'}")

                # 提取正文内容
                current_content = None
                content_container = await page.query_selector('message-content[class*="model-response-text"]')
                if content_container:
                    is_in_canvas = await content_container.evaluate('''(element) => {
                        return element.closest('extended-response-panel') !== null;
                    }''')

                    if not is_in_canvas:
                        markdown_elem = await content_container.query_selector('.markdown')
                        if markdown_elem:
                            html_content = await markdown_elem.inner_html()
                            if html_content and html_content.strip():
                                markdown_text = self.html_converter.handle(html_content).strip()
                                if markdown_text:
                                    current_content = markdown_text

                # 检测变化
                has_change = False

                if current_thinking != last_thinking:
                    has_change = True
                    last_thinking = current_thinking
                    if config.DEBUG and current_thinking:
                        print(f"📝 思维链更新: {current_thinking[:50]}...")

                if current_content != last_content:
                    has_change = True
                    last_content = current_content
                    if config.DEBUG and current_content:
                        print(f"📝 正文更新: {current_content[:50]}...")

                if current_canvas != last_canvas:
                    has_change = True
                    last_canvas = current_canvas
                    if config.DEBUG and current_canvas:
                        print(f"📄 Canvas更新: {current_canvas[:50]}...")

                # 返回数据
                if has_change:
                    stable_count = 0

                    if use_streaming:
                        yield {
                            "thinking": current_thinking,
                            "content": current_content,
                            "canvas": current_canvas
                        }
                else:
                    stable_count += 1

                # 检测完成
                if stable_count >= max_stable_count:
                    print(f"✅ 文本已稳定 {config.DOM_STABLE_TIMEOUT} 秒，判定完成")
                    if current_thinking:
                        print(f"   思维链: {len(current_thinking)} 字符")
                    if current_content:
                        print(f"   正文: {len(current_content)} 字符")
                    if current_canvas:
                        print(f"   Canvas: {len(current_canvas)} 字符")

                    if not use_streaming:
                        yield {
                            "thinking": current_thinking,
                            "content": current_content,
                            "canvas": current_canvas
                        }
                    break

                # 检测停止按钮消失
                stop_button = await page.query_selector('button[aria-label*="Stop"], button[aria-label*="停止"]')
                if not stop_button and stable_count > 5:
                    print("✅ 停止按钮已消失，判定完成")
                    if not use_streaming:
                        yield {
                            "thinking": current_thinking,
                            "content": current_content,
                            "canvas": current_canvas
                        }
                    break

                await asyncio.sleep(config.DOM_POLL_INTERVAL)

            except Exception as e:
                print(f"⚠️ DOM监控错误: {e}")
                if config.DEBUG:
                    import traceback
                    traceback.print_exc()
                await asyncio.sleep(config.DOM_POLL_INTERVAL)

    async def send_message(self, messages: list, model: str = "gemini-pro", **kwargs) -> AsyncGenerator[str, None]:
        """
        发送消息到 Gemini 并流式返回响应
        在已有页面中发送消息，保持对话连续性

        参数:
        - messages: 消息列表
        - model: 模型名称
        - **kwargs: 额外参数，包括 functions, function_call 等
        """
        if not self.is_initialized:
            await self.initialize()

        # 提取 function calling 相关参数
        functions = kwargs.get('functions', None)
        function_call = kwargs.get('function_call', 'auto')

        # 格式化对话历史为单个提示词，包含 function calling 指令
        formatted_prompt = self._format_messages_to_prompt(messages, functions, function_call)

        print(f"📝 发送消息 ({len(messages)} 条对话历史)")
        print(f"   格式化后的提示词: {formatted_prompt[:100]}...")
        if functions:
            print(f"   包含 {len(functions)} 个可用函数")

        # 清空之前的响应块
        self._response_chunks = []

        try:
            # 查找输入框
            input_selector = 'div.ql-editor[contenteditable="true"]'
            input_element = await self.page.wait_for_selector(input_selector, timeout=5000)

            # 输入消息
            await input_element.evaluate('''(element, text) => {
                element.textContent = text;
                element.dispatchEvent(new Event('input', { bubbles: true }));
            }''', formatted_prompt)

            print(f"✅ 内容已设置 ({len(formatted_prompt)} 字符)")
            await asyncio.sleep(0.5)

            # 查找并点击发送按钮
            send_button_selectors = [
                'button[aria-label*="Send"]',
                'button[aria-label*="发送"]',
                'button.send-button',
                'button[data-test-id="send-button"]',
                'button[type="submit"]',
            ]

            button_clicked = False
            for selector in send_button_selectors:
                try:
                    button = await self.page.wait_for_selector(selector, timeout=2000, state='visible')
                    if button:
                        is_visible = await button.is_visible()
                        is_enabled = await button.is_enabled()

                        if is_visible and is_enabled:
                            print(f"✅ 找到发送按钮: {selector}")
                            await button.click()
                            button_clicked = True
                            print(f"✅ 消息已发送")
                            break
                except Exception as e:
                    if config.DEBUG:
                        print(f"⚠️  尝试按钮 {selector} 失败: {e}")
                    continue

            if not button_clicked:
                # 备用方案：按 Enter 键发送
                print("⚠️  未找到发送按钮，尝试按 Enter 键...")
                await self.page.keyboard.press('Enter')
                print("✅ 已按 Enter 键发送")

            # 等待响应开始
            await asyncio.sleep(2)

            # 使用DOM监听或网络监听
            use_dom_streaming = config.USE_DOM_STREAMING

            if use_dom_streaming:
                # DOM监听方式
                print(f"🔄 使用DOM监听模式获取响应")
                async for data in self._monitor_dom_updates(self.page, use_streaming=True):
                    if data:
                        yield data
            else:
                # 网络监听方式
                print(f"🔄 使用网络监听模式获取响应")
                max_wait_minutes = config.RESPONSE_TIMEOUT // 60
                print(f"⏳ 等待响应（最长等待{max_wait_minutes}分钟）...")

                last_text = ""
                retry_count = 0
                max_retries = config.RESPONSE_TIMEOUT * 2
                chunks_processed = 0

                while retry_count < max_retries:
                    current_chunk_count = len(self._response_chunks)

                    if current_chunk_count > chunks_processed:
                        print(f"📦 处理响应块 {chunks_processed + 1}-{current_chunk_count}")

                        for i in range(chunks_processed, current_chunk_count):
                            chunk = self._response_chunks[i]
                            parsed_data = self.parser.parse_stream_chunk(chunk)

                            if parsed_data:
                                if isinstance(parsed_data, dict):
                                    thinking = parsed_data.get('thinking', '')
                                    content = parsed_data.get('content', '')

                                    if config.DEBUG:
                                        if thinking:
                                            print(f"✅ 解析到思维链: {thinking[:50]}...")
                                        if content:
                                            print(f"✅ 解析到正文: {content[:50]}...")

                                    yield parsed_data
                                    last_text = parsed_data
                                else:
                                    print(f"✅ 解析到文本: {str(parsed_data)[:50]}...")
                                    if parsed_data != last_text:
                                        yield parsed_data
                                        last_text = parsed_data

                        chunks_processed = current_chunk_count

                        # 检查是否完成
                        last_chunk = self._response_chunks[-1] if self._response_chunks else ""

                        if '"di"' in last_chunk or 'af.httprm' in last_chunk:
                            print("✅ 响应完成")
                            break

                    await asyncio.sleep(0.5)
                    retry_count += 1

                if retry_count >= max_retries:
                    timeout_message = f"⚠️ 响应超时：等待了{max_wait_minutes}分钟"
                    print(timeout_message)
                    yield {"content": f"\n\n{timeout_message}"}

        except Exception as e:
            print(f"❌ 发送消息失败: {e}")
            raise

    async def close(self):
        """断开连接（不关闭浏览器）"""
        if self.browser:
            await self.browser.close()  # 只是断开连接，不关闭 Chrome
        if self.playwright:
            await self.playwright.stop()
        self.is_initialized = False
        print("👋 已断开CDP连接（Chrome 仍在运行）")


# 全局客户端实例（单例模式）
_client = None

async def get_client() -> GeminiClientCDP:
    """获取全局客户端实例"""
    global _client
    if _client is None:
        _client = GeminiClientCDP()
        await _client.initialize()
    return _client