import requests
import httpx
import json
from typing import List, Dict, Any, Generator, AsyncGenerator
from ..events import StreamEvent
from .base import BaseClient

class OpenRouterClient(BaseClient):
    def __init__(self, api_key: str = None, base_url: str = "https://openrouter.ai/api"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        
        if api_key is None:
            import os
            api_key = os.environ.get("OPENROUTER_API_KEY")
        
        if not api_key:
            raise ValueError("OpenRouter API key is required. Provide it via argument or OPENROUTER_API_KEY environment variable.")
            
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "agent-sdk/1.0"
        }
        self.session.headers.update(self.headers)

    def _clean_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps common parameter names to OpenRouter/OpenAI compatible names.
        OpenRouter is quite flexible, so we mostly pass through, but handle known mappings.
        """
        cleaned = kwargs.copy()
        
        # Common mappings
        if "max_output_tokens" in cleaned:
            cleaned["max_tokens"] = cleaned.pop("max_output_tokens")
        if "stop_sequences" in cleaned:
            cleaned["stop"] = cleaned.pop("stop_sequences")
            
        return cleaned

    def chat(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        params = self._clean_kwargs(kwargs)
        resp = self.session.post(f"{self.base_url}/v1/chat/completions", json={"model": model, "messages": messages, **params})
        resp.raise_for_status()
        data = resp.json()
        choice = data["choices"][0]
        return {"content": choice["message"].get("content"), "tool_calls": choice["message"].get("tool_calls"), "raw": data}

    async def chat_async(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        params = self._clean_kwargs(kwargs)
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/v1/chat/completions", json={"model": model, "messages": messages, **params}, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
        choice = data["choices"][0]
        return {"content": choice["message"].get("content"), "tool_calls": choice["message"].get("tool_calls"), "raw": data}

    def chat_stream(self, model: str, messages: List[Dict], **kwargs) -> Generator[StreamEvent, None, None]:
        params = self._clean_kwargs(kwargs)
        # Ensure stream is True
        params["stream"] = True
        with self.session.post(f"{self.base_url}/v1/chat/completions", json={"model": model, "messages": messages, **params}, stream=True) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                yield from self._process_line(line)

    async def chat_stream_async(self, model: str, messages: List[Dict], **kwargs) -> AsyncGenerator[StreamEvent, None]:
        params = self._clean_kwargs(kwargs)
        # Ensure stream is True
        params["stream"] = True
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", f"{self.base_url}/v1/chat/completions", json={"model": model, "messages": messages, **params}, headers=self.headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    for event in self._process_line(line.encode('utf-8')): yield event

    def _process_line(self, line_bytes):
        if not line_bytes: return
        line = line_bytes.decode("utf-8", errors="ignore").strip()
        if line.startswith("data:"): line = line[5:].strip()
        if line == "[DONE]": yield StreamEvent("final", None); return
        try:
            obj = json.loads(line)
            if not obj.get("choices"): return
            delta = obj["choices"][0].get("delta", {})
            if "reasoning" in delta: yield StreamEvent("reasoning", delta["reasoning"])
            if "tool_calls" in delta: 
                for tc in delta["tool_calls"]: yield StreamEvent("tool_call", tc)
            if "content" in delta and delta["content"]: yield StreamEvent("token", delta["content"])
        except: pass
