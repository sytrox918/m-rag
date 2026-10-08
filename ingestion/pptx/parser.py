from pathlib import Path
from docling.document_converter import DocumentConverter
from docling.chunking import HierarchicalChunker
import uuid
from ingestion.common.content_units import ContentUnit

class PPTXParser:
    def __init__(self):
        self.converter = DocumentConverter()
        self.chunker = HierarchicalChunker()

    def parse(self, file_path: str, document_id: str = None) -> list[ContentUnit]:
        doc_id = document_id or str(uuid.uuid4())
        doc_name = Path(file_path).name
        
        result = self.converter.convert(file_path)
        doc = result.document
        chunks = self.chunker.chunk(doc)
        
        content_units = []
        for chunk in chunks:
            slide = None
            if chunk.meta.doc_items and len(chunk.meta.doc_items) > 0:
                first_item = chunk.meta.doc_items[0]
                if hasattr(first_item, 'prov') and first_item.prov:
                    slide = first_item.prov[0].page_no
                    
            unit = ContentUnit(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                document_name=doc_name,
                source_type='pptx',
                title=chunk.meta.heading if hasattr(chunk.meta, 'heading') else None,
                text=chunk.text,
                slide=slide,
                extraction_methods={"text": "docling"}
            )
            content_units.append(unit)
            
        return content_units
