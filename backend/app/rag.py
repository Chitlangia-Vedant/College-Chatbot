from langchain_community.document_loaders import PyPDFLoader, CSVLoader, WebBaseLoader, UnstructuredPDFLoader
from langchain_chroma import Chroma
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.document_loaders import SeleniumURLLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import HTMLHeaderTextSplitter, RecursiveCharacterTextSplitter
from pathlib import Path
from datetime import datetime
from app.logger import setup_logger
import os
import hashlib
import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document


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

#DO NOT DELETE
def ingest_pdf(file_path: str):
    filename = os.path.basename(file_path)
    logger.info(f"Action=Ingest_PDF | Status=Started | Source={filename}")
    
    loader = UnstructuredPDFLoader(
        file_path,
        mode="elements",
        strategy="hi_res",
        chunking_strategy="by_title",
        max_characters=1500
    )
    
    chunks = loader.load()
    current_date = datetime.now().strftime("%Y-%m-%d")
    ids = []
    
    for chunk in chunks:
        chunk.metadata["source"] = filename 
        chunk.metadata["date_added"] = current_date
        chunk.metadata["type"] = "pdf_structural"
        unique_string = f"{filename}_{chunk.page_content}"
        ids.append(hashlib.md5(unique_string.encode('utf-8')).hexdigest())

    vectordb.add_documents(chunks, ids=ids)
    pages_count = len({chunk.metadata.get("page_number", chunk.metadata.get("page", 1)) for chunk in chunks})

    logger.info(f"Action=Ingest_PDF | Status=Success | Source={filename} | Chunks={len(chunks)}")
    return {"pages": pages_count, "chunks": len(chunks)}

def ingest_pdf_semantic(file_path: str):
    """Chunks PDFs by meaning/topic using embeddings"""
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    semantic_splitter = SemanticChunker(embeddings)
    chunks = semantic_splitter.split_documents(documents)

    filename = os.path.basename(file_path)
    current_date = datetime.now().strftime("%Y-%m-%d")
    ids = []
    
    for chunk in chunks:
        chunk.metadata["source"] = filename 
        chunk.metadata["date_added"] = current_date
        chunk.metadata["type"] = "pdf_semantic"
        
        unique_string = f"{filename}_{chunk.page_content}"
        ids.append(hashlib.md5(unique_string.encode('utf-8')).hexdigest())

    vectordb.add_documents(chunks, ids=ids)

    # Restored Old Return (PyPDFLoader uses 'page')
    return {
        "pages": len({doc.metadata.get("page") for doc in documents}), 
        "chunks": len(chunks)
    }

def ingest_csv(file_path: str):
    filename = os.path.basename(file_path)
    logger.info(f"Action=Ingest_CSV | Status=Started | Source={filename}")
    
    loader = CSVLoader(file_path=file_path, encoding="utf-8", source_column="Question")
    documents = loader.load()

    current_date = datetime.now().strftime("%Y-%m-%d")
    ids = []
    for doc in documents:
        doc.metadata["source"] = filename 
        doc.metadata["date_added"] = current_date
        doc.metadata["type"] = "csv"
        unique_string = f"{filename}_{doc.page_content}"
        ids.append(hashlib.md5(unique_string.encode('utf-8')).hexdigest())

    vectordb.add_documents(documents, ids=ids)
    logger.info(f"Action=Ingest_CSV | Status=Success | Source={filename} | Rows={len(documents)}")
    return {"rows": len(documents)}

def ingest_website(url: str):
    """
    Scrapes dynamic content by rendering JavaScript with Selenium and 
    splits it into granular chunks for the vector database.
    """
    logger.info(f"Action=Scrape_URL | Status=Started | Method=Selenium | Source={url}")
    
    try:
        # 1. Load dynamic content using Selenium
        # This requires 'selenium' and 'unstructured' to be installed
        loader = SeleniumURLLoader(urls=[url])
        documents = loader.load()

        if not documents:
            logger.warning(f"Action=Scrape_URL | Status=Warning | Source={url} | Detail=No content captured")
            return {"source": url, "chunks_added": 0}

        # 2. Split the rendered text into chunks
        # RecursiveCharacterTextSplitter ensures we get multiple chunks even from flat pages
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=80,
            separators=["\n\n", "\n", ".", " "]
        )
        chunks = text_splitter.split_documents(documents)
        
        # 3. Process and store in ChromaDB
        current_date = datetime.now().strftime("%Y-%m-%d")
        ids = []
        
        for chunk in chunks:
            # Tagging metadata correctly so admin.py can find it
            chunk.metadata["source"] = url
            chunk.metadata["date_added"] = current_date
            chunk.metadata["type"] = "website_dynamic"
            
            # Create a unique ID based on the content to prevent duplicates
            unique_string = f"{url}_{chunk.page_content}"
            ids.append(hashlib.md5(unique_string.encode()).hexdigest())

        # Add the fresh chunks to the vector database
        vectordb.add_documents(chunks, ids=ids)
        
        logger.info(f"Action=Scrape_URL | Status=Success | Source={url} | Chunks={len(chunks)}")
        return {"source": url, "chunks_added": len(chunks)}

    except Exception as e:
        logger.error(f"Action=Scrape_URL | Status=Failed | Source={url} | Error={str(e)}")
        # Re-raise so the API returns a 500 error to the admin panel
        raise Exception(f"Dynamic Scraper Error: {str(e)}")

