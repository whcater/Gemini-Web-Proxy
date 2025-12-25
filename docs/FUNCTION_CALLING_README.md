# Function Calling 功能说明

## 概述
Gemini Web Proxy 现在支持 OpenAI Function Calling API 格式。系统会自动将函数定义转换为 Gemini 可以理解的提示词，并将 Gemini 的响应解析为标准的 OpenAI function calling 格式。

## 工作原理

### 1. 请求处理流程
1. **检测函数定义**：系统检测请求中的 `functions` 或 `tools` 参数
2. **生成提示词**：将函数定义转换为特殊格式的提示词，告诉 Gemini 如何格式化输出
3. **发送到 Gemini**：将增强后的提示词发送给 Gemini
4. **解析响应**：从 Gemini 的响应中提取函数调用信息
5. **格式转换**：转换为 OpenAI 兼容的响应格式

### 2. Gemini 响应格式
当需要调用函数时，Gemini 会按照以下格式返回：

```function_call
{
    "name": "function_name",
    "arguments": {
        "param1": "value1",
        "param2": "value2"
    }
}
```

### 3. OpenAI 响应格式
系统会将上述格式转换为标准的 OpenAI 格式：

```json
{
    "role": "assistant",
    "content": "可选的文本说明",
    "function_call": {
        "name": "function_name",
        "arguments": "{\"param1\":\"value1\",\"param2\":\"value2\"}"
    }
}
```

## 使用方法

### 基本示例
```python
import requests

# 定义函数
functions = [
    {
        "name": "getCurrentTime",
        "description": "Get the current time for a city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name"
                }
            },
            "required": ["city"]
        }
    }
]

# 发送请求
response = requests.post(
    "http://127.0.0.1:5000/v1/chat/completions",
    json={
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "What time is it in Beijing?"}
        ],
        "functions": functions,
        "function_call": "auto"  # 可选: "auto", "none", "required", 或函数名
    }
)

result = response.json()
message = result["choices"][0]["message"]

if "function_call" in message:
    print(f"函数: {message['function_call']['name']}")
    print(f"参数: {message['function_call']['arguments']}")
```

## 支持的功能

### ✅ 已支持
- OpenAI `functions` 参数
- OpenAI `tools` 参数（自动转换为 functions）
- `function_call` 模式：`auto`, `none`, `required`, 特定函数名
- 流式响应中的函数调用
- 非流式响应中的函数调用
- 多函数定义
- 可选和必需参数

### ⚠️ 注意事项
1. **Gemini 理解能力**：函数调用的成功率取决于 Gemini 对指令的理解
2. **格式严格性**：Gemini 必须严格按照指定格式返回，否则无法解析
3. **函数名匹配**：函数名必须与定义中的名称完全匹配

## 测试

运行测试脚本：
```bash
python test_function_calling.py
```

测试包括：
- 基本函数调用测试
- 天气查询函数测试
- 流式响应函数调用测试

## 调试

如果函数调用没有按预期工作：
1. 检查控制台输出，查看格式化后的提示词
2. 确认 Gemini 返回的格式是否正确
3. 启用 DEBUG 模式查看详细信息：
   ```python
   # config.py
   DEBUG = True
   ```

## 限制

1. **依赖提示词**：功能依赖于 Gemini 对提示词的理解和遵循
2. **格式要求**：Gemini 必须严格按照指定格式返回响应
3. **复杂函数**：对于非常复杂的函数定义，可能需要调整提示词模板