import time
import os
import shutil
import csv
import io
import requests
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Security, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv, find_dotenv

from app.logger import setup_logger
from app.llm import llm, rag_answer_stream, clear_llm_cache
from app.schemas import QuestionRequest, URLRequest, DeleteRequest
from app.rag import (
    ingest_pdf, 
    ingest_csv, 
    ingest_website, 
    delete_by_source, 
    get_all_sources, 
    ingest_website_semantic, 
    ingest_pdf_semantic
)

load_dotenv(find_dotenv())

# 2. Fetch the API key from the environment
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

# 3. Setup the Security Header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

def verify_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Access forbidden: Invalid API Key")

app = FastAPI(title="AI Chatbot Backend")

# --- Initialize Logger ---
logger = setup_logger("api_router")

# --- API Latency Middleware ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"Path={request.url.path} | Method={request.method} | "
        f"Status={response.status_code} | Latency={process_time:.4f}s"
    )
    return response

# Base directory → backend/
BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/")
def home():
    return {"status": "Backend is running"}


@app.post("/ask")
def ask_question(payload: QuestionRequest):
    try:
        response = llm.invoke(payload.question)
        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-pdf", dependencies=[Depends(verify_api_key)])
def upload_pdf(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    # 1. Validate extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
        
    # 2. SANITIZE: Strip out directory traversal characters
    safe_filename = os.path.basename(file.filename).replace("..", "").replace("/", "").replace("\\", "")
    file_path = UPLOAD_DIR / safe_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. Prevent Duplicates: Delete the old version
    delete_by_source(safe_filename)
    
    # 4. Process in background to avoid API timeouts
    background_tasks.add_task(ingest_pdf_semantic, str(file_path))
    
    # 5. Wipe cache to ensure users see the updated information
    clear_llm_cache()
    
    return {"message": f"{safe_filename} is being processed in the background."}


@app.post("/upload-csv", dependencies=[Depends(verify_api_key)])
def upload_csv(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    # 1. Validate extension
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    # 2. Strict Column Validation
    try:
        header_line = file.file.readline().decode('utf-8-sig') 
        file.file.seek(0)
        
        csv_reader = csv.reader(io.StringIO(header_line))
        headers = next(csv_reader, [])
        headers = [h.strip() for h in headers]
        
        if set(headers) != {"Question", "Answer"}:
            raise HTTPException(
                status_code=400, 
                detail=f"Upload failed. The CSV must contain ONLY 'Question' and 'Answer' columns. We found: {headers}"
            )
    except HTTPException:
        raise 
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read CSV file: {str(e)}")
        
    # 3. SANITIZE filename
    safe_filename = os.path.basename(file.filename).replace("..", "").replace("/", "").replace("\\", "")
    file_path = UPLOAD_DIR / safe_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    delete_by_source(safe_filename)

    background_tasks.add_task(ingest_csv, str(file_path))
    clear_llm_cache()

    return {"message": f"{safe_filename} is being processed in the background."}


@app.post("/ask-pdf")
def ask_pdf(payload: QuestionRequest):
    # Security: Add a strict character limit to prevent OOM/Prompt Bombing
    if len(payload.question) > 500:
        raise HTTPException(
            status_code=400, 
            detail="Question is too long. Please keep it under 500 characters."
        )
        
    # This sends an active stream back to the frontend
    return StreamingResponse(
        rag_answer_stream(payload.question, payload.chat_history), 
        media_type="text/event-stream"
    )


@app.post("/upload-url", dependencies=[Depends(verify_api_key)])
def upload_url(payload: URLRequest, background_tasks: BackgroundTasks = BackgroundTasks()):
    try:
        background_tasks.add_task(ingest_website, payload.url)
        clear_llm_cache()
        return {"message": f"Website {payload.url} is being processed in the background."}
    except Exception as e:
        err_msg = str(e)
        logger.error(f"Action=API_Upload_URL | Status=Failed | Reason={err_msg}")
        raise HTTPException(status_code=500, detail=err_msg)
    

@app.post("/delete-source", dependencies=[Depends(verify_api_key)])
def delete_source(payload: DeleteRequest):
    """
    Pass a filename (e.g., 'rules.pdf') or a URL to delete it from the chatbot's memory.
    """
    try:
        result = delete_by_source(payload.source)
        # Clear cache so the AI immediately "forgets" the deleted document
        clear_llm_cache()
        return {"message": "Deletion requested", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-url", dependencies=[Depends(verify_api_key)])
def update_url(payload: URLRequest, background_tasks: BackgroundTasks = BackgroundTasks()):
    # 1. Ping the URL to ensure it's alive and scrapeable FIRST to prevent data loss
    try:
        response = requests.get(payload.url, verify=False, timeout=10)
        response.raise_for_status() 
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Target URL is unreachable. Update aborted to protect existing data. Error: {str(e)}")

    # 2. Safe to proceed
    try:
        delete_by_source(payload.url)
        background_tasks.add_task(ingest_website, payload.url)
        clear_llm_cache()
        return {"message": f"Website {payload.url} is being updated in the background."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/list-sources")
def list_sources():
    """Returns a list of all unique documents and websites in the database."""
    try:
        sources = get_all_sources()
        return {"sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))