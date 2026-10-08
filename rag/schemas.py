from pydantic import BaseModel
from typing import List

class Claim(BaseModel):
    claim_id: str
    text: str
    evidence_ids: List[str]

class Answer(BaseModel):
    answer: str
    claims: List[Claim]
