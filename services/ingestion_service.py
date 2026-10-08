import time
import uuid
from ingestion.pdf.parser import PDFParser
from ingestion.pptx.parser import PPTXParser
from ingestion.video.parser import VideoParser
from services.embedding_service import embedding_service
from storage.vector_store import vector_store

class IngestionService:
    def __init__(self):
        self.pdf_parser = PDFParser()
        self.pptx_parser = PPTXParser()
        self.video_parser = VideoParser()

    def ingest_pdf(self, file_path: str):
        start = time.time()
        units = self.pdf_parser.parse(file_path)
        if units:
            vector_store.save_document(units[0].document_id, units[0].document_name, 'pdf')
            self._process_and_save_units(units)
            
        return {
            "duration": time.time() - start,
            "units": len(units),
            "pages": len(set(u.page for u in units if u.page is not None))
        }

    def ingest_pptx(self, file_path: str):
        start = time.time()
        units = self.pptx_parser.parse(file_path)
        if units:
            vector_store.save_document(units[0].document_id, units[0].document_name, 'pptx')
            self._process_and_save_units(units)
            
        return {
            "duration": time.time() - start,
            "units": len(units),
            "slides": len(set(u.slide for u in units if u.slide is not None))
        }

    def ingest_video(self, url: str):
        start = time.time()
        units = self.video_parser.parse(url)
        if units:
            vector_store.save_document(units[0].document_id, units[0].document_name, 'video')
            self._process_and_save_units(units)
            
        return {
            "duration": time.time() - start,
            "units": len(units),
            "segments": len(units)
        }
        
    def _process_and_save_units(self, units):
        # Batch embed
        texts = [u.searchable_text for u in units]
        embeddings = embedding_service.embed_batch(texts)
        for unit, emb in zip(units, embeddings):
            unit.embedding = emb
            
        vector_store.save_content_units(units)

ingestion_service = IngestionService()
