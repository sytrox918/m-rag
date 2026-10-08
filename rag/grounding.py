from typing import List, Dict, Any

class GroundingChecker:
    def check(self, evidence_pack: List[Dict[str, Any]]) -> str:
        if not evidence_pack:
            return "INSUFFICIENT"
            
        top_score = evidence_pack[0].get('score', 0)
        
        # Configurable thresholds
        if top_score > 0.015:
            return "FULL"
        elif top_score > 0.005:
            return "PARTIAL"
        else:
            return "INSUFFICIENT"

grounding_checker = GroundingChecker()
