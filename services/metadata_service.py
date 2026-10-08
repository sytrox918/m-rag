import json
import time
import concurrent.futures
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from langchain_groq import ChatGroq
from config.settings import settings

class UnitMetadata(BaseModel):
    unit_id: str = Field(description="The exact ID of the content unit")
    topics: List[str] = Field(description="Major topics covered in this unit")
    concepts: List[str] = Field(description="Key concepts and subtopics explained")
    prerequisites: List[str] = Field(description="Prior knowledge or terms needed to understand this unit")

class BatchMetadata(BaseModel):
    extracted_metadata: List[UnitMetadata] = Field(description="List of metadata for each unit")

class MetadataService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY or settings.ANSWER_API_KEY
        if self.api_key:
            self.llm = ChatGroq(
                temperature=0, 
                model_name=settings.ANSWER_MODEL, 
                api_key=self.api_key
            ).with_structured_output(BatchMetadata)
        else:
            self.llm = None

    def enrich_units(self, units: List['ContentUnit']):
        if not self.llm or not units:
            return
            
        # Process in batches of 15 to prevent context loss and stay under output token limits
        batch_size = 15
        batches = [units[i:i + batch_size] for i in range(0, len(units), batch_size)]
        
        def process_batch(batch):
            try:
                # Prepare input text
                prompt_text = "Extract topics, concepts, and prerequisites for each of the following content units:\n\n"
                for u in batch:
                    text_snippet = (u.searchable_text or "")[:1000] # Limit text length per unit to save tokens
                    prompt_text += f"--- UNIT ID: {u.id} ---\n{text_snippet}\n\n"
                
                # Sleep briefly to avoid Groq burst limits (30 RPM free tier)
                time.sleep(2)
                
                result = self.llm.invoke(prompt_text)
                
                # Map results back
                result_map = {m.unit_id: m for m in result.extracted_metadata}
                for u in batch:
                    if u.id in result_map:
                        meta = result_map[u.id]
                        u.topics = meta.topics
                        u.concepts = meta.concepts
                        u.prerequisites = meta.prerequisites
            except Exception as e:
                print(f"Error extracting metadata for batch: {e}")

        # Execute batches sequentially to safely avoid Groq rate limits
        for batch in batches:
            process_batch(batch)

metadata_service = MetadataService()
