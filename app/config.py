import os

# --- Configuration ---
DOCS_DIR = "./network_docs"
DB_DIR = "./chroma_db"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
SEARCH_RESULTS = 5
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Check if ChromaDB is available
try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False