from typing import List, Dict, Any, Generator, AsyncGenerator, Optional
from ..events import StreamEvent
from .base import BaseClient
import asyncio
import os

class LlamaCppClient(BaseClient):
    """
    Client for running local .gguf models using llama-cpp-python.
    Supports GBNF grammars, Tool Calls, and Smart VRAM Swapping!
    """
    # Tracks the currently active model instance for VRAM swapping
    _active_instance = None 

    def __init__(self, model_path: str, n_ctx: int = 8192, preload_all: bool = False, n_gpu_layers: int = -1, **kwargs):
        super().__init__()
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.kwargs = kwargs
        self.preload_all = preload_all
        
        self.llm = None
        # Rough pricing: Local models are free!
        self.PRICING_TABLE[model_path] = (0.0, 0.0) 

        if self.preload_all:
            self._load_model()

    def _unload_model(self):
        """Removes the model from VRAM and runs Garbage Collection."""
        if self.llm is not None:
            print(f"\n[LlamaCppClient] Unloading: {os.path.basename(self.model_path)}")
            
            # 1. Try to explicitly close the C++ backend pointers (if supported by the llama-cpp version)
            if hasattr(self.llm, 'close'):
                try:
                    self.llm.close()
                except Exception:
                    pass
                    
            # 2. Delete the Python object reference
            del self.llm
            self.llm = None
            
            # 3. Force Python Garbage Collector
            import gc
            gc.collect()
            
            # 4. Give the OS a moment to reclaim the VRAM blocks
            import time
            time.sleep(1.5)

    def _load_model(self):
        """Loads the model into VRAM. If another model is occupying it, it unloads that one first."""
        if self.llm is not None:
            return # Zaten yüklü
            
        # Eğer Preload_All kapalıysa ve RAM'de başka bir model varsa, onu sil!
        if not self.preload_all:
            if LlamaCppClient._active_instance is not None and LlamaCppClient._active_instance is not self:
                LlamaCppClient._active_instance._unload_model()
        
        try:
            from llama_cpp import Llama
            
            ctx = self.n_ctx
            if ctx == 0:
                ctx = 8192 
                print(f"[LlamaCppClient] Akıllı Limit Devrede: Modelin maksimum bağlamı okundu, ancak güvenlik için {ctx} token ile sınırlandırıldı.")

            print(f"\n[LlamaCppClient] 🚀 VRAM'e Yükleniyor: {os.path.basename(self.model_path)}")
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=ctx,
                n_gpu_layers=self.n_gpu_layers,
                verbose=False,
                **self.kwargs
            )
            
            # Bu modeli 'Aktif Model' olarak işaretle
            if not self.preload_all:
                LlamaCppClient._active_instance = self
                
        except ImportError:
            raise ImportError(
                "Please install llama-cpp-python to use local GGUF models: "
                "pip install llama-cpp-python"
            )

    def _prepare_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Cleans and prepares arguments, handling GBNF grammar conversion."""
        cleaned = kwargs.copy()
        
        # Mapping common names to llama-cpp
        if "max_output_tokens" in cleaned:
            cleaned["max_tokens"] = cleaned.pop("max_output_tokens")
            
        # Handle strict GBNF grammar strings
        grammar_str = cleaned.pop("grammar", None)
        if grammar_str and isinstance(grammar_str, str):
            from llama_cpp import LlamaGrammar
            cleaned["grammar"] = LlamaGrammar.from_string(grammar_str)
            
        return cleaned

    def chat(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        self._load_model()
        params = self._prepare_kwargs(kwargs)
        
        resp = self.llm.create_chat_completion(
            messages=messages,
            **params
        )
        
        if "usage" in resp:
            u = resp["usage"]
            self.track_usage(self.model_path, u.get("prompt_tokens", 0), u.get("completion_tokens", 0))
            
        choice = resp["choices"][0]
        msg = choice.get("message", {})
        return {
            "content": msg.get("content"), 
            "tool_calls": msg.get("tool_calls"),
            "raw": resp
        }

    async def chat_async(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        return await asyncio.to_thread(self.chat, model, messages, **kwargs)

    def chat_stream(self, model: str, messages: List[Dict], **kwargs) -> Generator[StreamEvent, None, None]:
        self._load_model()
        params = self._prepare_kwargs(kwargs)
        params["stream"] = True
        
        stream = self.llm.create_chat_completion(
            messages=messages,
            **params
        )
        
        for chunk in stream:
            choices = chunk.get("choices", [])
            if not choices: continue
            
            delta = choices[0].get("delta", {})
            if "content" in delta and delta["content"]:
                yield StreamEvent("token", delta["content"])
            if "tool_calls" in delta and delta["tool_calls"]:
                for tc in delta["tool_calls"]:
                    yield StreamEvent("tool_call", tc)

    async def chat_stream_async(self, model: str, messages: List[Dict], **kwargs) -> AsyncGenerator[StreamEvent, None]:
        self._load_model()
        params = self._prepare_kwargs(kwargs)
        params["stream"] = True
        
        stream = await asyncio.to_thread(self.llm.create_chat_completion, messages=messages, **params)
        
        for chunk in stream:
            choices = chunk.get("choices", [])
            if not choices: continue
            
            delta = choices[0].get("delta", {})
            if "content" in delta and delta["content"]:
                yield StreamEvent("token", delta["content"])
            if "tool_calls" in delta and delta["tool_calls"]:
                for tc in delta["tool_calls"]:
                    yield StreamEvent("tool_call", tc)
            await asyncio.sleep(0)

    def generate_image(self, prompt: str, **kwargs):
        raise NotImplementedError("LlamaCppClient does not support image generation.")

    async def generate_image_async(self, prompt: str, **kwargs):
        raise NotImplementedError("LlamaCppClient does not support image generation.")

    def speech_to_text(self, audio_file, **kwargs):
        raise NotImplementedError("LlamaCppClient does not support speech-to-text.")

    async def speech_to_text_async(self, audio_file, **kwargs):
        raise NotImplementedError("LlamaCppClient does not support speech-to-text.")