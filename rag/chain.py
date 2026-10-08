import time
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from config.settings import settings
from rag.prompts import ANSWER_PROMPT, STANDALONE_QUERY_PROMPT
from rag.schemas import Answer
from rag.retriever import HybridRetriever
from rag.grounding import grounding_checker
from rag.citations import citation_validator

class RAGChain:
    def __init__(self):
        provider = settings.ANSWER_PROVIDER.lower()
        if provider == "groq":
            self.llm = ChatGroq(
                model_name=settings.ANSWER_MODEL,
                api_key=settings.ANSWER_API_KEY or "dummy_key"
            )
        else:
            self.llm = ChatOpenAI(
                model=settings.ANSWER_MODEL,
                api_key=settings.ANSWER_API_KEY or "dummy_key",
                base_url="https://api.openai.com/v1" if provider == "openai" else None
            )
        self.structured_llm = self.llm.with_structured_output(Answer)
        self.retriever = HybridRetriever()

    def process(self, question: str, chat_history: list = None):
        start = time.time()
        
        # Format chat history (Sliding Window: Keep only the last 3 conversational turns to save tokens)
        formatted_history = ""
        if chat_history:
            recent_history = chat_history[-6:] # 3 user + 3 assistant messages
            for msg in recent_history:
                formatted_history += f"{msg['role'].upper()}: {msg['content']}\n"
                
        # Contextualize query if there is history
        search_query = question
        if chat_history:
            prompt_val = STANDALONE_QUERY_PROMPT.invoke({
                "chat_history": formatted_history,
                "question": question
            })
            from langchain_core.output_parsers import StrOutputParser
            search_query = (self.llm | StrOutputParser()).invoke(prompt_val).strip()
        
        retrieval_start = time.time()
        docs = self.retriever.invoke(search_query)
        retrieval_time = time.time() - retrieval_start
        
        evidence_pack = []
        evidence_text_parts = []
        
        for doc in docs:
            evidence_pack.append({"score": doc.metadata["score"], "unit_id": doc.metadata["content_unit_id"]})
            
            src_info = f"Source: {doc.metadata['document_name']}"
            if doc.metadata['page']:
                src_info += f", Page: {doc.metadata['page']}"
            elif doc.metadata['slide']:
                src_info += f", Slide: {doc.metadata['slide']}"
            elif doc.metadata['start_time'] is not None:
                src_info += f", Timestamp: {doc.metadata['start_time']} - {doc.metadata['end_time']}"
                
            evidence_text_parts.append(f"[{doc.metadata['evidence_id']}] {src_info}\n{doc.page_content}")
            
        evidence_text = "\n\n".join(evidence_text_parts)
        
        grounding_start = time.time()
        grounding_state = grounding_checker.check(evidence_pack)
        grounding_time = time.time() - grounding_start
        
        generation_start = time.time()
        if grounding_state == "INSUFFICIENT":
            answer = "The provided material does not contain enough information to answer this."
            claims = []
        else:
            prompt_val = ANSWER_PROMPT.invoke({
                "chat_history": formatted_history,
                "evidence_text": evidence_text,
                "question": question,
                "grounding_state": grounding_state
            })
            
            try:
                result = self.structured_llm.invoke(prompt_val)
                answer = result.answer
                claims = [c.model_dump() for c in result.claims]
            except Exception as e:
                answer = f"Error generating answer: {e}"
                claims = []
                
        generation_time = time.time() - generation_start
        
        citation_start = time.time()
        validated_claims = citation_validator.validate(claims, docs)
        citation_time = time.time() - citation_start
        
        total_time = time.time() - start
        
        return {
            "answer": answer,
            "claims": validated_claims,
            "grounding": grounding_state,
            "evidence": [d.metadata for d in docs],
            "evidence_docs": docs,
            "latency": {
                "retrieval": retrieval_time,
                "grounding": grounding_time,
                "generation": generation_time,
                "citation": citation_time,
                "total": total_time
            }
        }

rag_chain = RAGChain()
