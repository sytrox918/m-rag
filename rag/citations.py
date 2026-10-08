from typing import List, Dict, Any

class CitationValidator:
    def validate(self, claims: List[Dict[str, Any]], evidence_docs: List[Any]) -> List[Dict[str, Any]]:
        valid_evidence_ids = {doc.metadata["evidence_id"]: doc for doc in evidence_docs}
        
        validated_claims = []
        for claim in claims:
            valid_claim_evidence = []
            for eid in claim["evidence_ids"]:
                if eid in valid_evidence_ids:
                    doc = valid_evidence_ids[eid]
                    
                    if doc.metadata['source_type'] == 'pdf' and doc.metadata['page'] is None:
                        continue
                    if doc.metadata['source_type'] == 'pptx' and doc.metadata['slide'] is None:
                        continue
                    if doc.metadata['source_type'] == 'video' and doc.metadata['start_time'] is None:
                        continue
                        
                    valid_claim_evidence.append(eid)
                    
            if valid_claim_evidence:
                claim["evidence_ids"] = valid_claim_evidence
                validated_claims.append(claim)
                
        return validated_claims

citation_validator = CitationValidator()
