#!/usr/bin/env python3
"""
调试Gemini Web Proxy - 查看原始响应
"""
import asyncio
from gemini_client import get_client
import config

async def test_direct():
    """直接测试GeminiClient"""
    try:
        print("初始化客户端...")
        client = await get_client()

        messages = [
            {"role": "user", "content": "say hello"}
        ]

        print("发送消息...")
        response_count = 0
        async for response in client.send_message(messages, model="gemini-pro"):
            response_count += 1
            print(f"\n响应 #{response_count}:")
            print(f"类型: {type(response)}")
            print(f"内容: {response}")

            # 如果收到足够的响应就退出
            if response_count > 5:
                print("\n收到足够的响应，退出测试")
                break

        if response_count == 0:
            print("❌ 没有收到任何响应")
        else:
            print(f"\n✅ 总共收到 {response_count} 个响应")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 确保启用调试模式
    config.DEBUG = True
    asyncio.run(test_direct())