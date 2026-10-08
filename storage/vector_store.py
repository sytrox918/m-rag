from typing import List
from storage.postgres import get_db, DocumentModel, ContentUnitModel
from ingestion.common.content_units import ContentUnit

class VectorStore:
    def __init__(self):
        pass

    def save_document(self, doc_id: str, name: str, source_type: str):
        db = next(get_db())
        try:
            doc = DocumentModel(id=doc_id, name=name, source_type=source_type)
            db.merge(doc)
            db.commit()
        finally:
            db.close()

    def save_asset(self, asset_id: str, document_id: str, file_path: str, asset_type: str):
        db = next(get_db())
        try:
            from storage.postgres import AssetModel
            asset = AssetModel(id=asset_id, document_id=document_id, file_path=file_path, asset_type=asset_type)
            db.merge(asset)
            db.commit()
        finally:
            db.close()

    def save_content_units(self, units: List[ContentUnit]):
        db = next(get_db())
        try:
            for unit in units:
                db_unit = ContentUnitModel(
                    id=unit.id,
                    document_id=unit.document_id,
                    document_name=unit.document_name,
                    source_type=unit.source_type,
                    title=unit.title,
                    text=unit.text,
                    searchable_text=unit.searchable_text,
                    ocr_text=unit.ocr_text,
                    visual_description=unit.visual_description,
                    equations=unit.equations,
                    tables=unit.tables,
                    topics=unit.topics,
                    concepts=unit.concepts,
                    prerequisites=unit.prerequisites,
                    page=unit.page,
                    slide=unit.slide,
                    start_time=unit.start_time,
                    end_time=unit.end_time,
                    bbox=unit.bbox,
                    asset_ids=unit.asset_ids,
                    extraction_methods=unit.extraction_methods,
                    extraction_confidence=unit.extraction_confidence,
                    parent_unit_id=unit.parent_unit_id,
                    metadata_json=unit.metadata,
                    embedding=unit.embedding
                )
                db.merge(db_unit)
            db.commit()
        finally:
            db.close()

vector_store = VectorStore()