# DO NOT DELETE    
def ingest_website_header(url: str):
    """Scrapes a webpage with advanced browser-mimicking and logs chunking results."""
    
    # 1. Added Start Log
    logger.info(f"Action=Scrape_URL | Status=Started | Source={url}")

    try:
        loader = WebBaseLoader(url)
        loader.requests_kwargs = {'verify': False, 'timeout': 20}
        docs = loader.load()

        response = requests.get(url, verify=False, timeout=20)

        headers_to_split_on = [
            ("h1", "Header 1"),
            ("h2", "Header 2"),
            ("h3", "Header 3"),
        ]
        html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        chunks = html_splitter.split_text(response.text)
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        ids = []
        for chunk in chunks:
            chunk.metadata["source"] = url
            chunk.metadata["date_added"] = current_date
            chunk.metadata["type"] = "website"
            unique_string = f"{url}_{chunk.page_content}"
            ids.append(hashlib.md5(unique_string.encode()).hexdigest())

        vectordb.add_documents(chunks, ids=ids)
        
        # 2. Added Success Log to match semantic version
        logger.info(f"Action=Scrape_URL | Status=Success | Source={url} | Chunks={len(chunks)}")
        
        return {"source": url, "chunks_added": len(chunks)}

    except requests.exceptions.RequestException as e:
        # 3. Added Error Log for consistent failure tracking
        logger.error(f"Action=Scrape_URL | Status=Failed | Source={url} | Error={str(e)}")
        raise Exception(f"External Site Error: {str(e)}")

#DO NOT DELETE    
def ingest_website_semantic(url: str):
    logger.info(f"Action=Scrape_URL | Status=Started | URL={url}")
   
    try:
 
        loader = WebBaseLoader(url)
        loader.requests_kwargs = {'verify': False, 'timeout': 20}
        documents = loader.load()

        # SemanticChunker processes the text pulled by WebBaseLoader
        semantic_splitter = SemanticChunker(
            embeddings, 
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=80 
        )
        
        # We pass the loaded documents directly to the semantic splitter
        chunks = semantic_splitter.split_documents(documents)

        current_date = datetime.now().strftime("%Y-%m-%d")
        ids = []
        for chunk in chunks:
            chunk.metadata["source"] = url
            chunk.metadata["date_added"] = current_date
            chunk.metadata["type"] = "website_semantic"
            unique_string = f"{url}_{chunk.page_content}"
            ids.append(hashlib.md5(unique_string.encode()).hexdigest())

        vectordb.add_documents(chunks, ids=ids)
        logger.info(f"Action=Scrape_URL | Status=Success | Source={url} | Chunks={len(chunks)}")
        return {"source": url, "chunks_added": len(chunks)}

    except Exception as e:
        logger.error(f"Action=Scrape_URL | Status=Failed | Source={url} | Error={str(e)}")
        raise Exception(f"Semantic Web Loader Error: {str(e)}")   

def get_retriever_with_sources():
    vectordb = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(VECTOR_DIR),
        embedding_function=embeddings
    )
    return vectordb.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 6,          # Number of diverse chunks to return to the LLM
            "fetch_k": 20,   # Initial pool of chunks to fetch before filtering
            "lambda_mult": 0.5 # Balances relevance (0) vs diversity (1)
        })

def delete_by_source(source: str):
    try:
        logger.info(f"Action=Delete_Source | Status=Attempting | Source={source}")
        matching_docs = vectordb.get(where={"source": source})
        ids_to_delete = matching_docs.get("ids", [])

        if not ids_to_delete:
            logger.warning(f"Action=Delete_Source | Status=Not_Found | Source={source}")
            return {"deleted": 0, "message": f"Source '{source}' not found."}

        vectordb.delete(ids=ids_to_delete)
        logger.info(f"Action=Delete_Source | Status=Success | Source={source} | Chunks_Removed={len(ids_to_delete)}")
        return {"deleted": len(ids_to_delete), "message": f"Successfully deleted {source}"}
    except Exception as e:
        logger.error(f"Action=Delete_Source | Status=Failed | Source={source} | Error={str(e)}")
        return {"deleted": 0, "error": str(e)}
        
def get_all_sources():
    """Retrieves a list of all unique sources currently in the database."""
    try:
        # Fetch only the metadatas to save memory
        data = vectordb.get(include=['metadatas'])
        unique_sources = set()
        
        metadatas = data.get("metadatas", [])
        if not metadatas:
            return []

        for metadata in metadatas:
            # Ensure metadata exists and contains a non-empty source
            if metadata and "source" in metadata and metadata["source"]:
                unique_sources.add(metadata["source"])
                
        return sorted(list(unique_sources))
    except Exception as e:
        logger.error(f"Action=Get_Sources | Status=Error | Detail={str(e)}")
        return []