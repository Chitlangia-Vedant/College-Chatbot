from fastapi import FastAPI, HTTPException, UploadFile, File
from app.llm import llm, rag_answer
from app.schemas import QuestionRequest
from app.rag import ingest_pdf, ingest_csv
from pathlib import Path
import shutil
from app.schemas import QuestionRequest, URLRequest
from app.rag import ingest_pdf, ingest_csv, ingest_website
from app.schemas import DeleteRequest
from app.rag import delete_by_source

app = FastAPI(title="AI Chatbot Backend")

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


@app.post("/upload-pdf")
def upload_pdf(file: UploadFile = File(...)):
    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    chunks = ingest_pdf(str(file_path))
    return {"message": "PDF ingested successfully", "chunks": chunks}

@app.post("/upload-csv")
def upload_csv(file: UploadFile = File(...)):
    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = ingest_csv(str(file_path))
    return {"message": "CSV ingested successfully", "chunks": result}


@app.post("/ask-pdf")
def ask_pdf(payload: QuestionRequest):
    return rag_answer(
        payload.question,
        payload.chat_history
    )
@app.post("/upload-url")
def upload_url(payload: URLRequest):
    try:
        result = ingest_website(payload.url)
        return {
            "message": "Website ingested successfully",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/delete-url")
def delete_url(payload: DeleteRequest):
    try:
        result = delete_by_source(payload.source)
        return {
            "message": "Deletion completed",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))