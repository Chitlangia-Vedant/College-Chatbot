import hashlib
import time
import json
import os
import requests
import logging # <-- NEW IMPORT
from langchain_community.document_loaders import WebBaseLoader

# --- NEW: Configure the Logger ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("chatbot_updater.log"), # Saves to a file
        logging.StreamHandler() # Also prints to your terminal
    ]
)

TRACKED_URLS = [
    "https://www.sgsits.ac.in/admissions",
    "https://www.sgsits.ac.in/fee-structure",
    "https://www.sgsits.ac.in/contact-us"
]

HASH_FILE = "website_hashes.json"
API_UPDATE_URL = "http://127.0.0.1:8000/update-url"

def load_hashes():
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            return json.load(f)
    return {}

def save_hashes(hashes):
    with open(HASH_FILE, "w") as f:
        json.dump(hashes, f, indent=4)

def get_page_hash(url):
    try:
        loader = WebBaseLoader(url)
        docs = loader.load()
        page_text = "\n".join([doc.page_content for doc in docs])
        return hashlib.md5(page_text.encode('utf-8')).hexdigest()
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}") # <-- CHANGED FROM PRINT
        return None

def trigger_backend_update(url):
    logging.info(f"Triggering database update for {url}...") # <-- CHANGED FROM PRINT
    try:
        response = requests.post(API_UPDATE_URL, json={"url": url})
        if response.status_code == 200:
            logging.info(f"Database updated successfully for {url}!") # <-- CHANGED FROM PRINT
        else:
            logging.warning(f"Backend returned an error: {response.text}") # <-- CHANGED FROM PRINT
    except Exception as e:
        logging.error(f"Could not connect to backend: {e}") # <-- CHANGED FROM PRINT

def monitor_websites():
    logging.info("Website Monitor Started...") # <-- CHANGED FROM PRINT
    hashes = load_hashes()

    while True:
        logging.info("Checking for updates...") # <-- CHANGED FROM PRINT
        for url in TRACKED_URLS:
            current_hash = get_page_hash(url)
            
            if current_hash is None:
                continue

            if url not in hashes or hashes[url] != current_hash:
                logging.warning(f"CHANGE DETECTED: {url}") # <-- CHANGED FROM PRINT
                trigger_backend_update(url)
                hashes[url] = current_hash
                save_hashes(hashes)
            else:
                logging.info(f"No changes: {url}") # <-- CHANGED FROM PRINT

        logging.info("Sleeping for 24 hours...") # <-- CHANGED FROM PRINT
        time.sleep(86400)

if __name__ == "__main__":
    monitor_websites()