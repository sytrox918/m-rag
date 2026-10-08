from pptx import Presentation
import uuid
from ingestion.common.content_units import ContentUnit
from pathlib import Path

class PPTXParser:
    def parse(self, file_path: str, document_id: str = None) -> list[ContentUnit]:
        doc_id = document_id or str(uuid.uuid4())
        doc_name = Path(file_path).name
        
        prs = Presentation(file_path)
        content_units = []
        
        for i, slide in enumerate(prs.slides):
            slide_number = i + 1
            
            text_parts = []
            title = None
            
            if slide.shapes.title:
                title = slide.shapes.title.text
                
            for shape in slide.shapes:
                if not shape.has_text_frame:
                    continue
                for paragraph in shape.text_frame.paragraphs:
                    if paragraph.text.strip():
                        text_parts.append(paragraph.text.strip())
                        
            text = "\n".join(text_parts)
            
            if title or text:
                unit = ContentUnit(
                    id=str(uuid.uuid4()),
                    document_id=doc_id,
                    document_name=doc_name,
                    source_type='pptx',
                    title=title,
                    text=text,
                    slide=slide_number
                )
                content_units.append(unit)
                
        return content_units
