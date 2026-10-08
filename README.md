# 🧠 Multimodal Educational RAG System

A state-of-the-art, GPU-accelerated Multimodal RAG system built specifically for educational content. This system can digest Videos, PDFs, and PowerPoints, visually understand diagrams, mathematically graph prerequisites, and act as a conversational AI tutor with flawless source grounding.

## ✨ Key Features

*   **Multimodal Ingestion**: Natively processes YouTube Videos (audio + scene changes), PDFs, and PPTX files.
*   **Vision Language Processing**: Extracts frames, charts, and diagrams and passes them through **Gemini 3.7 Flash** to embed their visual context.
*   **True Knowledge Graph**: Dynamically extracts topics and prerequisites using Llama 3.1, building a topological curriculum graph via **NetworkX** that can be visualized interactively in the UI.
*   **Advanced Hybrid Retrieval**: Combines Dense (BGE-M3) and Sparse (Postgres GIN BM25) search using **Reciprocal Rank Fusion (RRF)**, followed by a **Cross-Encoder Reranker** (`BAAI/bge-reranker-v2-m3`) for ultimate precision.
*   **Conversational Tutor Chat**: Multi-session memory architecture that contextually rewrites follow-up questions while maintaining absolute source grounding.
*   **GPU Acceleration**: Whisper and BGE-M3 embeddings automatically utilize CUDA for extreme inference speed.

## 🚀 Quickstart

### 1. Installation
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1 # Windows
# source .venv/bin/activate # Linux/Mac

pip install -r requirements.txt
pip install pyvis networkx # For Knowledge Graph
```

### 2. Configuration
Copy `.env.example` to `.env` and provide your credentials.
You will need:
*   A **Supabase / Postgres DB** (with pgvector extension)
*   A **Groq API Key** (for Llama-3.1 Answer Generation)
*   A **Gemini API Key** (for Vision Processing)

### 3. Initialize Database
Create the necessary pgvector tables:
```bash
python scripts/init_db.py
```

### 4. Run the Dashboard
```bash
streamlit run app.py
```

## 🏗️ Architecture

Check out the full technical architecture flowcharts and design decisions in [ARCHITECTURE.md](ARCHITECTURE.md).
