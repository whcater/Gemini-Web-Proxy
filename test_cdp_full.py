#!/usr/bin/env python
"""
测试CDP完整版本
"""
import requests
import json
import time

def test_simple_request():
    """测试简单请求"""
    url = "http://127.0.0.1:5000/v1/chat/completions"

    data = {
        "model": "gemini-pro",
        "messages": [
            {"role": "user", "content": "你好，请简短地告诉我今天是几号？"}
        ],
        "stream": False
    }

    print("📤 发送测试请求...")
    print(f"   URL: {url}")
    print(f"   消息: {data['messages'][0]['content']}")

    try:
        response = requests.post(url, json=data, timeout=120)

        if response.status_code == 200:
            result = response.json()
            print("\n✅ 请求成功!")

            # 提取响应内容
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"].get("content", "")
                reasoning = result["choices"][0]["message"].get("reasoning_content", "")

                if reasoning:
                    print(f"\n💭 思维链:")
                    print(f"   {reasoning[:200]}..." if len(reasoning) > 200 else f"   {reasoning}")

                if content:
                    print(f"\n📝 响应内容:")
                    print(f"   {content}")

                print(f"\n📊 统计:")
                print(f"   模型: {result.get('model', 'unknown')}")
                print(f"   完成原因: {result['choices'][0].get('finish_reason', 'unknown')}")
            else:
                print(f"\n⚠️ 响应格式异常:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"\n❌ 请求失败: HTTP {response.status_code}")
            print(response.text)

    except requests.exceptions.Timeout:
        print("\n⚠️ 请求超时（120秒）")
    except Exception as e:
        print(f"\n❌ 错误: {e}")


def test_streaming():
    """测试流式响应"""
    url = "http://127.0.0.1:5000/v1/chat/completions"

    data = {
        "model": "gemini-pro",
        "messages": [
            {"role": "user", "content": "计算 1+1 等于多少？"}
        ],
        "stream": True
    }

    print("\n📤 发送流式测试请求...")
    print(f"   消息: {data['messages'][0]['content']}")

    try:
        response = requests.post(url, json=data, stream=True, timeout=120)

        if response.status_code == 200:
            print("\n✅ 开始接收流式响应:")

            full_content = ""
            full_reasoning = ""

            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            print("\n✅ 流式响应完成")
                            break

                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    content = delta["content"]
                                    full_content += content
                                    print(content, end="", flush=True)
                                if "reasoning_content" in delta:
                                    reasoning = delta["reasoning_content"]
                                    full_reasoning += reasoning
                        except json.JSONDecodeError:
                            pass

            if full_reasoning:
                print(f"\n\n💭 思维链: {full_reasoning[:200]}..." if len(full_reasoning) > 200 else f"\n\n💭 思维链: {full_reasoning}")

            if full_content:
                print(f"\n\n📝 完整响应: {full_content}")
        else:
            print(f"\n❌ 请求失败: HTTP {response.status_code}")
            print(response.text)

    except requests.exceptions.Timeout:
        print("\n⚠️ 请求超时（120秒）")
    except Exception as e:
        print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    print("="*60)
    print("CDP 完整版本测试")
    print("="*60)

    # 测试非流式请求
    test_simple_request()

    # 等待一下
    time.sleep(2)

    # 测试流式请求
    test_streaming()

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)