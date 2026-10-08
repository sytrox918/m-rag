# Multimodal RAG System

A simple, fast, and reliable multimodal RAG system for educational content.

## Setup

1. Create a virtual environment and activate it:
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\Activate.ps1
# On Linux/Mac:
source .venv/bin/activate
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
Copy `.env.example` to `.env` and fill in your PostgreSQL and OpenAI/LLM API credentials.
```bash
cp .env.example .env
```

4. Initialize the database:
Make sure you have PostgreSQL running with the `pgvector` extension available.
```bash
python scripts/init_db.py
```

5. Run the application:
```bash
streamlit run app.py
```

## Features
- Ingest PDF documents (using Docling)
- Ingest PPTX presentations (using python-pptx)
- Ingest YouTube videos (using yt-dlp and faster-whisper)
- Hybrid Retrieval (pgvector L2 distance + PostgreSQL Full Text Search via Reciprocal Rank Fusion)
- Source Grounding validation
- Citation matching and extraction directly linked to evidence chunks
