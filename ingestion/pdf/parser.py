import pymupdf
import uuid
from pathlib import Path
from docling.document_converter import DocumentConverter
from docling.chunking import HierarchicalChunker
from ingestion.common.content_units import ContentUnit
from config.settings import settings
from storage.vector_store import vector_store

class PDFParser:
    def __init__(self):
        self.converter = DocumentConverter()
        self.chunker = HierarchicalChunker()
        self.assets_dir = Path(settings.ASSETS_DIR)
        self.assets_dir.mkdir(exist_ok=True, parents=True)

    def parse(self, file_path: str, document_id: str = None) -> list[ContentUnit]:
        doc_id = document_id or str(uuid.uuid4())
        doc_name = Path(file_path).name
        
        # 1. Render pages
        vector_store.save_document(doc_id, doc_name, 'pdf')
        doc_fitz = pymupdf.open(file_path)
        page_assets = {}
        for i in range(len(doc_fitz)):
            page_num = i + 1
            page = doc_fitz[i]
            pix = page.get_pixmap(dpi=150)
            asset_id = str(uuid.uuid4())
            asset_path = self.assets_dir / f"{asset_id}.png"
            pix.save(str(asset_path))
            page_assets[page_num] = asset_id
            
            vector_store.save_asset(asset_id, doc_id, str(asset_path), "pdf_page")
            
        doc_fitz.close()
            
        # 2. Extract using Docling
        result = self.converter.convert(file_path)
        doc = result.document
        chunks = self.chunker.chunk(doc)
        
        content_units = []
        for chunk in chunks:
            page = None
            bbox = None
            asset_ids = []
            
            if chunk.meta.doc_items and len(chunk.meta.doc_items) > 0:
                first_item = chunk.meta.doc_items[0]
                if hasattr(first_item, 'prov') and first_item.prov:
                    page = first_item.prov[0].page_no
                    if hasattr(first_item.prov[0], 'bbox'):
                        b = first_item.prov[0].bbox
                        bbox = [b.l, b.t, b.r, b.b] if hasattr(b, 'l') else None
                        
            if page and page in page_assets:
                asset_ids.append(page_assets[page])
                        
            unit = ContentUnit(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                document_name=doc_name,
                source_type='pdf',
                title=chunk.meta.heading if hasattr(chunk.meta, 'heading') else None,
                text=chunk.text,
                page=page,
                bbox=bbox,
                asset_ids=asset_ids,
                extraction_methods={"text": "docling"}
            )
            content_units.append(unit)
            
        return content_units
