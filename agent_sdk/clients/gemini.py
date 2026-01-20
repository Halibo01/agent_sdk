from typing import List, Dict, Any, Generator, AsyncGenerator
from ..events import StreamEvent
from .base import BaseClient

class GeminiClient(BaseClient):
    def __init__(self, api_key: str = None):
        try:
            import google.generativeai as genai
            if api_key: # Only configure if API key is explicitly provided
                genai.configure(api_key=api_key)
            self.genai = genai
        except ImportError:
            raise ImportError("Please install google-generativeai: pip install google-generativeai")

    def _convert_messages(self, messages):
        history = []
        system_instruction = None
        for m in messages:
            if m["role"] == "system":
                system_instruction = m["content"]
            elif m["role"] == "user":
                history.append({"role": "user", "parts": [m["content"]]})
            elif m["role"] == "assistant":
                history.append({"role": "model", "parts": [m["content"]]})
        return system_instruction, history

    def chat(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        sys_inst, history = self._convert_messages(messages)
        model_obj = self.genai.GenerativeModel(model, system_instruction=sys_inst)
        last_msg = history.pop() if history and history[-1]["role"] == "user" else {"parts": [""]}
        
        chat = model_obj.start_chat(history=history)
        resp = chat.send_message(last_msg["parts"][0])
        return {"content": resp.text, "raw": resp}

    async def chat_async(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        sys_inst, history = self._convert_messages(messages)
        model_obj = self.genai.GenerativeModel(model, system_instruction=sys_inst)
        last_msg = history.pop() if history and history[-1]["role"] == "user" else {"parts": [""]}
        
        chat = model_obj.start_chat(history=history)
        resp = await chat.send_message_async(last_msg["parts"][0])
        return {"content": resp.text, "raw": resp}

    def chat_stream(self, model: str, messages: List[Dict], **kwargs) -> Generator[StreamEvent, None, None]:
        sys_inst, history = self._convert_messages(messages)
        model_obj = self.genai.GenerativeModel(model, system_instruction=sys_inst)
        last_msg = history.pop() if history and history[-1]["role"] == "user" else {"parts": [""]}
        
        chat = model_obj.start_chat(history=history)
        resp = chat.send_message(last_msg["parts"][0], stream=True)
        for chunk in resp: yield StreamEvent("token", chunk.text)

    async def chat_stream_async(self, model: str, messages: List[Dict], **kwargs) -> AsyncGenerator[StreamEvent, None]:
        sys_inst, history = self._convert_messages(messages)
        model_obj = self.genai.GenerativeModel(model, system_instruction=sys_inst)
        last_msg = history.pop() if history and history[-1]["role"] == "user" else {"parts": [""]}
        
        chat = model_obj.start_chat(history=history)
        resp = await chat.send_message_async(last_msg["parts"][0], stream=True)
        async for chunk in resp: yield StreamEvent("token", chunk.text)
