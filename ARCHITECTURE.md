# 🏛️ System Architecture

This document maps out the high-performance, GPU-accelerated Multimodal RAG architecture.

## 📥 1. Ingestion & Indexing Pipeline

```mermaid
flowchart TD
    classDef ui fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff
    classDef ai fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff
    classDef db fill:#64748b,stroke:#334155,stroke-width:2px,color:#fff

    UI[Streamlit Dashboard]:::ui -->|Upload Media| Parsers
    
    subgraph Multi-Modal Parsers
        Parsers[Docling / PyMuPDF / PPTX / Whisper + SceneDetect]
    end

    Parsers -->|Extract Text & Images| VLM[Gemini 3.7 Flash API]:::ai
    VLM -->|Generate Visual Descriptions| Meta[Metadata Extraction<br>Llama-3.1 via Groq]:::ai
    
    Meta -->|Extract Topics & Prerequisites| Embed[Embedding Service<br>CUDA BGE-M3]:::ai
    
    Embed -->|Dense Vectors & Text| DB[(PostgreSQL + pgvector)]:::db
    Parsers -.->|Save Raw Images| FS[(Local File System<br>/assets/)]:::db
```

## 🔍 2. Advanced Retrieval & Generation (Tutor Chat)

```mermaid
flowchart TD
    classDef ui fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff
    classDef ai fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff
    classDef db fill:#64748b,stroke:#334155,stroke-width:2px,color:#fff
    classDef logic fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff

    User((User)) -->|Follow-up Question| QueryRewrite
    
    subgraph Conversational Engine
        QueryRewrite[Query Contextualizer<br>Llama-3.1]:::logic
    end

    QueryRewrite -->|Standalone Query| Hybrid[Hybrid Search]:::logic
    
    subgraph Vector Database
        DB[(PostgreSQL)]:::db
        DB -.-> Dense[pgvector HNSW L2]
        DB -.-> Sparse[Postgres GIN BM25]
    end
    
    Hybrid --> Dense
    Hybrid --> Sparse
    
    Dense --> RRF[Reciprocal Rank Fusion]:::logic
    Sparse --> RRF
    
    RRF -->|Top 20| Reranker[Cross-Encoder Reranker<br>BAAI/bge-reranker-v2-m3]:::ai
    Reranker -->|Top 10| Gen[Answer Generation<br>Llama-3.1-70B]:::ai
    
    Gen -->|Grounded JSON| UI[Streamlit Frontend<br>Displays Text + Rendered Images]:::ui
```

## 🕸️ 3. True Knowledge Graph Construction

```mermaid
flowchart LR
    classDef db fill:#64748b,stroke:#334155,stroke-width:2px,color:#fff
    classDef logic fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff

    DB[(PostgreSQL JSON Columns)]:::db -->|Query Topics & Prerequisites| NX[NetworkX Graph Builder]:::logic
    NX -->|Topological Sort| Graph[Interactive PyVis Widget]:::logic
    Graph -->|Renders UI| Streamlit
```

## 🛠️ Technology Stack
*   **Frontend**: Streamlit, PyVis (HTML Components)
*   **Database**: PostgreSQL, pgvector (HNSW, GIN)
*   **Vector Embeddings**: `BAAI/bge-m3` (Local, CUDA Accelerated)
*   **Cross-Encoder**: `BAAI/bge-reranker-v2-m3` (Local, CUDA Accelerated)
*   **Vision Language Model (VLM)**: Gemini 3.7 Flash API (Cascading Fallbacks)
*   **Large Language Model (LLM)**: Llama-3.1-70B-Versatile via Groq LPU
*   **Video Processing**: yt-dlp, faster-whisper, PyAV, scenedetect
*   **Document Parsing**: Docling, PyMuPDF, python-pptx
