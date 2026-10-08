# Multimodal RAG System Architecture

This document maps out the high-performance, asynchronous Multimodal RAG architecture we built for the hackathon.

```mermaid
flowchart TD
    classDef frontend fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff
    classDef backend fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff
    classDef worker fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#fff
    classDef ai fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff
    classDef db fill:#64748b,stroke:#334155,stroke-width:2px,color:#fff

    User([User]) -->|Uploads File| UI

    subgraph Frontend
        UI[Streamlit UI]:::frontend
    end

    subgraph Backend Services
        API[FastAPI Router\n(Port 8000)]:::backend
        UI -->|HTTP POST /api/ingest| API
        API -.->|Immediate 200 OK| UI
        
        API -->|Queue| Semaphore{GPU\nSemaphore}
        Semaphore --> Worker[Background Tasks Worker]:::worker
    end

    subgraph Multimodal Parsers
        Worker -->|PDF/PPTX| Docling[Docling & PyMuPDF\n(Text & Layout)]:::ai
        Worker -->|Video URL| Whisper[faster-whisper & scenedetect\n(Audio & Frames)]:::ai
    end

    subgraph AI Processing Pipeline
        Docling --> VLM[Groq Vision API\n(llama-3.2-11b-vision)]:::ai
        Whisper --> VLM
        
        VLM -->|Generates Semantic\nVisual Descriptions| Embedder[HuggingFace Embeddings\n(BGE-M3 in Batch)]:::ai
    end

    subgraph Storage & Indexing
        Embedder --> DB[(PostgreSQL Database)]:::db
        DB -.->|Dense Search| pg[pgvector HNSW Index]:::db
        DB -.->|Sparse Search| ts[tsvector GIN Index]:::db
        
        Docling -.->|Saves Extracted\nImages| FS[(Local File System\n/assets/)]:::db
        Whisper -.->|Saves Extracted\nFrames| FS
    end

    subgraph Retrieval Pipeline
        UI -->|Query| Retriever[Hybrid Search Retriever]:::backend
        Retriever --> DB
        Retriever -->|Context + Provenance| ChatLLM[Groq Chat API\n(llama-3.1-70b-versatile)]:::ai
        ChatLLM -->|Grounded Answer| UI
    end
```
