import os
import logging
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# --- Configuration ---
DOCS_DIR = os.getenv("DOCS_DIR", "./network_docs")
DB_DIR = os.getenv("DB_DIR", "./chroma_db")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
SEARCH_RESULTS = int(os.getenv("SEARCH_RESULTS", "5"))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")

# Validate required settings
if not OLLAMA_HOST:
    logger.warning("OLLAMA_HOST is not set! Using default: http://localhost:11434")
    OLLAMA_HOST = "http://localhost:11434"

if not OLLAMA_MODEL:
    logger.warning("OLLAMA_MODEL is not set! Using default: llama2")
    OLLAMA_MODEL = "llama2"

# Ollama embedding settings
USE_OLLAMA_EMBEDDINGS = os.getenv("USE_OLLAMA_EMBEDDINGS", "true").lower() == "true"
OLLAMA_EMBEDDING_BATCH_SIZE = int(os.getenv("OLLAMA_EMBEDDING_BATCH_SIZE", "10"))
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

# Application settings
PORT = int(os.getenv("PORT", "5000"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

# Safely import ChromaDB
try:
    import chromadb
    CHROMA_AVAILABLE = True
    logger.info("ChromaDB successfully imported")
except ImportError:
    logger.warning("ChromaDB import failed - vector search will be disabled")
    CHROMA_AVAILABLE = False

# Print configuration summary
def log_config():
    """Log the current configuration settings"""
    logger.info("=== Configuration ===")
    logger.info(f"DOCS_DIR: {DOCS_DIR}")
    logger.info(f"DB_DIR: {DB_DIR}")
    logger.info(f"OLLAMA_HOST: {OLLAMA_HOST}")
    logger.info(f"OLLAMA_MODEL: {OLLAMA_MODEL}")
    logger.info(f"OLLAMA_EMBEDDING_MODEL: {OLLAMA_EMBEDDING_MODEL}")
    logger.info(f"USE_OLLAMA_EMBEDDINGS: {USE_OLLAMA_EMBEDDINGS}")
    logger.info(f"CHROMA_AVAILABLE: {CHROMA_AVAILABLE}")
    logger.info(f"PORT: {PORT}")
    logger.info(f"DEBUG_MODE: {DEBUG_MODE}")
    logger.info("====================")