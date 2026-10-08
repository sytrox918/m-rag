from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ContentUnit(BaseModel):
    id: str

    document_id: str
    document_name: str
    source_type: str  # 'pdf', 'pptx', 'video'

    title: Optional[str] = None
    text: Optional[str] = None

    ocr_text: Optional[str] = None
    visual_description: Optional[str] = None
    equations: List[str] = Field(default_factory=list)
    tables: List[Dict[str, Any]] = Field(default_factory=list)

    topics: List[str] = Field(default_factory=list)
    concepts: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)

    page: Optional[int] = None
    slide: Optional[int] = None

    start_time: Optional[float] = None
    end_time: Optional[float] = None

    bbox: Optional[List[float]] = None

    asset_ids: List[str] = Field(default_factory=list)

    extraction_methods: Dict[str, str] = Field(default_factory=dict)
    extraction_confidence: Dict[str, float] = Field(default_factory=dict)
    parent_unit_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    embedding: Optional[List[float]] = None

    @property
    def searchable_text(self) -> str:
        parts = []
        if self.title:
            parts.append(self.title)
        if self.text:
            parts.append(self.text)
        if self.visual_description:
            parts.append(self.visual_description)
        if self.ocr_text:
            parts.append(self.ocr_text)
        if self.concepts:
            parts.append(", ".join(self.concepts))
        if self.topics:
            parts.append(", ".join(self.topics))
        
        return " | ".join(parts)
