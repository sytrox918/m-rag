from sqlalchemy import text
from storage.postgres import get_db, ContentUnitModel
from typing import List, Dict, Any

class SparseRetriever:
    def retrieve(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        db = next(get_db())
        try:
            stmt = text("""
                SELECT id, ts_rank_cd(to_tsvector('english', coalesce(searchable_text, '')), websearch_to_tsquery('english', :query)) AS rank
                FROM content_units
                WHERE to_tsvector('english', coalesce(searchable_text, '')) @@ websearch_to_tsquery('english', :query)
                ORDER BY rank DESC
                LIMIT :top_k
            """)
            
            result = db.execute(stmt, {"query": query, "top_k": top_k}).mappings().all()
            
            ids = [r['id'] for r in result]
            if not ids:
                return []
                
            units = db.query(ContentUnitModel).filter(ContentUnitModel.id.in_(ids)).all()
            unit_map = {u.id: u for u in units}
            
            # Preserve order from the query results
            return [{
                "unit": unit_map[r['id']],
                "score": r['rank']
            } for r in result if r['id'] in unit_map]
            
        finally:
            db.close()

sparse_retriever = SparseRetriever()
