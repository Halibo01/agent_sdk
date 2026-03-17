from abc import ABC, abstractmethod
from typing import List, Any, Union

class BaseEmbeddingFunction(ABC):
    """
    Abstract base class for all custom embedding functions.
    Ensures compatibility with vector databases like ChromaDB.
    """
    
    @abstractmethod
    def __call__(self, input: Union[str, List[str]]) -> List[List[float]]:
        """
        Embeds the input (which could be text, or file paths for multimodal models).
        Must return a list of embeddings (list of floats).
        """
        pass
