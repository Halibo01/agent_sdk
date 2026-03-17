import os
from typing import List, Union
from .base import BaseEmbeddingFunction

class GeminiMultimodalEmbedding(BaseEmbeddingFunction):
    """
    Multimodal Embedding Function using Google's Gemini Models.
    Requires 'google-generativeai' package and GEMINI_API_KEY.
    
    Can process text and images (via base64 or file paths).
    """
    
    def __init__(self, api_key: str = None, model_name: str = "models/gemini-embedding-2-preview"):
        self.model_name = model_name
        try:
            import google.generativeai as genai
            self.genai = genai
            
            # Configure with provided key or fallback to environment variable
            key = api_key or os.environ.get("GEMINI_API_KEY")
            if not key:
                raise ValueError("GEMINI_API_KEY not found. Please provide it or set the environment variable.")
            self.genai.configure(api_key=key)
            
        except ImportError:
            raise ImportError("Please install google-generativeai: pip install google-generativeai")

    def _process_single_input(self, input_item: str) -> dict:
        """
        Determines if the input is a local file (image/video/audio) or plain text,
        and formats it correctly for the Gemini API.
        """
        # If it's a file path and it exists
        if os.path.isfile(input_item):
            ext = os.path.splitext(input_item)[1].lower()
            
            # Simple mime-type mapping for common local files
            mime_types = {
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp',
                '.mp3': 'audio/mpeg', '.wav': 'audio/wav',
                '.mp4': 'video/mp4', '.mpeg': 'video/mpeg', '.mov': 'video/quicktime',
                '.pdf': 'application/pdf'
            }
            
            if ext in mime_types:
                # Read local file
                with open(input_item, "rb") as f:
                    file_bytes = f.read()
                return {"mime_type": mime_types[ext], "data": file_bytes}
            
        # If not a recognized file, treat as plain text
        return input_item

    def __call__(self, input: Union[str, List[str]]) -> List[List[float]]:
        """
        Generates embeddings for the provided inputs.
        Compatible with ChromaDB's expected signature.
        """
        if isinstance(input, str):
            inputs = [input]
        else:
            inputs = input

        embeddings = []
        for item in inputs:
            processed_content = self._process_single_input(item)
            
            result = self.genai.embed_content(
                model=self.model_name,
                contents=[processed_content]
            )
            
            # Gemini returns 'embedding' directly in the result dictionary
            embeddings.append(result['embedding'])
            
        return embeddings
