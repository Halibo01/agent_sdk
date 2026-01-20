from typing import List, Dict, Any, Generator, AsyncGenerator
from ..events import StreamEvent
from .base import BaseClient

class AnthropicClient(BaseClient):
    def __init__(self, api_key: str = None):
        try:
            from anthropic import Anthropic, AsyncAnthropic
            self.client = Anthropic(api_key=api_key)
            self.async_client = AsyncAnthropic(api_key=api_key)
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")

    def _prep_msgs(self, messages):
        system = next((m["content"] for m in messages if m["role"] == "system"), None)
        msgs = [m for m in messages if m["role"] != "system"]
        return system, msgs

    def _clean_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filters kwargs to include only parameters supported by Anthropic API.
        """
        supported_params = {
            "temperature", "top_p", "top_k", "max_tokens", "stop_sequences",
            "metadata", "timeout"
        }
        
        cleaned = {}
        for k, v in kwargs.items():
            if k in supported_params:
                cleaned[k] = v
            # Common mappings
            elif k == "max_output_tokens":
                cleaned["max_tokens"] = v
            elif k == "stop":
                cleaned["stop_sequences"] = v if isinstance(v, list) else [v]
                
        return cleaned

    def chat(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        system, msgs = self._prep_msgs(messages)
        params = self._clean_kwargs(kwargs)
        # Ensure max_tokens defaults to 1024 if not provided
        if "max_tokens" not in params: params["max_tokens"] = 1024
        
        resp = self.client.messages.create(model=model, messages=msgs, system=system, **params)
        return {"content": resp.content[0].text, "raw": resp}

    async def chat_async(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        system, msgs = self._prep_msgs(messages)
        params = self._clean_kwargs(kwargs)
        if "max_tokens" not in params: params["max_tokens"] = 1024

        resp = await self.async_client.messages.create(model=model, messages=msgs, system=system, **params)
        return {"content": resp.content[0].text, "raw": resp}

    def chat_stream(self, model: str, messages: List[Dict], **kwargs) -> Generator[StreamEvent, None, None]:
        system, msgs = self._prep_msgs(messages)
        params = self._clean_kwargs(kwargs)
        if "max_tokens" not in params: params["max_tokens"] = 1024

        with self.client.messages.stream(model=model, messages=msgs, system=system, **params) as stream:
            for text in stream.text_stream: yield StreamEvent("token", text)

    async def chat_stream_async(self, model: str, messages: List[Dict], **kwargs) -> AsyncGenerator[StreamEvent, None]:
        system, msgs = self._prep_msgs(messages)
        params = self._clean_kwargs(kwargs)
        if "max_tokens" not in params: params["max_tokens"] = 1024

        stream = await self.async_client.messages.create(model=model, messages=msgs, system=system, stream=True, **params)
        async for event in stream:
            if event.type == 'content_block_delta' and event.delta.type == 'text_delta':
                yield StreamEvent("token", event.delta.text)
