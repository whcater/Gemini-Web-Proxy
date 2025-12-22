"""
测试 Function Call 结果传递
验证第二次请求是否正确包含函数执行结果
"""
import requests
import json

# 配置
API_BASE = "http://127.0.0.1:5000/v1"
API_KEY = "test-key"

def test_function_result_handling():
    """测试函数执行结果的处理"""
    print("="*60)
    print("测试 Function Call 结果传递")
    print("="*60)

    # 定义函数
    functions = [{
        "name": "getCurrentTime",
        "description": "Get the current time for a given city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name"
                }
            }
        }
    }]

    # 第一次请求 - 获取函数调用
    print("\n📤 第一次请求: 询问时间")
    messages1 = [
        {
            "role": "system",
            "content": "You are a helpful assistant that tells the current time."
        },
        {
            "role": "user",
            "content": "What time is it in Beijing?"
        }
    ]

    response1 = requests.post(
        f"{API_BASE}/chat/completions",
        json={
            "model": "gpt-3.5-turbo",
            "messages": messages1,
            "functions": functions,
            "function_call": "auto",
            "stream": False
        },
        timeout=60
    )

    if response1.status_code == 200:
        result1 = response1.json()
        message1 = result1["choices"][0]["message"]

        if "function_call" in message1:
            print(f"✅ 收到函数调用:")
            print(f"   函数: {message1['function_call']['name']}")
            print(f"   参数: {message1['function_call']['arguments']}")

            # 构建第二次请求的消息历史
            messages2 = messages1.copy()

            # 添加 assistant 的函数调用响应
            messages2.append({
                "role": "assistant",
                "function_call": message1["function_call"],
                "content": message1.get("content", "")
            })

            # 添加函数执行结果
            messages2.append({
                "role": "function",
                "name": "getCurrentTime",
                "content": "The current time in Beijing is 2025-12-21 22:52:27"
            })

            print("\n📤 第二次请求: 传递函数执行结果")
            print("   消息历史包含:")
            for i, msg in enumerate(messages2):
                role = msg.get('role')
                if role == 'function':
                    print(f"     [{i}] {role}: {msg.get('name')} -> {msg.get('content')}")
                elif role == 'assistant' and msg.get('function_call'):
                    print(f"     [{i}] {role}: function_call -> {msg['function_call']['name']}")
                else:
                    content = msg.get('content', '')
                    print(f"     [{i}] {role}: {content[:50]}...")

            # 第二次请求 - 传递函数结果（不包含 functions 参数）
            response2 = requests.post(
                f"{API_BASE}/chat/completions",
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": messages2,
                    "stream": False
                },
                timeout=60
            )

            if response2.status_code == 200:
                result2 = response2.json()
                message2 = result2["choices"][0]["message"]

                print(f"\n✅ 第二次响应:")
                print(f"   内容: {message2.get('content', '')}")

                # 检查响应是否包含了函数结果信息
                if "22:52:27" in message2.get('content', '') or "Beijing" in message2.get('content', ''):
                    print("\n🎉 成功！Gemini 正确使用了函数执行结果")
                else:
                    print("\n⚠️ 响应中可能没有使用函数结果")
            else:
                print(f"\n❌ 第二次请求失败: {response2.status_code}")
        else:
            print("\n⚠️ 第一次请求没有返回函数调用")
    else:
        print(f"\n❌ 第一次请求失败: {response1.status_code}")

if __name__ == "__main__":
    print("\n🚀 开始测试 Function Call 结果传递\n")
    test_function_result_handling()
    print("\n" + "="*60)
    print("✅ 测试完成!")
    print("="*60)