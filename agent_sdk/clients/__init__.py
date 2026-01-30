"""
Agent SDK Clients

Unified interface for interacting with various LLM providers.
All clients support both synchronous (`chat`, `chat_stream`) and asynchronous (`chat_stream_async`) execution.

Documentation: https://docs.agent-sdk-core.dev/modules/clients

Available Clients:
- **OpenAIClient**: Standard OpenAI API (and compatible like Grok, DeepSeek, Qwen).
- **GeminiClient**: Google's Gemini models.
- **AnthropicClient**: Claude models.
- **OllamaClient**: Local models via Ollama.
- **OpenRouterClient**: Unified access to many models via OpenRouter.
"""

from .base import BaseClient
from .openrouter import OpenRouterClient
from .ollama import OllamaClient
from .openai import OpenAIClient, GrokClient, DeepSeekClient, QwenClient, ZhipuClient
from .anthropic import AnthropicClient
from .gemini import GeminiClient

__all__ = [
    "BaseClient",
    "OpenRouterClient",
    "OllamaClient",
    "OpenAIClient",
    "GrokClient",
    "DeepSeekClient",
    "QwenClient",
    "ZhipuClient",
    "AnthropicClient",
    "GeminiClient"
]