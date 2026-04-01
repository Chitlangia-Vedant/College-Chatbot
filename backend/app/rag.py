from langchain_community.document_loaders import PyPDFLoader,CSVLoader
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from pathlib import Path
import hashlib
from langchain_community.document_loaders import WebBaseLoader

# Base directory → backend/
BASE_DIR = Path(__file__).resolve().parents[1]

UPLOAD_DIR = BASE_DIR / "data" / "uploads"
VECTOR_DIR = BASE_DIR / "vectorstore"
COLLECTION_NAME = "pdf_documents"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_DIR.mkdir(parents=True, exist_ok=True)

embeddings = OllamaEmbeddings(model="nomic-embed-text")


def ingest_pdf(file_path: str):
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=250
    )
    chunks = splitter.split_documents(documents)

    vectordb = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(VECTOR_DIR),
        embedding_function=embeddings
    )

    vectordb.add_documents(chunks)

    return {
        "pages": len({doc.metadata.get("page") for doc in documents}),
        "chunks": len(chunks)
    }

def ingest_csv(file_path: str):
    loader = CSVLoader(
        file_path=file_path,
        encoding="utf-8",
        source_column="Question" # citations to show the exact question instead of the filename
    )
    documents = loader.load()

    vectordb = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(VECTOR_DIR),
        embedding_function=embeddings
    )

    vectordb.add_documents(documents)

    return {
        "rows": len(documents),
    }


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

    # 3. Generate unique IDs (prevents duplicates)
    ids = []
    for chunk in chunks:
        chunk.metadata = {"source": url}

        unique_string = f"{url}_{chunk.page_content}"
        chunk_id = hashlib.md5(unique_string.encode()).hexdigest()
        ids.append(chunk_id)

    # 4. Store in SAME Chroma DB
    vectordb = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(VECTOR_DIR),
        embedding_function=embeddings
    )

    vectordb.add_documents(chunks, ids=ids)

    return {
        "source": url,
        "chunks_added": len(chunks)
    }
def delete_by_source(source: str):
    vectordb = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(VECTOR_DIR),
        embedding_function=embeddings
    )

    # Get all stored docs
    data = vectordb.get()

    ids_to_delete = []

    for i, metadata in enumerate(data["metadatas"]):
        if metadata.get("source") == source:
            ids_to_delete.append(data["ids"][i])

    if not ids_to_delete:
        return {"deleted": 0}

    vectordb.delete(ids=ids_to_delete)

    return {"deleted": len(ids_to_delete)}