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
        t0 = time.time()
        
        # 1. Parsing
        t_parse_start = time.time()
        units = self.pdf_parser.parse(file_path)
        t_parse = time.time() - t_parse_start
        
        t_vlm = 0
        t_meta = 0
        t_embed = 0
        t_save = 0
        
        if units:
            vector_store.save_document(units[0].document_id, units[0].document_name, 'pdf')
            t_vlm, t_meta, t_embed, t_save = self._process_and_save_units(units)
            
        return {
            "total_duration": time.time() - t0,
            "latency": {
                "parsing": t_parse,
                "vlm": t_vlm,
                "metadata_extraction": t_meta,
                "embedding": t_embed,
                "database": t_save
            },
            "units": len(units),
            "pages": len(set(u.page for u in units if u.page is not None))
        }

    def ingest_pptx(self, file_path: str):
        t0 = time.time()
        
        t_parse_start = time.time()
        units = self.pptx_parser.parse(file_path)
        t_parse = time.time() - t_parse_start
        
        t_vlm = 0
        t_meta = 0
        t_embed = 0
        t_save = 0
        
        if units:
            vector_store.save_document(units[0].document_id, units[0].document_name, 'pptx')
            t_vlm, t_meta, t_embed, t_save = self._process_and_save_units(units)
            
        return {
            "total_duration": time.time() - t0,
            "latency": {
                "parsing": t_parse,
                "vlm": t_vlm,
                "metadata_extraction": t_meta,
                "embedding": t_embed,
                "database": t_save
            },
            "units": len(units),
            "slides": len(set(u.slide for u in units if u.slide is not None))
        }

    def ingest_video(self, url: str):
        t0 = time.time()
        
        t_parse_start = time.time()
        units = self.video_parser.parse(url)
        t_parse = time.time() - t_parse_start
        
        t_vlm = 0
        t_meta = 0
        t_embed = 0
        t_save = 0
        
        if units:
            vector_store.save_document(units[0].document_id, units[0].document_name, 'video')
            t_vlm, t_meta, t_embed, t_save = self._process_and_save_units(units)
            
        return {
            "total_duration": time.time() - t0,
            "latency": {
                "parsing_and_transcribing": t_parse,
                "vlm": t_vlm,
                "metadata_extraction": t_meta,
                "embedding": t_embed,
                "database": t_save
            },
            "units": len(units),
            "segments": len(units)
        }
        
    def _process_and_save_units(self, units):
        # 1. VLM Processing (Parallel)
        t_vlm_start = time.time()
        from services.vlm_service import vlm_service
        from config.settings import settings
        from pathlib import Path
        import concurrent.futures
        
        assets_dir = Path(settings.ASSETS_DIR)
        
        def process_unit_vlm(unit):
            descriptions = []
            if unit.asset_ids:
                for asset_id in unit.asset_ids:
                    asset_file = assets_dir / f"{asset_id}.png"
                    if not asset_file.exists():
                        asset_file = assets_dir / f"{asset_id}.jpg"
                    
                    if asset_file.exists():
                        desc = vlm_service.describe_image(str(asset_file))
                        if desc:
                            descriptions.append(desc)
            
            if descriptions:
                unit.visual_description = "\n\n".join(descriptions)
                # Append visual description so it gets embedded for semantic search!
                if unit.searchable_text:
                    unit.searchable_text += f"\n\n[Visual Description: {unit.visual_description}]"
                else:
                    unit.searchable_text = f"[Visual Description: {unit.visual_description}]"

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(process_unit_vlm, units)
            
        t_vlm = time.time() - t_vlm_start

        # 1.5 Metadata Extraction (Topics, Concepts, Prerequisites)
        t_meta_start = time.time()
        from services.metadata_service import metadata_service
        metadata_service.enrich_units(units)
        
        # Append extracted metadata to searchable text to improve embedding quality
        for unit in units:
            meta_text = ""
            if unit.topics: meta_text += f"\nTopics: {', '.join(unit.topics)}"
            if unit.concepts: meta_text += f"\nConcepts: {', '.join(unit.concepts)}"
            if unit.prerequisites: meta_text += f"\nPrerequisites: {', '.join(unit.prerequisites)}"
            if meta_text and unit.searchable_text:
                unit.searchable_text += f"\n\n[Extracted Metadata]{meta_text}"
                
        t_meta = time.time() - t_meta_start

        # 2. Batch embed
        t_embed_start = time.time()
        texts = [u.searchable_text or "" for u in units]
        embeddings = embedding_service.embed_batch(texts)
        for unit, emb in zip(units, embeddings):
            unit.embedding = emb
        t_embed = time.time() - t_embed_start
            
        # 3. Save to database
        t_save_start = time.time()
        vector_store.save_content_units(units)
        t_save = time.time() - t_save_start
        
        return t_vlm, t_meta, t_embed, t_save

ingestion_service = IngestionService()
