from abc import ABC, abstractmethod
from typing import Any, Dict, List, Generator, AsyncGenerator
from ..events import StreamEvent

class BaseClient(ABC):
    """
    Common interface that all LLM providers must adhere to.
    """
    def __init__(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.estimated_cost = 0.0
        
        # Rough cost per 1M tokens (prompt, completion)
        self.PRICING_TABLE = {
            "gpt-4o": (5.0, 15.0),
            "gpt-4o-mini": (0.15, 0.60),
            "claude-3-5-sonnet-20240620": (3.0, 15.0),
            "claude-3-haiku-20240307": (0.25, 1.25),
            "gemini-1.5-pro": (3.5, 10.5),
            "gemini-1.5-flash": (0.075, 0.30),
            "meta-llama/llama-3.1-8b-instruct:free": (0.0, 0.0),
            "openai/gpt-4o-mini": (0.15, 0.60), # OpenRouter fallback
        }

    def track_usage(self, model: str, prompt_t: int, completion_t: int):
        """Updates the token counts and estimates cost based on the model."""
        self.prompt_tokens += prompt_t
        self.completion_tokens += completion_t
        
        # Estimate cost
        prices = self.PRICING_TABLE.get(model, (0.0, 0.0))
        cost = (prompt_t / 1_000_000) * prices[0] + (completion_t / 1_000_000) * prices[1]
        self.estimated_cost += cost

    def get_cost_summary(self) -> Dict[str, Any]:
        """Returns a summary of token usage and estimated costs."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.prompt_tokens + self.completion_tokens,
            "estimated_cost_usd": round(self.estimated_cost, 6)
        }

    @abstractmethod
    def chat(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]: pass

    @abstractmethod
    async def chat_async(self, model: str, messages: List[Dict], **kwargs) -> Dict[str, Any]: pass

    @abstractmethod
    def chat_stream(self, model: str, messages: List[Dict], **kwargs) -> Generator[StreamEvent, None, None]: pass

    @abstractmethod
    async def chat_stream_async(self, model: str, messages: List[Dict], **kwargs) -> AsyncGenerator[StreamEvent, None]: pass

    @abstractmethod
    def generate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generates an image from a text prompt.
        Should return a dictionary with at least a 'url' or 'b64_json' key.
        """
        pass

    @abstractmethod
    async def generate_image_async(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Asynchronously generates an image from a text prompt.
        """
        pass

    @abstractmethod
    def speech_to_text(self, audio_file: Any, **kwargs) -> str:
        """
        Converts speech from an audio file to text.
        """
        pass

    @abstractmethod
    async def speech_to_text_async(self, audio_file: Any, **kwargs) -> str:
        """
        Asynchronously converts speech from an audio file to text.
        """
        pass
