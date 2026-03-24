from typing import List, Dict, Any, Generator, AsyncGenerator
from ..events import StreamEvent
from .base import BaseClient

class GeminiClient(BaseClient):
    def __init__(self, api_key: str = None):
        super().__init__()
        try:
            import google.generativeai as genai
            if api_key: # Only configure if API key is explicitly provided
                genai.configure(api_key=api_key)
            self.genai = genai
        except ImportError:
            raise ImportError("Please install google-generativeai: pip install google-generativeai")

    def _parse_content(self, content):
        if isinstance(content, str):
            return [content]
        elif isinstance(content, list):
            parts = []
            for item in content:
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif item.get("type") == "image_url":
                    # Parse data:image/jpeg;base64,...
                    url = item["image_url"]["url"]
                    if url.startswith("data:"):
                        mime_type = url.split(";")[0].split(":")[1]
                        base64_data = url.split(",")[1]
                        import base64
                        parts.append({
                            "mime_type": mime_type,
                            "data": base64.b64decode(base64_data)
                        })
                    else:
                        raise ValueError("Gemini client currently only supports base64 encoded images via data URIs in multimodal messages.")
            return parts
        return [str(content)]

    def _convert_messages(self, messages):
        history = []
        system_instruction = None
        for m in messages:
            if m["role"] == "system":
                system_instruction = m["content"]
            elif m["role"] == "user":
                history.append({"role": "user", "parts": self._parse_content(m["content"])})
            elif m["role"] == "assistant":
                history.append({"role": "model", "parts": self._parse_content(m["content"])})
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
        
        if hasattr(resp, 'usage_metadata') and resp.usage_metadata:
            self.track_usage(model, resp.usage_metadata.prompt_token_count, resp.usage_metadata.candidates_token_count)
            
        return {"content": resp.text, "raw": resp}

    async def chat_async(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        sys_inst, history = self._convert_messages(messages)
        model_obj = self.genai.GenerativeModel(model, system_instruction=sys_inst)
        last_msg = history.pop() if history and history[-1]["role"] == "user" else {"parts": [""]}
        
        config = self._get_generation_config(kwargs)
        chat = model_obj.start_chat(history=history)
        resp = await chat.send_message_async(last_msg["parts"][0], generation_config=config)
        
        if hasattr(resp, 'usage_metadata') and resp.usage_metadata:
            self.track_usage(model, resp.usage_metadata.prompt_token_count, resp.usage_metadata.candidates_token_count)
            
        return {"content": resp.text, "raw": resp}

    def chat_stream(self, model: str, messages: List[Dict], **kwargs) -> Generator[StreamEvent, None, None]:
        sys_inst, history = self._convert_messages(messages)
        model_obj = self.genai.GenerativeModel(model, system_instruction=sys_inst)
        last_msg = history.pop() if history and history[-1]["role"] == "user" else {"parts": [""]}
        
        config = self._get_generation_config(kwargs)
        chat = model_obj.start_chat(history=history)
        resp = chat.send_message(last_msg["parts"][0], stream=True, generation_config=config)
        for chunk in resp:
            if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata and chunk.usage_metadata.prompt_token_count > 0:
                self.track_usage(model, chunk.usage_metadata.prompt_token_count, chunk.usage_metadata.candidates_token_count)
            yield StreamEvent("token", chunk.text)

    async def chat_stream_async(self, model: str, messages: List[Dict], **kwargs) -> AsyncGenerator[StreamEvent, None]:
        sys_inst, history = self._convert_messages(messages)
        model_obj = self.genai.GenerativeModel(model, system_instruction=sys_inst)
        last_msg = history.pop() if history and history[-1]["role"] == "user" else {"parts": [""]}
        
        config = self._get_generation_config(kwargs)
        chat = model_obj.start_chat(history=history)
        resp = await chat.send_message_async(last_msg["parts"][0], stream=True, generation_config=config)
        async for chunk in resp:
            if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata and chunk.usage_metadata.prompt_token_count > 0:
                self.track_usage(model, chunk.usage_metadata.prompt_token_count, chunk.usage_metadata.candidates_token_count)
            yield StreamEvent("token", chunk.text)

    def generate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generates an image using Gemini's ImageGenerationModel."""
        model = kwargs.pop("model", "imagen-3.0-generate-001")
        imagen = self.genai.ImageGenerationModel(model)
        result = imagen.generate_images(
            prompt=prompt,
            number_of_images=kwargs.get("n", 1),
            aspect_ratio=kwargs.get("aspect_ratio", "1:1"),
            output_mime_type=kwargs.get("output_mime_type", "image/png")
        )
        images_data = []
        for img in result.images:
            images_data.append({
                "b64_json": img._image_bytes.decode('utf-8') if isinstance(img._image_bytes, bytes) else img._image_bytes
            })
        return {"data": images_data, "raw": result}

    async def generate_image_async(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Asynchronously generates an image using Gemini's ImageGenerationModel."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.generate_image(prompt, **kwargs))

    def speech_to_text(self, audio_file: Any, **kwargs) -> str:
        """Converts audio to text using Gemini's multimodal capabilities."""
        model_name = kwargs.pop("model", "gemini-1.5-flash")
        # Load audio data if it's a path, or use directly if bytes/file-like
        if isinstance(audio_file, str):
            with open(audio_file, "rb") as f:
                audio_data = f.read()
        elif hasattr(audio_file, "read"):
            audio_data = audio_file.read()
        else:
            audio_data = audio_file
            
        model = self.genai.GenerativeModel(model_name)
        prompt = kwargs.pop("prompt", "Transcribe the following audio accurately. Output only the transcription.")
        
        response = model.generate_content([
            prompt,
            {"mime_type": "audio/mpeg", "data": audio_data}
        ])
        return response.text

    async def speech_to_text_async(self, audio_file: Any, **kwargs) -> str:
        """Asynchronously converts audio to text using Gemini."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.speech_to_text(audio_file, **kwargs))
