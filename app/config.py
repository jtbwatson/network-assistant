import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Configuration ---
DOCS_DIR = "./network_docs"
DB_DIR = "./chroma_db"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
SEARCH_RESULTS = 5
OLLAMA_HOST = os.getenv("OLLAMA_HOST")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

# Ollama embedding settings
USE_OLLAMA_EMBEDDINGS = os.getenv("USE_OLLAMA_EMBEDDINGS", "true").lower() == "true"
OLLAMA_EMBEDDING_BATCH_SIZE = int(os.getenv("OLLAMA_EMBEDDING_BATCH_SIZE", "10"))

# Safely import ChromaDB
try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False