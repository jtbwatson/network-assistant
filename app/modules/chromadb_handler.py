import os
import logging
import config

logger = logging.getLogger(__name__)

def init_db():
    """Initialize ChromaDB"""
    if not config.CHROMA_AVAILABLE:
        logger.warning("ChromaDB not available. Vector search will be disabled.")
        return None, None

    os.makedirs(config.DB_DIR, exist_ok=True)
    try:
        import chromadb
        client = chromadb.PersistentClient(path=config.DB_DIR)
        
        # Try to get embedding function
        try:
            from chromadb.utils.embedding_functions import (
                SentenceTransformerEmbeddingFunction,
            )
            emb_fn = SentenceTransformerEmbeddingFunction(model_name="all-mpnet-base-v2")
        except Exception as e:
            logger.error(f"Error loading sentence transformer: {e}")
            emb_fn = None
            
        # Try to get existing collection or create new one
        try:
            collection = client.get_collection(name="network_docs")
            logger.info("Found existing collection: network_docs")
        except ValueError:
            collection = client.create_collection(
                name="network_docs", embedding_function=emb_fn
            )
            logger.info("Created new collection: network_docs")
            
        return client, collection
    
    except Exception as e:
        logger.error(f"Error initializing ChromaDB: {e}")
        return None, None