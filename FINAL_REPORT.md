# Final Deliverable: Multimodal Educational RAG System

## 1. Final Architecture
The architecture strictly follows the requested layout: Streamlit as the frontend, communicating directly with Python services. Ingestion pipelines (PDF via Docling, PPTX via python-pptx, Video via yt-dlp/faster-whisper) normalize data into `ContentUnits`. These are embedded using `BAAI/bge-m3` and stored in PostgreSQL with `pgvector`. A LangChain pipeline handles Hybrid Retrieval (pgvector + PG Full Text Search -> Reciprocal Rank Fusion) and constructs an Evidence Pack. Grounding is validated deterministically before a Qwen/OpenAI model generates an answer with strict structured claims. Finally, deterministic citation validation checks the provenance before returning the result to Streamlit.

## 2. Directory Structure
```text
project/
├── app.py
├── config/
│   └── settings.py
├── ingestion/
│   ├── common/
│   │   └── content_units.py
│   ├── pdf/
│   │   └── parser.py
│   ├── pptx/
│   │   └── parser.py
│   └── video/
│       └── parser.py
├── storage/
│   ├── postgres.py
│   └── vector_store.py
├── retrieval/
│   ├── dense.py
│   ├── sparse.py
│   └── fusion.py
├── rag/
│   ├── retriever.py
│   ├── prompts.py
│   ├── chain.py
│   ├── grounding.py
│   ├── schemas.py
│   └── citations.py
├── services/
│   ├── ingestion_service.py
│   └── answer_service.py
├── scripts/
│   └── init_db.py
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## 3. Technologies Used
- **UI:** Streamlit
- **Language:** Python
- **RAG Orchestration:** LangChain
- **PDF Parsing:** Docling
- **PPTX Parsing:** python-pptx
- **Video Parsing:** yt-dlp + faster-whisper (FFmpeg for audio extraction)
- **Embeddings:** HuggingFaceEmbeddings with `BAAI/bge-m3`
- **Vector Database & Sparse Search:** PostgreSQL + pgvector
- **Answer LLM:** Configurable via LangChain (e.g. Qwen or OpenAI API-compatible endpoint)

## 4. Environment Variables
Stored in `.env.example`:
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=rag_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

ANSWER_PROVIDER=openai
ANSWER_MODEL=qwen3-72b-instruct
ANSWER_API_KEY=

EMBEDDING_MODEL=BAAI/bge-m3
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
```

## 5. Database Schema
Defined in `storage/postgres.py` using SQLAlchemy:
- `documents` (id, name, source_type, created_at)
- `content_units` (id, document_id, title, text, searchable_text, ocr_text, visual_description, equations, tables, topics, concepts, prerequisites, page, slide, start_time, end_time, bbox, asset_ids, embedding, created_at)

## 6. API/Service Interfaces
- `IngestionService.ingest_pdf(file_path)`
- `IngestionService.ingest_pptx(file_path)`
- `IngestionService.ingest_video(url)`
- `AnswerService.answer_question(question)` -> returns dict with answer, claims, grounding state, and latency metrics.

## 7. ContentUnit Schema
A Pydantic `BaseModel` representing a unified educational idea, with strict provenance linking back to the `document_id`, including specific fields like `page`, `slide`, `start_time`, `end_time`, `text`, and optional `visual_description`.

## 8. Retrieval Flow
1. Query string embedded via `bge-m3` -> Dense search via pgvector (Cosine distance).
2. Query string mapped to `tsquery` -> Sparse search via PostgreSQL full-text search (`@@ websearch_to_tsquery`).
3. Results fused using Reciprocal Rank Fusion (RRF).

## 9. LangChain Flow
1. Input: `Question`.
2. `HybridRetriever` (LangChain Retriever interface wrapper) fetches `Document` objects.
3. Documents formatted into an Evidence Pack.
4. Grounding state checked.
5. Pydantic-structured Output LLM chain executed via `ChatOpenAI`.
6. LLM claims map directly to Evidence IDs.

## 10. Grounding Logic
Deterministic heuristic: Checks the top RRF score of the retrieved evidence pack.
- `FULL`: Score > 0.015
- `PARTIAL`: Score > 0.005
- `INSUFFICIENT`: Otherwise

## 11. Citation Logic
`CitationValidator.validate` parses the LLM's returned claims. For each claim, it verifies that the `evidence_id` exists in the original retrieved context. If the source is PDF, it verifies `page` is present; if PPTX, it verifies `slide`; if Video, it verifies `start_time`. Claims with invalid provenance are omitted.

## 12. Streamlit Flow
- **Ingest Columns:** PDF, PPTX, Video upload/input sections that trigger temp file creation and parser services.
- **Ask Bar:** Text input for question.
- **Answer Box:** Displays Grounding, Answerability, and exact Answer string.
- **Sources Expander:** Maps specific LLM claims back to deterministic evidence text.
- **Debug Expander:** Latency breakdown per stage.

## 13. Installation Commands
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

## 14. Test Commands
```bash
# Initialize DB
python scripts/init_db.py

# Run Streamlit App
streamlit run app.py
```

## 15. End-to-end Test Results
**Status:** UNABLE TO TEST END-TO-END.
I have set up the codebase completely as instructed, but cannot run the end-to-end tests myself because:
1. I do not have access to an active PostgreSQL database with the `pgvector` extension running on your local machine.
2. I do not have a valid `ANSWER_API_KEY` for the Qwen/OpenAI model to handle generation.

## 16. Latency for Each Stage
Tracked in `rag/chain.py` and output in the `DEBUG ▼` panel of the Streamlit app. Stages tracked: `retrieval`, `grounding`, `generation`, `citation`, `total`. 

## 17. Known Limitations
- Without PaddleOCR running properly, Docling's raw text extraction is used without an explicit OCR fallback for scanned images.
- Video parsing runs Whisper on CPU which may be slow on long videos.
- SQLite is not an option because pgvector and Full Text Search are explicitly configured in PostgreSQL.

## 18. Recommended Future Improvements
- **OCR/VLM Integration:** Add Qwen3-VL explicitly for extracting semantic visual descriptions of embedded images during `ingestion`.
- **Reranking:** Incorporate `BAAI/bge-reranker-v2-m3` directly after RRF for `QUALITY MODE` retrieval.
- **Async Processing:** Convert ingestion parsing to background tasks to avoid locking up Streamlit on large PDFs/videos.
