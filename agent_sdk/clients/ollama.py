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

    def _prepare_payload(self, model: str, messages: List[Dict], stream: bool, **kwargs) -> Dict[str, Any]:
        """
        Prepares the payload for Ollama API, moving generation parameters into 'options'.
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        # Ollama expects parameters in 'options' dict
        # See: https://github.com/ollama/ollama/blob/main/docs/api.md#generate-request
        options = {}
        supported_options = {
            "num_keep", "seed", "num_predict", "top_k", "top_p", "tfs_z", 
            "typical_p", "repeat_last_n", "temperature", "repeat_penalty", 
            "presence_penalty", "frequency_penalty", "mirostat", "mirostat_tau",
            "mirostat_eta", "penalize_newline", "stop"
        }

        for k, v in kwargs.items():
            if k in supported_options:
                options[k] = v
            # Mappings
            elif k == "max_tokens" or k == "max_output_tokens":
                options["num_predict"] = v
            elif k == "stop_sequences":
                options["stop"] = v
        
        if options:
            payload["options"] = options
            
        return payload

    def chat(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        payload = self._prepare_payload(model, messages, stream=False, **kwargs)
        resp = self.session.post(f"{self.base_url}/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return {"content": data.get("message", {}).get("content"), "raw": data}

    async def chat_async(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        payload = self._prepare_payload(model, messages, stream=False, **kwargs)
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
        return {"content": data.get("message", {}).get("content"), "raw": data}

    def chat_stream(self, model: str, messages: List[Dict], **kwargs) -> Generator[StreamEvent, None, None]:
        payload = self._prepare_payload(model, messages, stream=True, **kwargs)
        with self.session.post(f"{self.base_url}/api/chat", json=payload, stream=True) as resp:
            for line in resp.iter_lines():
                if not line: continue
                obj = json.loads(line)
                if obj.get("done"): break
                yield StreamEvent("token", obj.get("message", {}).get("content", ""))

    async def chat_stream_async(self, model: str, messages: List[Dict], **kwargs) -> AsyncGenerator[StreamEvent, None]:
        payload = self._prepare_payload(model, messages, stream=True, **kwargs)
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as resp:
                async for line in resp.aiter_lines():
                    if not line: continue
                    obj = json.loads(line)
                    if obj.get("done"): break
                    yield StreamEvent("token", obj.get("message", {}).get("content", ""))
