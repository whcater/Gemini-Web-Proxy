"""
Gemini to OpenAI API Proxy
将 Gemini Pro 网页版包装为 OpenAI API 格式
"""
from flask import Flask, request, Response, jsonify
import asyncio
import json
import time
import threading
from typing import AsyncGenerator
import config
from gemini_client_cdp_full import get_client
from parser import GeminiResponseParser
from function_calling import FunctionCallingHandler


app = Flask(__name__)

# 全局事件循环和线程
_loop = None
_loop_thread = None
_loop_lock = threading.Lock()


def get_event_loop():
    """获取或创建全局事件循环"""
    global _loop, _loop_thread
    
    with _loop_lock:
        if _loop is None or not _loop.is_running():
            _loop = asyncio.new_event_loop()
            
            def run_loop():
                asyncio.set_event_loop(_loop)
                _loop.run_forever()
            
            _loop_thread = threading.Thread(target=run_loop, daemon=True)
            _loop_thread.start()
            print("🔄 启动全局事件循环")
        
        return _loop


def run_async(coro):
    """在全局事件循环中运行异步函数"""
    loop = get_event_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """
    OpenAI 兼容的聊天完成接口
    """
    try:
        # 解析请求
        data = request.json
        messages = data.get('messages', [])
        stream = data.get('stream', False)
        model = data.get('model', config.DEFAULT_MODEL)

        # Function Calling 相关参数
        functions = data.get('functions', None)
        function_call = data.get('function_call', 'auto')
        tools = data.get('tools', None)  # 新版本 API 使用 tools

        # 如果有 tools，转换为 functions
        if tools and not functions:
            fc_handler = FunctionCallingHandler()
            functions = fc_handler.convert_tools_to_functions(tools)

        if not messages:
            return jsonify({"error": "No messages provided"}), 400

        print(f"\n{'='*60}")
        print(f"📨 收到请求:")
        print(f"   full request body: {data}")
        print(f"   消息数量: {len(messages)}")
        print(f"   模型: {model}")
        print(f"   流式: {stream}")

        if functions:
            print(f"   函数调用: {len(functions)} 个函数可用")
            for func in functions:
                print(f"     - {func.get('name', 'unknown')}: {func.get('description', '')[:50]}")

        # 打印对话历史
        for i, msg in enumerate(messages):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            print(f"   [{i}] {role}: {content[:50]}...")

        print(f"{'='*60}\n")


        if stream:
            # 流式响应
            return Response(
                stream_response(messages, model, functions, function_call),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no',
                    'Connection': 'keep-alive',
                }
            )
        else:
            # 非流式响应
            return Response(
                non_stream_response(messages, model, functions, function_call),
                mimetype='application/json'
            )
            
    except Exception as e:
        print(f"❌ 请求处理错误: {e}")
        import traceback
        traceback.print_exc()
        
        error_response = {
            "error": {
                "message": str(e),
                "type": "server_error",
                "details": "请查看服务器日志获取详细信息"
            }
        }
        return jsonify(error_response), 500


