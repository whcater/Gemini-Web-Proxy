"""
测试提示词生成，查看函数结果是否被正确包含
"""
from gemini_client_cdp_full import GeminiClientCDP

# 创建客户端实例
client = GeminiClientCDP()

# 模拟第二次请求的消息历史
messages = [
    {
        "content": "You are a helpful assistant that tells the current time in a city.",
        "role": "system"
    },
    {
        "content": "what time is it in china?",
        "role": "user"
    },
    {
        "role": "assistant",
        "function_call": {
            "name": "getCurrentTime",
            "arguments": "{\"city\": \"Beijing\"}"
        },
        "content": ""
    },
    {
        "role": "function",
        "name": "getCurrentTime",
        "content": "The current time in Beijing (Asia/Shanghai) is 2025-12-21 22:52:27"
    }
]

# 不包含 functions，模拟第二次请求
formatted_prompt = client._format_messages_to_prompt(messages)

print("="*60)
print("生成的提示词：")
print("="*60)
print(formatted_prompt)
print("="*60)