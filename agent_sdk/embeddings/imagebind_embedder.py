import os
from typing import List, Union
from .base import BaseEmbeddingFunction

class ImageBindEmbeddingFunction(BaseEmbeddingFunction):
    """
    Multimodal Embedding Function using Meta's open-source ImageBind model.
    Runs entirely LOCALLY (No API key needed).
    
    Requires: pip install imagebind
    (Note: ImageBind requires PyTorch and potentially significant system resources).
    """
    
    def __init__(self, device: str = "cpu"):
        """
        Initializes the ImageBind model.
        Args:
            device (str): 'cuda' for GPU, 'cpu' for standard processing.
        """
        self.device = device
        try:
            import torch
            from imagebind import data
            from imagebind.models import imagebind_model
            from imagebind.models.imagebind_model import ModalityType
            
            self.ModalityType = ModalityType
            self.data = data
            self.torch = torch
            
            print(f"[ImageBind] Loading model to {self.device}... This may take a moment.")
            self.model = imagebind_model.imagebind_huge(pretrained=True)
            self.model.eval()
            self.model.to(self.device)
            print("[ImageBind] Model loaded successfully.")
            
        except ImportError:
            raise ImportError(
                "Please install imagebind to use this feature.\n"
                "Follow instructions at: https://github.com/facebookresearch/ImageBind"
            )

    def __call__(self, input: Union[str, List[str]]) -> List[List[float]]:
        """
        Generates embeddings for the provided inputs (Text, Image paths, Audio paths, Video paths).
        Compatible with ChromaDB's expected signature.
        """
        if isinstance(input, str):
            inputs = [input]
        else:
            inputs = input

        # Categorize inputs by modality based on file extensions
        texts = []
        vision_paths = [] # images and videos
        audio_paths = []
        
        # We need to preserve the original order of inputs to return embeddings correctly
        input_mapping = [] 

        for idx, item in enumerate(inputs):
            if os.path.isfile(item):
                ext = os.path.splitext(item)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.webp', '.mp4', '.avi']:
                    vision_paths.append(item)
                    input_mapping.append(("vision", len(vision_paths)-1))
                elif ext in ['.mp3', '.wav', '.flac']:
                    audio_paths.append(item)
                    input_mapping.append(("audio", len(audio_paths)-1))
                else:
                    # Fallback to text if unknown file type (though might not make sense)
                    texts.append(item)
                    input_mapping.append(("text", len(texts)-1))
            else:
                texts.append(item)
                input_mapping.append(("text", len(texts)-1))

        # Prepare inputs for the model
        model_inputs = {}
        if texts:
            model_inputs[self.ModalityType.TEXT] = self.data.load_and_transform_text(texts, self.device)
        if vision_paths:
            model_inputs[self.ModalityType.VISION] = self.data.load_and_transform_vision_data(vision_paths, self.device)
        if audio_paths:
            model_inputs[self.ModalityType.AUDIO] = self.data.load_and_transform_audio_data(audio_paths, self.device)

        # Generate embeddings
        with self.torch.no_grad():
            embeddings_dict = self.model(model_inputs)

        # Reconstruct the final list in the exact order of the original inputs
        final_embeddings = []
        for mod_type, list_idx in input_mapping:
            if mod_type == "text":
                emb = embeddings_dict[self.ModalityType.TEXT][list_idx].tolist()
            elif mod_type == "vision":
                emb = embeddings_dict[self.ModalityType.VISION][list_idx].tolist()
            elif mod_type == "audio":
                emb = embeddings_dict[self.ModalityType.AUDIO][list_idx].tolist()
            final_embeddings.append(emb)

        return final_embeddings
