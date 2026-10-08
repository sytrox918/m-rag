from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
import shutil
import os
import asyncio
from services.ingestion_service import ingestion_service

app = FastAPI(title="Multimodal RAG API")

# 7. GPU Concurrency Control
# This ensures that no matter how many parallel requests hit the API, 
# only ONE heavy ingestion task uses the GPU/CPU heavily at a time.
gpu_semaphore = asyncio.Semaphore(1)

def run_ingest_pdf(file_path: str):
    try:
        metrics = ingestion_service.ingest_pdf(file_path)
        print(f"✅ Background PDF Ingestion Completed!\nMetrics: {metrics}")
    finally:
        if os.path.exists(file_path):
            os.unlink(file_path)

def run_ingest_pptx(file_path: str):
    try:
        metrics = ingestion_service.ingest_pptx(file_path)
        print(f"✅ Background PPTX Ingestion Completed!\nMetrics: {metrics}")
    finally:
        if os.path.exists(file_path):
            os.unlink(file_path)

def run_ingest_video(url: str):
    metrics = ingestion_service.ingest_video(url)
    print(f"✅ Background Video Ingestion Completed!\nMetrics: {metrics}")

async def background_ingest_pdf(file_path: str):
    async with gpu_semaphore:
        await asyncio.to_thread(run_ingest_pdf, file_path)

async def background_ingest_pptx(file_path: str):
    async with gpu_semaphore:
        await asyncio.to_thread(run_ingest_pptx, file_path)

async def background_ingest_video(url: str):
    async with gpu_semaphore:
        await asyncio.to_thread(run_ingest_video, url)

@app.post("/api/ingest/pdf")
async def ingest_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    tmp_path = f"temp_{file.filename}"
    with open(tmp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    background_tasks.add_task(background_ingest_pdf, tmp_path)
    return {"status": "processing", "message": "PDF ingestion queued."}

@app.post("/api/ingest/pptx")
async def ingest_pptx(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    tmp_path = f"temp_{file.filename}"
    with open(tmp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    background_tasks.add_task(background_ingest_pptx, tmp_path)
    return {"status": "processing", "message": "PPTX ingestion queued."}

class VideoRequest(BaseModel):
    url: str

@app.post("/api/ingest/video")
async def ingest_video(request: VideoRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(background_ingest_video, request.url)
    return {"status": "processing", "message": "Video ingestion queued."}

class AskRequest(BaseModel):
    question: str
    chat_history: list = []

@app.post("/api/ask")
async def ask_question(request: AskRequest):
    from services.answer_service import answer_service
    # Run the heavy LLM chain in a thread to prevent blocking the event loop
    result = await asyncio.to_thread(answer_service.answer_question, request.question, request.chat_history)
    return result

@app.get("/api/graph/{concept}")
async def get_graph(concept: str):
    from services.graph_service import graph_service
    path_data = await asyncio.to_thread(graph_service.get_learning_path, concept)
    html_data = await asyncio.to_thread(graph_service.generate_visual_graph, concept)
    return {
        "path_data": path_data,
        "html_data": html_data
    }
