from typing import List, Dict, Any, Generator, AsyncGenerator, Optional
from ..events import StreamEvent
from .base import BaseClient

class OpenAIClient(BaseClient):
    def __init__(self, api_key: str = None, base_url: Optional[str] = None):
        try:
            from openai import OpenAI, AsyncOpenAI
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        except ImportError:
            raise ImportError("Please install openai: pip install openai")

    def chat(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        resp = self.client.chat.completions.create(model=model, messages=messages, **kwargs)
        msg = resp.choices[0].message
        return {"content": msg.content, "tool_calls": [tc.model_dump() for tc in msg.tool_calls] if msg.tool_calls else None, "raw": resp}

    async def chat_async(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        resp = await self.async_client.chat.completions.create(model=model, messages=messages, **kwargs)
        msg = resp.choices[0].message
        return {"content": msg.content, "tool_calls": [tc.model_dump() for tc in msg.tool_calls] if msg.tool_calls else None, "raw": resp}

    def chat_stream(self, model: str, messages: List[Dict], **kwargs) -> Generator[StreamEvent, None, None]:
        stream = self.client.chat.completions.create(model=model, messages=messages, stream=True, **kwargs)
        for chunk in stream:
            if not chunk.choices: continue
            delta = chunk.choices[0].delta
            if delta.content: yield StreamEvent("token", delta.content)
            if delta.tool_calls:
                for tc in delta.tool_calls: yield StreamEvent("tool_call", tc.model_dump())

    async def chat_stream_async(self, model: str, messages: List[Dict], **kwargs) -> AsyncGenerator[StreamEvent, None]:
        stream = await self.async_client.chat.completions.create(model=model, messages=messages, stream=True, **kwargs)
        async for chunk in stream:
            if not chunk.choices: continue
            delta = chunk.choices[0].delta
            if delta.content: yield StreamEvent("token", delta.content)
            if delta.tool_calls:
                for tc in delta.tool_calls: yield StreamEvent("tool_call", tc.model_dump())

class GrokClient(OpenAIClient):
    def __init__(self, api_key: str): super().__init__(api_key=api_key, base_url="https://api.x.ai/v1")

class DeepSeekClient(OpenAIClient):
    def __init__(self, api_key: str): super().__init__(api_key=api_key, base_url="https://api.deepseek.com/v1")

class QwenClient(OpenAIClient):
    def __init__(self, api_key: str, base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"): super().__init__(api_key=api_key, base_url=base_url)

class ZhipuClient(OpenAIClient):
    def __init__(self, api_key: str): super().__init__(api_key=api_key, base_url="https://open.bigmodel.cn/api/paas/v4/")
