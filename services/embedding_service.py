from langchain_huggingface import HuggingFaceEmbeddings
from config.settings import settings
import os

class EmbeddingService:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # For bge-m3, we can use HuggingFaceEmbeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.model_name,
            model_kwargs={'device': device}, 
            encode_kwargs={'normalize_embeddings': True, 'batch_size': 32}
        )
        
    def embed_text(self, text: str) -> list[float]:
        return self.embeddings.embed_query(text)
        
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return self.embeddings.embed_documents(texts)

embedding_service = EmbeddingService()
