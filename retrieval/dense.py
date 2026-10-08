from sqlalchemy import select
from storage.postgres import get_db, ContentUnitModel
from services.embedding_service import embedding_service
from typing import List, Dict, Any

class DenseRetriever:
    def retrieve(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        query_embedding = embedding_service.embed_text(query)
        db = next(get_db())
        try:
            stmt = select(ContentUnitModel).order_by(
                ContentUnitModel.embedding.cosine_distance(query_embedding)
            ).limit(top_k)
            
            results = db.execute(stmt).scalars().all()
            
            return [{
                "unit": result,
                # We can approximate score by taking 1 - distance, but order is more important for RRF
                "score": 1.0 # placeholder score, order is what matters for RRF
            } for result in results]
        finally:
            db.close()

dense_retriever = DenseRetriever()
