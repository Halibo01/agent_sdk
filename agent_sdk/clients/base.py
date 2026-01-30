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