def stream_response(messages: list, model: str = config.DEFAULT_MODEL, functions: list = None, function_call: str = "auto"):
    """流式响应生成器"""
    loop = get_event_loop()

    # 创建队列用于线程间通信
    import queue
    q = queue.Queue()

    async def async_generator():
        try:
            client = await get_client()
            # 使用client的parser实例，保持状态
            parser = client.parser
            fc_handler = client.function_handler

            # 流式获取响应，传递 functions 参数
            async for data_chunk in client.send_message(messages, model=model, functions=functions, function_call=function_call):
                if data_chunk:
                    # 调试：输出接收到的数据
                    if config.DEBUG:
                        print(f"[DEBUG] 收到数据块: {str(data_chunk)[:100]}...")

                    # 如果有 functions，尝试解析 function call
                    if functions and isinstance(data_chunk, dict):
                        content = data_chunk.get('content', '')
                        if content:
                            function_call_data, remaining_text = fc_handler.parse_gemini_response(content)
                            if function_call_data:
                                # 有函数调用，发送函数调用信息
                                print(f"✅ 检测到函数调用: {function_call_data['name']}")
                                # 发送函数调用开始
                                sse_data = fc_handler.format_streaming_chunk(function_call_data, None, is_first=True)
                                q.put(('data', sse_data))
                                # 发送函数参数
                                sse_data = fc_handler.format_streaming_chunk(function_call_data, None, is_first=False)
                                q.put(('data', sse_data))
                                # 如果有剩余文本，发送文本
                                if remaining_text:
                                    sse_data = fc_handler.format_streaming_chunk(None, remaining_text)
                                    q.put(('data', sse_data))
                            else:
                                # 没有函数调用，正常发送内容
                                sse_data = parser.to_openai_format(data_chunk, model=model)
                                if sse_data:
                                    q.put(('data', sse_data))
                    else:
                        # 转换为 OpenAI 格式（支持结构化数据）
                        sse_data = parser.to_openai_format(data_chunk, model=model)
                        if sse_data:  # 只有非空数据才放入队列
                            if config.DEBUG:
                                print(f"[DEBUG] 转换后的SSE数据: {sse_data[:100]}...")
                            q.put(('data', sse_data))
                        else:
                            if config.DEBUG:
                                print(f"[DEBUG] 转换返回空数据")

            # 发送完成标记
            q.put(('data', parser.to_openai_format("", is_done=True, model=model)))
            q.put(('done', None))
            
        except Exception as e:
            print(f"❌ 流式响应错误: {e}")
            import traceback
            traceback.print_exc()
            error_data = {
                "error": {
                    "message": str(e),
                    "type": "server_error"
                }
            }
            q.put(('data', f"data: {json.dumps(error_data)}\n\n"))
            q.put(('done', None))
    
    # 在全局事件循环中运行
    asyncio.run_coroutine_threadsafe(async_generator(), loop)
    
    # 从队列中读取并yield
    # 使用配置的响应超时时间，并额外增加5分钟缓冲
    queue_timeout = config.RESPONSE_TIMEOUT + 300  # 额外5分钟缓冲
    while True:
        try:
            msg_type, data = q.get(timeout=queue_timeout)
            if msg_type == 'done':
                break
            yield data
        except queue.Empty:
            timeout_minutes = queue_timeout // 60
            print(f"⚠️  队列超时（等待了 {timeout_minutes} 分钟）")
            break


