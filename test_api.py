#!/usr/bin/env python3
"""
测试Gemini Web Proxy的API
"""
import requests
import json
import time

def test_non_streaming():
    """测试非流式响应"""
    print("\n" + "="*60)
    print("测试非流式API")
    print("="*60 + "\n")

    url = "http://127.0.0.1:5000/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-key"
    }

    data = {
        "model": "gemini-pro",
        "messages": [
            {"role": "user", "content": "how to be rich"}
        ],
        "stream": False
    }

    print(f"📤 发送请求到: {url}")
    print(f"   消息: {data['messages'][0]['content']}")

    start_time = time.time()

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        elapsed = time.time() - start_time

        print(f"\n⏱  响应时间: {elapsed:.2f} 秒")
        print(f"📥 状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("\n✅ 收到响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            # 检查响应格式
            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0].get("message", {})
                content = message.get("content", "")
                reasoning = message.get("reasoning_content", "")

                if reasoning:
                    print(f"\n💭 思维链 ({len(reasoning)} 字符):")
                    print(f"   {reasoning[:200]}...")

                if content:
                    print(f"\n📝 正文 ({len(content)} 字符):")
                    print(f"   {content[:200]}...")
                else:
                    print("\n⚠️  响应中没有正文内容!")
            else:
                print("\n⚠️  响应格式不正确，缺少choices字段!")
        else:
            print(f"\n❌ 请求失败:")
            print(response.text)

    except requests.exceptions.Timeout:
        print(f"\n❌ 请求超时（60秒）")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")


def test_streaming():
    """测试流式响应"""
    print("\n" + "="*60)
    print("测试流式API")
    print("="*60 + "\n")

    url = "http://127.0.0.1:5000/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-key"
    }

    data = {
        "model": "gemini-pro",
        "messages": [
            {"role": "user", "content": "tell me a short joke"}
        ],
        "stream": True
    }

    print(f"📤 发送请求到: {url}")
    print(f"   消息: {data['messages'][0]['content']}")

    start_time = time.time()

    try:
        response = requests.post(url, headers=headers, json=data, stream=True, timeout=60)

        print(f"\n📥 状态码: {response.status_code}")

        if response.status_code == 200:
            print("\n开始接收流式响应:")
            print("-" * 40)

            full_content = ""
            full_reasoning = ""
            chunk_count = 0

            for line in response.iter_lines():
                if line:
                    chunk_count += 1
                    decoded = line.decode('utf-8')

                    if decoded.startswith("data: "):
                        data_str = decoded[6:]

                        if data_str == "[DONE]":
                            break

                        try:
                            chunk_data = json.loads(data_str)
                            if "choices" in chunk_data:
                                delta = chunk_data["choices"][0].get("delta", {})

                                if "reasoning_content" in delta:
                                    reasoning = delta["reasoning_content"]
                                    full_reasoning += reasoning
                                    print(f"[思维] {reasoning}", end="", flush=True)

                                if "content" in delta:
                                    content = delta["content"]
                                    full_content += content
                                    print(content, end="", flush=True)
                        except json.JSONDecodeError:
                            print(f"\n⚠️  无法解析的数据块: {data_str[:100]}")

            elapsed = time.time() - start_time
            print("\n" + "-" * 40)
            print(f"\n✅ 流式响应完成:")
            print(f"   接收了 {chunk_count} 个数据块")
            print(f"   总时间: {elapsed:.2f} 秒")

            if full_reasoning:
                print(f"   思维链长度: {len(full_reasoning)} 字符")

            if full_content:
                print(f"   正文长度: {len(full_content)} 字符")
            else:
                print("   ⚠️  没有接收到正文内容!")
        else:
            print(f"\n❌ 请求失败:")
            print(response.text)

    except requests.exceptions.Timeout:
        print(f"\n❌ 请求超时（60秒）")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")


if __name__ == "__main__":
    import sys

    print("\n🚀 开始测试 Gemini Web Proxy API")
    print("   请确保服务器正在运行: python main.py")

    # 检查服务器是否运行
    try:
        response = requests.get("http://127.0.0.1:5000/health", timeout=2)
        if response.status_code == 200:
            print("✅ 服务器正在运行")
        else:
            print(f"⚠️  服务器响应异常，状态码: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请先运行: python main.py")
        print("\n请在另一个终端中运行服务器后再测试")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 检查服务器状态时出错: {e}")
        sys.exit(1)

    # 测试非流式响应
    test_non_streaming()

    print("\n" + "="*60)

    # 检查是否在交互式环境中运行
    if sys.stdin.isatty():
        input("按回车键继续测试流式响应...")
    else:
        print("自动继续测试流式响应...")
        time.sleep(1)

    # 测试流式响应
    test_streaming()

    print("\n✅ 测试完成!")