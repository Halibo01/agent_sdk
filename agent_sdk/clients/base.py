from abc import ABC, abstractmethod
from typing import Any, Dict, List, Generator, AsyncGenerator
from ..events import StreamEvent

class BaseClient(ABC):
    """
    Common interface that all LLM providers must adhere to.
    """
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
