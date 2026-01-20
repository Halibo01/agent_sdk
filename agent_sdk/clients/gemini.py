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

    def _get_generation_config(self, kwargs):
        generation_config = {}
        # Map common keys to Gemini's expected keys
        if "temperature" in kwargs: generation_config["temperature"] = kwargs["temperature"]
        if "top_p" in kwargs: generation_config["top_p"] = kwargs["top_p"]
        if "top_k" in kwargs: generation_config["top_k"] = kwargs["top_k"]
        if "max_output_tokens" in kwargs: generation_config["max_output_tokens"] = kwargs["max_output_tokens"]
        if "max_tokens" in kwargs: generation_config["max_output_tokens"] = kwargs["max_tokens"]
        if "stop_sequences" in kwargs: generation_config["stop_sequences"] = kwargs["stop_sequences"]
        if "stop" in kwargs: generation_config["stop_sequences"] = kwargs["stop"]
        
        return self.genai.types.GenerationConfig(**generation_config) if generation_config else None

    def chat(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        sys_inst, history = self._convert_messages(messages)
        model_obj = self.genai.GenerativeModel(model, system_instruction=sys_inst)
        last_msg = history.pop() if history and history[-1]["role"] == "user" else {"parts": [""]}
        
        config = self._get_generation_config(kwargs)
        chat = model_obj.start_chat(history=history)
        resp = chat.send_message(last_msg["parts"][0], generation_config=config)
        return {"content": resp.text, "raw": resp}

    async def chat_async(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        sys_inst, history = self._convert_messages(messages)
        model_obj = self.genai.GenerativeModel(model, system_instruction=sys_inst)
        last_msg = history.pop() if history and history[-1]["role"] == "user" else {"parts": [""]}
        
        config = self._get_generation_config(kwargs)
        chat = model_obj.start_chat(history=history)
        resp = await chat.send_message_async(last_msg["parts"][0], generation_config=config)
        return {"content": resp.text, "raw": resp}

    def chat_stream(self, model: str, messages: List[Dict], **kwargs) -> Generator[StreamEvent, None, None]:
        sys_inst, history = self._convert_messages(messages)
        model_obj = self.genai.GenerativeModel(model, system_instruction=sys_inst)
        last_msg = history.pop() if history and history[-1]["role"] == "user" else {"parts": [""]}
        
        config = self._get_generation_config(kwargs)
        chat = model_obj.start_chat(history=history)
        resp = chat.send_message(last_msg["parts"][0], stream=True, generation_config=config)
        for chunk in resp: yield StreamEvent("token", chunk.text)

    async def chat_stream_async(self, model: str, messages: List[Dict], **kwargs) -> AsyncGenerator[StreamEvent, None]:
        sys_inst, history = self._convert_messages(messages)
        model_obj = self.genai.GenerativeModel(model, system_instruction=sys_inst)
        last_msg = history.pop() if history and history[-1]["role"] == "user" else {"parts": [""]}
        
        config = self._get_generation_config(kwargs)
        chat = model_obj.start_chat(history=history)
        resp = await chat.send_message_async(last_msg["parts"][0], stream=True, generation_config=config)
        async for chunk in resp: yield StreamEvent("token", chunk.text)
