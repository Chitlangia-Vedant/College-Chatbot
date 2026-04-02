from langchain_community.document_loaders import PyPDFLoader,CSVLoader, WebBaseLoader
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from pathlib import Path
from datetime import datetime
from app.logger import setup_logger
import logging
import os
import hashlib

logger = setup_logger("vector_database")

# Base directory → backend/
BASE_DIR = Path(__file__).resolve().parents[1]

UPLOAD_DIR = BASE_DIR / "data" / "uploads"
VECTOR_DIR = BASE_DIR / "vectorstore"
COLLECTION_NAME = "pdf_documents"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_DIR.mkdir(parents=True, exist_ok=True)

embeddings = OllamaEmbeddings(model="nomic-embed-text")

vectordb = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=str(VECTOR_DIR),
    embedding_function=embeddings
)


def ingest_pdf(file_path: str):
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=250
    )
    chunks = splitter.split_documents(documents)

    # Standardize source and generate unique IDs
    filename = os.path.basename(file_path)
    current_date = datetime.now().strftime("%Y-%m-%d") # Gets today's date like "2024-10-25"
    ids = []
    for chunk in chunks:
        chunk.metadata["source"] = filename 
        chunk.metadata["date_added"] = current_date
        chunk.metadata["type"] = "pdf"
        
        unique_string = f"{filename}_{chunk.page_content}"
        ids.append(hashlib.md5(unique_string.encode('utf-8')).hexdigest())

    vectordb.add_documents(chunks, ids=ids)

    return {
        "pages": len({doc.metadata.get("page") for doc in documents}), 
        "chunks": len(chunks)
    }

def ingest_csv(file_path: str):
    loader = CSVLoader(
        file_path=file_path,
        encoding="utf-8",
        source_column="Question" 
    )
    documents = loader.load()

    # Standardize source and generate unique IDs
    filename = os.path.basename(file_path)
    current_date = datetime.now().strftime("%Y-%m-%d")
    ids = []
    for doc in documents:
        doc.metadata["source"] = filename 
        doc.metadata["date_added"] = current_date
        doc.metadata["type"] = "csv"
        
        unique_string = f"{filename}_{doc.page_content}"
        ids.append(hashlib.md5(unique_string.encode('utf-8')).hexdigest())

    vectordb.add_documents(documents, ids=ids)

    return {"rows": len(documents)}


def get_retriever_with_sources():
    vectordb = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(VECTOR_DIR),
        embedding_function=embeddings
    )
    return vectordb.as_retriever(search_kwargs={"k": 4})

def ingest_website(url: str):
    """Scrapes a webpage and adds it to the Chroma vector store."""

    # 1. Load webpage
    loader = WebBaseLoader(url)
    documents = loader.load()

    # 2. Split text (same logic as PDF → consistency)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=250
    )
    chunks = splitter.split_documents(documents)

    current_date = datetime.now().strftime("%Y-%m-%d")

    # 3. Generate unique IDs (prevents duplicates)
    ids = []
    for chunk in chunks:
        chunk.metadata = {
            "source": url,
            "date_added": current_date,
            "type": "website"
        }

        unique_string = f"{url}_{chunk.page_content}"
        chunk_id = hashlib.md5(unique_string.encode()).hexdigest()
        ids.append(chunk_id)

    vectordb.add_documents(chunks, ids=ids)

    return {
        "source": url,
        "chunks_added": len(chunks)
    }

def delete_by_source(source: str):
    """Deletes any chunks matching the exact source (filename or URL)"""

    try:
        # Optimized deletion: Use Chroma's built-in metadata filter
        matching_docs = vectordb.get(where={"source": source})
        ids_to_delete = matching_docs.get("ids", [])

        if not ids_to_delete:
            return {"deleted": 0, "message": f"Source '{source}' not found in database."}

        vectordb.delete(ids=ids_to_delete)
        return {"deleted": len(ids_to_delete), "message": f"Successfully deleted {source}"}
        
    except Exception as e:
        return {"deleted": 0, "error": str(e)}
    
def get_all_sources():
    """Retrieves a list of all unique sources currently in the database."""
   
    try:
        data = vectordb.get()
        unique_sources = set()
        
        # Look through all metadata and grab the "source" tags
        for metadata in data.get("metadatas", []):
            if metadata and "source" in metadata:
                unique_sources.add(metadata["source"])
                
        return sorted(list(unique_sources))
    except Exception as e:
        logger.error(f"Error fetching sources: {e}")
        return []