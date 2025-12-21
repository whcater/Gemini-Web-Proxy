"""
测试 Function Calling 功能
测试 Gemini Proxy 对 OpenAI Function Calling API 的支持
"""
import requests
import json
import time

# 配置
API_BASE = "http://127.0.0.1:5000/v1"
API_KEY = "test-key"  # 任意值，会被忽略

def test_function_calling():
    """测试基本的 Function Calling 功能"""
    print("="*60)
    print("测试 Function Calling 功能")
    print("="*60)

    # 定义函数
    functions = [
        {
            "name": "getCurrentTime",
            "description": "Get the current time for a given city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city name, e.g., 'Beijing', 'New York'"
                    },
                    "timezone": {
                        "type": "string",
                        "description": "The timezone, e.g., 'Asia/Shanghai', 'America/New_York'"
                    }
                },
                "required": ["city"]
            }
        },
        {
            "name": "getWeather",
            "description": "Get the weather for a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The location to get weather for"
                    },
                    "unit": {
                        "type": "string",
                        "description": "Temperature unit: 'celsius' or 'fahrenheit'",
                        "enum": ["celsius", "fahrenheit"]
                    }
                },
                "required": ["location"]
            }
        }
    ]

    # 测试消息
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that can tell time and weather. Use the available functions when needed."
        },
        {
            "role": "user",
            "content": "What time is it in Beijing?"
        }
    ]

    # 请求数据
    request_data = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "functions": functions,
        "function_call": "auto",
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 2000
    }

    print("\n📤 发送请求到 API...")
    print(f"   函数数量: {len(functions)}")
    for func in functions:
        print(f"   - {func['name']}: {func['description']}")
    print(f"\n   用户问题: {messages[-1]['content']}")

    # 发送请求
    try:
        response = requests.post(
            f"{API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json=request_data,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            print("\n✅ 收到响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            # 检查是否有函数调用
            if result.get("choices"):
                choice = result["choices"][0]
                message = choice.get("message", {})

                if "function_call" in message:
                    func_call = message["function_call"]
                    print(f"\n🎯 检测到函数调用:")
                    print(f"   函数名: {func_call.get('name')}")
                    print(f"   参数: {func_call.get('arguments')}")

                    # 解析参数
                    try:
                        args = json.loads(func_call.get('arguments', '{}'))
                        print(f"   解析后的参数: {args}")
                    except json.JSONDecodeError:
                        print(f"   ⚠️ 参数解析失败")

                if message.get("content"):
                    print(f"\n📝 助手回复: {message['content']}")

        else:
            print(f"\n❌ 请求失败: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")

def test_weather_function():
    """测试天气查询函数调用"""
    print("\n" + "="*60)
    print("测试天气查询函数")
    print("="*60)

    functions = [
        {
            "name": "getWeather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    }
                },
                "required": ["location"]
            }
        }
    ]

    messages = [
        {
            "role": "user",
            "content": "What's the weather like in Tokyo?"
        }
    ]

    request_data = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "functions": functions,
        "function_call": "auto",
        "stream": False
    }

    print(f"\n   用户问题: {messages[-1]['content']}")

    try:
        response = requests.post(
            f"{API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json=request_data,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            message = result["choices"][0]["message"]

            if "function_call" in message:
                print(f"\n✅ 函数调用成功!")
                print(f"   函数: {message['function_call']['name']}")
                print(f"   参数: {message['function_call']['arguments']}")
            else:
                print(f"\n⚠️ 没有检测到函数调用")
                print(f"   回复: {message.get('content', '')}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")

def test_streaming_function_call():
    """测试流式响应中的函数调用"""
    print("\n" + "="*60)
    print("测试流式函数调用")
    print("="*60)

    functions = [
        {
            "name": "calculateSum",
            "description": "Calculate the sum of two numbers",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"}
                },
                "required": ["a", "b"]
            }
        }
    ]

    messages = [
        {
            "role": "user",
            "content": "Please calculate 15 + 27 for me"
        }
    ]

    request_data = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "functions": functions,
        "stream": True  # 流式响应
    }

    print(f"\n   用户问题: {messages[-1]['content']}")
    print("   模式: 流式响应")

    try:
        response = requests.post(
            f"{API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json=request_data,
            stream=True,
            timeout=60
        )

        if response.status_code == 200:
            print("\n📥 接收流式响应:")
            function_name = None
            function_args = ""

            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            print("\n✅ 流式传输完成")
                            break

                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {})

                            if "function_call" in delta:
                                fc = delta["function_call"]
                                if "name" in fc:
                                    function_name = fc["name"]
                                    print(f"   检测到函数: {function_name}")
                                if "arguments" in fc:
                                    function_args += fc["arguments"]

                            if "content" in delta:
                                print(f"   文本: {delta['content']}", end="")

                        except json.JSONDecodeError:
                            pass

            if function_name:
                print(f"\n\n🎯 函数调用汇总:")
                print(f"   函数名: {function_name}")
                print(f"   参数: {function_args}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")

def main():
    """运行所有测试"""
    print("\n🚀 开始测试 Function Calling 功能\n")
    print("请确保 Gemini Proxy 服务正在运行 (http://127.0.0.1:5000)")
    print("="*60)

    # 等待服务就绪
    print("\n检查服务状态...")
    try:
        response = requests.get(f"{API_BASE}/models", timeout=5)
        if response.status_code == 200:
            print("✅ 服务正常运行\n")
        else:
            print("⚠️ 服务响应异常")
    except:
        print("❌ 无法连接到服务，请先启动 main.py")
        return

    # 运行测试
    test_function_calling()
    time.sleep(2)

    test_weather_function()
    time.sleep(2)

    test_streaming_function_call()

    print("\n" + "="*60)
    print("✅ 所有测试完成!")
    print("="*60)

if __name__ == "__main__":
    main()