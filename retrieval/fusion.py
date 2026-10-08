from typing import List, Dict, Any

class ReciprocalRankFusion:
    def fuse(self, dense_results: List[Dict[str, Any]], sparse_results: List[Dict[str, Any]], k: int = 60, top_n: int = 10) -> List[Dict[str, Any]]:
        scores = {}
        units_map = {}
        
        def add_to_rrf(results, weight=1.0):
            for rank, item in enumerate(results):
                unit_id = item['unit'].id
                units_map[unit_id] = item['unit']
                if unit_id not in scores:
                    scores[unit_id] = 0.0
                scores[unit_id] += weight / (k + rank + 1)
                
        add_to_rrf(dense_results)
        add_to_rrf(sparse_results)
        
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        return [{
            "unit": units_map[unit_id],
            "score": score
        } for unit_id, score in sorted_results]

rrf = ReciprocalRankFusion()