def non_stream_response(messages: list, model: str = config.DEFAULT_MODEL, functions: list = None, function_call: str = "auto"):
    """非流式响应"""
    async def get_full_response():
        try:
            client = await get_client()
            fc_handler = client.function_handler

            # 收集所有响应
            full_thinking = ""
            full_content = ""
            full_canvas = ""

            async for data_chunk in client.send_message(messages, model=model, functions=functions, function_call=function_call):
                if isinstance(data_chunk, dict):
                    thinking = data_chunk.get('thinking', '')
                    content = data_chunk.get('content', '')
                    canvas = data_chunk.get('canvas', '')
                    if thinking:
                        full_thinking = thinking  # 思维链通常是完整的，不需要累加
                    if content:
                        full_content = content  # 正文也是完整的
                    if canvas:
                        full_canvas = canvas  # Canvas也是完整的
                else:
                    # 兼容旧格式
                    full_content += str(data_chunk)

            # 构建message对象
            message = {"role": "assistant"}

            # 如果有 functions，尝试解析 function call
            function_call_data = None
            remaining_text = full_content

            if functions and full_content:
                function_call_data, remaining_text = fc_handler.parse_gemini_response(full_content)
                if function_call_data:
                    print(f"✅ 检测到函数调用: {function_call_data['name']}")

            # 如果有函数调用
            if function_call_data:
                message["function_call"] = function_call_data
                if remaining_text:
                    message["content"] = remaining_text
            else:
                # 根据配置选择格式
                if config.ENABLE_THINKING and full_thinking:
                    if config.THINKING_FORMAT == "reasoning_content":
                        # o1系列格式
                        message["reasoning_content"] = full_thinking
                        # 将Canvas追加到正文
                        if full_canvas:
                            message["content"] = f"{full_content}\n\n{full_canvas}" if full_content else full_canvas
                        else:
                            message["content"] = full_content
                    elif config.THINKING_FORMAT == "inline":
                        # 内联格式
                        combined = f"<think>\n{full_thinking}\n</think>"
                        if full_content:
                            combined += f"\n\n{full_content}"
                        # 将Canvas追加到正文
                        if full_canvas:
                            combined += f"\n\n{full_canvas}"
                        message["content"] = combined
                    else:
                        # 将Canvas追加到正文
                        if full_canvas:
                            message["content"] = f"{full_content}\n\n{full_canvas}" if full_content else full_canvas
                        else:
                            message["content"] = full_content
                else:
                    # 将Canvas追加到正文
                    if full_canvas:
                        message["content"] = f"{full_content}\n\n{full_canvas}" if full_content else full_canvas
                    else:
                        message["content"] = full_content
            
            # 返回 OpenAI 格式
            response = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": message,
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
            
            return json.dumps(response)
            
        except Exception as e:
            print(f"❌ 非流式响应错误: {e}")
            import traceback
            traceback.print_exc()
            error_response = {
                "error": {
                    "message": str(e),
                    "type": "server_error"
                }
            }
            return json.dumps(error_response)
    
    try:
        return run_async(get_full_response())
    except Exception as e:
        print(f"❌ 运行异步函数失败: {e}")
        import traceback
        traceback.print_exc()
        return json.dumps({"error": {"message": str(e), "type": "server_error"}})


@app.route('/v1/models', methods=['GET'])
def list_models():
    """列出可用模型"""
    models_data = []
    for model_id, model_info in config.AVAILABLE_MODELS.items():
        models_data.append({
            "id": model_id,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "google",
            "description": model_info["description"]
        })
    
    models = {
        "object": "list",
        "data": models_data
    }
    return jsonify(models)


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok"})


@app.route('/', methods=['GET'])
def index():
    """首页"""
    return """
    <html>
    <head><title>Gemini Proxy</title></head>
    <body>
        <h1>🚀 Gemini to OpenAI API Proxy</h1>
        <p>服务运行中...</p>
        <h2>使用方法：</h2>
        <pre>
# 在模型设置中配置:
API Base URL: http://127.0.0.1:5000/v1
API Key: (任意填写，会被忽略)
Model: gemini-pro
        </pre>
        <h2>测试接口：</h2>
        <pre>
curl http://127.0.0.1:5000/v1/models
        </pre>
    </body>
    </html>
    """


def main():
    """主函数"""
    import logging
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("Gemin Web to OpenAI API Proxy")
    print("="*60)
    print(f"监听地址: http://{config.HOST}:{config.PORT}")
    print(f"Chrome 用户数据: {config.CHROME_USER_DATA}")
    print(f"Headless 模式: {config.HEADLESS}")
    print("="*60 + "\n")
    
    print("💡 提示：")
    print("   1. 请确保 Chrome 浏览器已登录 Gemini Pro")
    print("   2. 首次启动会打开浏览器，请保持运行")
    print("   3. 在模型API链接中配置:")
    print(f"      API Base URL: http://{config.HOST}:{config.PORT}/v1")
    print("      Model: gemini-pro")
    print("\n正在启动服务器...\n")
    
    try:
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=False,  # 禁用 debug 避免与 Playwright 冲突
            use_reloader=False,  # 禁用自动重载
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 服务器已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()