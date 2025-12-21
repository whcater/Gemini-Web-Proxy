"""
Function Calling 支持模块
处理 OpenAI 格式的 function calling 请求，
将其转换为 Gemini 可以理解的格式，
并将 Gemini 的响应转换回 OpenAI 兼容格式
"""
import json
import re
from typing import Optional, Dict, Any, List


class FunctionCallingHandler:
    """处理 Function Calling 的转换"""

    def __init__(self):
        self.functions_map = {}
        self.current_functions = []

    def format_functions_to_prompt(self, functions: List[Dict], function_call: str = "auto") -> str:
        """
        将 OpenAI 格式的 functions 转换为提示词
        告诉 Gemini 如何格式化响应
        """
        if not functions:
            return ""

        self.current_functions = functions
        self.functions_map = {func['name']: func for func in functions}

        prompt = """
[FUNCTION CALLING MODE]
You have access to the following functions. You must respond in a specific format to call functions.

Available functions:
"""
        for func in functions:
            name = func.get('name', '')
            description = func.get('description', '')
            parameters = func.get('parameters', {})
            properties = parameters.get('properties', {})
            required = parameters.get('required', [])

            prompt += f"\n{name}: {description}\n"
            if properties:
                prompt += "  Parameters:\n"
                for param_name, param_info in properties.items():
                    param_type = param_info.get('type', 'string')
                    param_desc = param_info.get('description', '')
                    is_required = param_name in required
                    prompt += f"    - {param_name} ({param_type}{'*' if is_required else ''}): {param_desc}\n"

        prompt += """
IMPORTANT RESPONSE FORMAT:
When you need to call a function, respond EXACTLY in this format:
```function_call
{
    "name": "function_name",
    "arguments": {
        "param1": "value1",
        "param2": "value2"
    }
}
```

After the function call block, you can provide additional explanation or context in plain text.
If you don't need to call any function, just respond normally.

Remember:
1. Always use the exact function names provided above
2. Arguments must match the parameter specifications
3. Use JSON format inside the function_call code block
4. Required parameters (marked with *) must be included
"""

        if function_call == "required" or function_call != "auto":
            if function_call not in ["auto", "required", "none"]:
                # 特定函数名
                prompt += f"\n[REQUIRED] You MUST call the function: {function_call}"
            elif function_call == "required":
                prompt += "\n[REQUIRED] You MUST call one of the available functions."

        return prompt

    def parse_gemini_response(self, response: str) -> tuple[Optional[Dict], str]:
        """
        解析 Gemini 的响应，提取 function call 信息
        返回: (function_call_dict, remaining_text)
        """
        # 查找 function_call 代码块
        pattern = r'```function_call\s*(.*?)\s*```'
        matches = re.findall(pattern, response, re.DOTALL)

        if not matches:
            # 没有函数调用，返回原文本
            return None, response

        # 获取第一个函数调用
        function_call_json = matches[0].strip()

        try:
            function_call = json.loads(function_call_json)

            # 验证函数调用格式
            if not isinstance(function_call, dict):
                return None, response

            function_name = function_call.get('name')
            arguments = function_call.get('arguments', {})

            # 验证函数名是否存在
            if function_name not in self.functions_map:
                print(f"⚠️ 未知的函数名: {function_name}")
                return None, response

            # 移除 function_call 块，保留其余文本
            remaining_text = re.sub(pattern, '', response, count=1).strip()

            return {
                "name": function_name,
                "arguments": json.dumps(arguments) if isinstance(arguments, dict) else arguments
            }, remaining_text

        except json.JSONDecodeError as e:
            print(f"⚠️ 解析 function_call JSON 失败: {e}")
            return None, response

    def format_to_openai_response(self, function_call: Optional[Dict], text: str, model: str = "gpt-3.5-turbo") -> Dict:
        """
        将解析后的结果转换为 OpenAI 格式的响应
        """
        message = {"role": "assistant"}

        if function_call:
            # 有函数调用
            message["content"] = text if text else None
            message["function_call"] = function_call
        else:
            # 没有函数调用，纯文本响应
            message["content"] = text

        return message

    def format_streaming_chunk(self, function_call: Optional[Dict], text: str, is_first: bool = False, is_done: bool = False) -> str:
        """
        格式化为流式响应的 SSE 格式
        """
        import time

        if is_done:
            return "data: [DONE]\n\n"

        chunk_data = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "gpt-3.5-turbo",
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": None
            }]
        }

        if is_first:
            chunk_data["choices"][0]["delta"]["role"] = "assistant"
            if function_call:
                chunk_data["choices"][0]["delta"]["function_call"] = {
                    "name": function_call["name"],
                    "arguments": ""
                }
        elif function_call:
            # 流式传输函数参数
            chunk_data["choices"][0]["delta"]["function_call"] = {
                "arguments": function_call.get("arguments", "")
            }
        else:
            # 流式传输文本内容
            chunk_data["choices"][0]["delta"]["content"] = text

        return f"data: {json.dumps(chunk_data)}\n\n"

    def should_use_function_calling(self, request_data: Dict) -> bool:
        """
        判断请求是否需要使用 function calling
        """
        return bool(request_data.get('functions')) or bool(request_data.get('tools'))

    def convert_tools_to_functions(self, tools: List[Dict]) -> List[Dict]:
        """
        将新版本的 tools 格式转换为 functions 格式
        OpenAI 的新 API 使用 tools 而不是 functions
        """
        functions = []
        for tool in tools:
            if tool.get('type') == 'function':
                function = tool.get('function', {})
                functions.append(function)
        return functions