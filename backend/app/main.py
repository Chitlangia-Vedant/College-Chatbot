import time
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Security, Request
from app.logger import setup_logger
from fastapi.responses import StreamingResponse
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv
from app.llm import llm, rag_answer_stream
from app.schemas import QuestionRequest, URLRequest, DeleteRequest
from app.rag import ingest_pdf, ingest_csv, ingest_website, delete_by_source, get_all_sources
from pathlib import Path
import shutil
import os
import csv
import io

# 1. Load the variables from the .env file
load_dotenv()

# 2. Fetch the API key from the environment
# The second argument "fallback_secret_here" is a backup just in case the .env file is missing
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

# 3. Setup the Security Header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


def verify_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Access forbidden: Invalid API Key")

app = FastAPI(title="AI Chatbot Backend")

# --- Initialize Logger ---
logger = setup_logger("api_router")

# --- NEW: API Latency Middleware ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Process the request
    response = await call_next(request)
    
    # Calculate how long it took
    process_time = time.time() - start_time
    
    # Log the structured data
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
def upload_pdf(file: UploadFile = File(...)):
    # 1. Validate extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
        
    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Prevent Duplicates: Delete the old version of this PDF from the database first
    delete_by_source(file.filename)
    
    chunks = ingest_pdf(str(file_path))
    return {"message": f"{file.filename} ingested successfully", "chunks": chunks}

@app.post("/upload-csv", dependencies=[Depends(verify_api_key)])
def upload_csv(file: UploadFile = File(...)):
    # 1. Validate extension
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    # --- NEW: Strict Column Validation ---
    try:
        # Read the first line of the file (the headers) without saving it
        header_line = file.file.readline().decode('utf-8-sig') # utf-8-sig handles Excel's hidden BOM characters
        file.file.seek(0) # IMPORTANT: Reset the cursor back to 0 so we can save the file later!
        
        # Parse the headers
        csv_reader = csv.reader(io.StringIO(header_line))
        headers = next(csv_reader, [])
        
        # Clean up the headers (removes accidental spaces, e.g., " Question " -> "Question")
        headers = [h.strip() for h in headers]
        
        # Verify that the columns are EXACTLY "Question" and "Answer" (order doesn't matter)
        if set(headers) != {"Question", "Answer"}:
            raise HTTPException(
                status_code=400, 
                detail=f"Upload failed. The CSV must contain ONLY 'Question' and 'Answer' columns. We found: {headers}"
            )
    except HTTPException:
        raise # Passes our exact error message to the user
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read CSV file: {str(e)}")
    # -------------------------------------
        
    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Prevent Duplicates: Delete the old version of this CSV from the database first
    delete_by_source(file.filename)

    result = ingest_csv(str(file_path))
    return {"message": f"{file.filename} ingested successfully", "chunks": result}


@app.post("/ask-pdf")
def ask_pdf(payload: QuestionRequest):
    # This sends an active stream back to the frontend
    return StreamingResponse(
        rag_answer_stream(payload.question, payload.chat_history), 
        media_type="text/event-stream"
    )

@app.post("/upload-url", dependencies=[Depends(verify_api_key)])
def upload_url(payload: URLRequest):
    try:
        result = ingest_website(payload.url)
        return {
            "message": "Website ingested successfully",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Universal Delete Endpoint (Replaces the old /delete-url)
@app.post("/delete-source", dependencies=[Depends(verify_api_key)])
def delete_source(payload: DeleteRequest):
    """
    Pass a filename (e.g., 'rules.pdf') or a URL to delete it from the chatbot's memory.
    """
    try:
        result = delete_by_source(payload.source)
        return {"message": "Deletion requested", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update-url", dependencies=[Depends(verify_api_key)])
def update_url(payload: URLRequest):
    try:
        # 1. Delete the old version
        delete_by_source(payload.url)
        # 2. Scrape and save the fresh version
        result = ingest_website(payload.url)
        return {
            "message": "Website updated successfully",
            "data": result
        }
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