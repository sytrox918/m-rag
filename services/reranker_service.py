import torch
from sentence_transformers import CrossEncoder
from config.settings import settings

class RerankerService:
    def __init__(self):
        # We use a lightweight cross-encoder to save memory while providing massive accuracy gains
        # BAAI/bge-reranker-v2-m3 is very strong for multilingual RAG
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = settings.RERANKER_MODEL
        print(f"Loading Reranker Model: {self.model_name} on {self.device}")
        
        # Load the model lazily to save startup time if not used immediately
        self._model = None
        
    @property
    def model(self):
        if self._model is None:
            self._model = CrossEncoder(self.model_name, device=self.device)
        return self._model

    def rerank(self, query: str, documents: list[str], top_k: int = 5) -> list[dict]:
        """
        Reranks a list of document strings based on the query.
        Returns a list of dicts with 'index' and 'score', sorted by highest score.
        """
        if not documents:
            return []
            
        pairs = [[query, doc] for doc in documents]
        scores = self.model.predict(pairs)
        
        # Combine indices and scores, then sort descending
        ranked = [{"index": i, "score": float(scores[i])} for i in range(len(scores))]
        ranked.sort(key=lambda x: x["score"], reverse=True)
        
        return ranked[:top_k]

reranker_service = RerankerService()
