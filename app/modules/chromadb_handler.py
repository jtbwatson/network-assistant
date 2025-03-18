import os
import logging
import config
import shutil
import time
import json

# Disable ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"

logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 2

class ChromaDBStatus:
    """Class to track ChromaDB status and performance metrics"""
    def __init__(self):
        self.initialized = False
        self.collection_name = "network_docs"
        self.document_count = 0
        self.last_query_time = 0
        self.last_error = None
        self.initialization_time = None
        
    def update_document_count(self, collection):
        """Update the document count from the collection"""
        try:
            all_docs = collection.get()
            if all_docs and "ids" in all_docs:
                self.document_count = len(all_docs["ids"])
        except Exception as e:
            logger.error(f"🔴 Error updating document count: {e}")
    
    def record_query_time(self, elapsed_time):
        """Record the time taken for a query"""
        self.last_query_time = elapsed_time
        
    def get_status_dict(self):
        """Get the status as a dictionary"""
        return {
            "initialized": self.initialized,
            "collection_name": self.collection_name,
            "document_count": self.document_count,
            "last_query_time_ms": round(self.last_query_time * 1000) if self.last_query_time else None,
            "initialization_time": self.initialization_time
        }

# Global status tracker
db_status = ChromaDBStatus()


def get_embedding_function():
    """Get the appropriate embedding function based on configuration"""
    try:
        # Import the custom Ollama embedding function
        from modules.ollama_embedding import OllamaEmbeddingFunction
        
        # Check if we should use Ollama for embeddings
        use_ollama_embeddings = config.USE_OLLAMA_EMBEDDINGS
        
        if use_ollama_embeddings:
            try:
                # Create the Ollama embedding function using the embedding-specific model
                emb_fn = OllamaEmbeddingFunction(
                    ollama_base_url=config.OLLAMA_HOST,
                    model_name=config.OLLAMA_EMBEDDING_MODEL  # Use dedicated embedding model
                )
                logger.info(f"🟢 Using Ollama for embeddings: {config.OLLAMA_HOST} with model {config.OLLAMA_EMBEDDING_MODEL}")
                return emb_fn
            except Exception as e:
                logger.error(f"🔴 Error setting up Ollama embedding function: {e}")
                logger.warning("🟡 Falling back to local embedding function")
                # Fall back to local embeddings
                use_ollama_embeddings = False
        
        # Use local sentence-transformer if not using Ollama
        if not use_ollama_embeddings:
            # Get the default embedding function
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            emb_fn = SentenceTransformerEmbeddingFunction(model_name="all-mpnet-base-v2")
            logger.info("🟡 Using local SentenceTransformer for embeddings")
            return emb_fn
            
    except Exception as e:
        logger.error(f"🔴 Error getting embedding function: {e}")
        logger.warning("🟡 No embedding function available, using default")
        return None


def init_db():
    """Initialize ChromaDB"""
    if not config.CHROMA_AVAILABLE:
        logger.warning("🔴 ChromaDB not available. Vector search will be disabled.")
        return None, None

    start_time = time.time()
    os.makedirs(config.DB_DIR, exist_ok=True)
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Configure ChromaDB settings
        chroma_settings = Settings(
            anonymized_telemetry=False,
            persist_directory=config.DB_DIR,
            is_persistent=True
        )
        
        # Add a retry mechanism to handle tenant initialization issues
        for retry_count in range(MAX_RETRIES):
            try:
                logger.info(f"🟡 Initializing ChromaDB (attempt {retry_count + 1}/{MAX_RETRIES})")
                
                # Create persistent client
                client = chromadb.PersistentClient(
                    path=config.DB_DIR,
                    settings=chroma_settings
                )
                
                # Get the embedding function
                emb_fn = get_embedding_function()
                    
                # Try to get existing collection or create new one
                try:
                    collection = client.get_collection(
                        name=db_status.collection_name,
                        embedding_function=emb_fn
                    )
                    logger.info(f"🟢 Found existing collection: {db_status.collection_name}")
                except ValueError:
                    collection = client.create_collection(
                        name=db_status.collection_name, 
                        embedding_function=emb_fn
                    )
                    logger.info(f"🟢 Created new collection: {db_status.collection_name}")
                
                # Update status
                db_status.initialized = True
                db_status.initialization_time = time.time() - start_time
                db_status.update_document_count(collection)
                
                logger.info(f"🟢 ChromaDB initialized successfully in {db_status.initialization_time:.2f}s with {db_status.document_count} documents")
                return client, collection
                
            except Exception as e:
                logger.warning(f"🟡 Attempt {retry_count + 1} failed: {e}")
                db_status.last_error = str(e)
                
                if retry_count < MAX_RETRIES - 1:
                    logger.info(f"🟡 Waiting {RETRY_DELAY}s before retry")
                    time.sleep(RETRY_DELAY)
        
        # If we get here, all retries failed
        logger.error(f"🔴 Error initializing ChromaDB after {MAX_RETRIES} attempts: {db_status.last_error}")
        return None, None
    
    except Exception as e:
        logger.error(f"🔴 Error initializing ChromaDB: {e}")
        db_status.last_error = str(e)
        return None, None


def get_database_stats():
    """
    Get statistics about the ChromaDB database.
    
    Returns:
        dict: Database statistics
    """
    stats = {
        "status": db_status.get_status_dict(),
        "path": config.DB_DIR,
        "embedding_source": "ollama" if config.USE_OLLAMA_EMBEDDINGS else "local",
        "embedding_model": config.OLLAMA_EMBEDDING_MODEL if config.USE_OLLAMA_EMBEDDINGS else "all-mpnet-base-v2"
    }
    
    # Add disk usage information if database exists
    if os.path.exists(config.DB_DIR):
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(config.DB_DIR):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            
            from modules.utils import format_file_size
            stats["disk_usage"] = format_file_size(total_size)
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            stats["disk_usage"] = "Unknown"
    else:
        stats["disk_usage"] = "0 B"
    
    return stats


def query_with_timing(collection, query_texts, n_results=5, **kwargs):
    """
    Query the collection with timing information.
    
    Args:
        collection: ChromaDB collection
        query_texts: Text to query
        n_results: Number of results to return
        **kwargs: Additional arguments to pass to collection.query
        
    Returns:
        dict: Query results
    """
    if not db_status.initialized or collection is None:
        return None
        
    start_time = time.time()
    try:
        results = collection.query(
            query_texts=query_texts,
            n_results=n_results,
            **kwargs
        )
        elapsed = time.time() - start_time
        db_status.record_query_time(elapsed)
        logger.debug(f"Query completed in {elapsed:.4f}s")
        return results
    except Exception as e:
        logger.error(f"Error querying collection: {e}")
        elapsed = time.time() - start_time
        db_status.record_query_time(elapsed)
        db_status.last_error = str(e)
        return None