from langchain_huggingface import HuggingFaceEmbeddings
from config.settings import settings
import os

class EmbeddingService:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        # For bge-m3, we can use HuggingFaceEmbeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.model_name,
            model_kwargs={'device': 'cpu'}, # Can be set to cuda if available
            encode_kwargs={'normalize_embeddings': True}
        )
        
    def embed_text(self, text: str) -> list[float]:
        return self.embeddings.embed_query(text)
        
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return self.embeddings.embed_documents(texts)

embedding_service = EmbeddingService()
