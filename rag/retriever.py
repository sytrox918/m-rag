from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from typing import List
from retrieval.dense import dense_retriever
from retrieval.sparse import sparse_retriever
from retrieval.fusion import rrf

class HybridRetriever(BaseRetriever):
    top_k: int = 10
    
    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        
        dense_res = dense_retriever.retrieve(query, top_k=self.top_k * 2)
        sparse_res = sparse_retriever.retrieve(query, top_k=self.top_k * 2)
        
        fused = rrf.fuse(dense_res, sparse_res, top_n=self.top_k)
        
        docs = []
        for rank, item in enumerate(fused):
            unit = item['unit']
            docs.append(Document(
                page_content=unit.searchable_text or "",
                metadata={
                    "evidence_id": f"evidence_{rank+1}",
                    "content_unit_id": unit.id,
                    "source_type": unit.source_type,
                    "document_name": unit.document_name,
                    "page": unit.page,
                    "slide": unit.slide,
                    "start_time": unit.start_time,
                    "end_time": unit.end_time,
                    "score": item['score']
                }
            ))
        return docs
