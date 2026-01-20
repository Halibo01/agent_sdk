import requests
import httpx
import json
from typing import List, Dict, Any, Generator, AsyncGenerator
from ..events import StreamEvent
from .base import BaseClient

class OllamaClient(BaseClient):
    def __init__(self, api_key: str = None): # Renaming to api_key for consistency with engine.py
        self.base_url = api_key if api_key else "http://localhost:11434"
        self.session = requests.Session()

    def chat(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        resp = self.session.post(f"{self.base_url}/api/chat", json={"model": model, "messages": messages, "stream": False, **kwargs})
        resp.raise_for_status()
        data = resp.json()
        return {"content": data.get("message", {}).get("content"), "raw": data}

    async def chat_async(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/api/chat", json={"model": model, "messages": messages, "stream": False, **kwargs})
            resp.raise_for_status()
            data = resp.json()
        return {"content": data.get("message", {}).get("content"), "raw": data}

    def chat_stream(self, model: str, messages: List[Dict], **kwargs) -> Generator[StreamEvent, None, None]:
        with self.session.post(f"{self.base_url}/api/chat", json={"model": model, "messages": messages, "stream": True, **kwargs}, stream=True) as resp:
            for line in resp.iter_lines():
                if not line: continue
                obj = json.loads(line)
                if obj.get("done"): break
                yield StreamEvent("token", obj.get("message", {}).get("content", ""))

    async def chat_stream_async(self, model: str, messages: List[Dict], **kwargs) -> AsyncGenerator[StreamEvent, None]:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json={"model": model, "messages": messages, "stream": True, **kwargs}) as resp:
                async for line in resp.aiter_lines():
                    if not line: continue
                    obj = json.loads(line)
                    if obj.get("done"): break
                    yield StreamEvent("token", obj.get("message", {}).get("content", ""))
