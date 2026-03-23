from fastapi import FastAPI, HTTPException, UploadFile, File
from app.llm import llm, rag_answer
from app.schemas import QuestionRequest
from app.rag import ingest_pdf
from pathlib import Path
import shutil

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


@app.post("/ask-pdf")
def ask_pdf(payload: QuestionRequest):
    return rag_answer(
        payload.question,
        payload.chat_history
    )