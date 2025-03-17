import os
import logging
import config
import shutil
import time

# Disable ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"

logger = logging.getLogger(__name__)

def get_embedding_function():
    """Get the appropriate embedding function based on configuration"""
    try:
        # Import the custom Ollama embedding function
        from modules.ollama_embedding import OllamaEmbeddingFunction
        
        # Check if we should use Ollama for embeddings
        use_ollama_embeddings = config.USE_OLLAMA_EMBEDDINGS
        
        if use_ollama_embeddings:
            try:
                # Create the Ollama embedding function
                emb_fn = OllamaEmbeddingFunction(
                    ollama_base_url=config.OLLAMA_HOST,
                    model_name=config.OLLAMA_MODEL
                )
                logger.info(f"Using Ollama for embeddings: {config.OLLAMA_HOST} with model {config.OLLAMA_MODEL}")
                return emb_fn
            except Exception as e:
                logger.error(f"Error setting up Ollama embedding function: {e}")
                logger.warning("Falling back to local embedding function")
                # Fall back to local embeddings
                use_ollama_embeddings = False
        
        # Use local sentence-transformer if not using Ollama
        if not use_ollama_embeddings:
            # Get the default embedding function
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            emb_fn = SentenceTransformerEmbeddingFunction(model_name="all-mpnet-base-v2")
            logger.info("Using local SentenceTransformer for embeddings")
            return emb_fn
            
    except Exception as e:
        logger.error(f"Error getting embedding function: {e}")
        logger.warning("No embedding function available, using default")
        return None


def init_db():
    """Initialize ChromaDB"""
    if not config.CHROMA_AVAILABLE:
        logger.warning("ChromaDB not available. Vector search will be disabled.")
        return None, None

    os.makedirs(config.DB_DIR, exist_ok=True)
    try:
        import chromadb
        
        # Add a retry mechanism to handle tenant initialization issues
        max_retries = 3
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                client = chromadb.PersistentClient(path=config.DB_DIR)
                
                # Get the embedding function
                emb_fn = get_embedding_function()
                    
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
                last_error = e
                logger.warning(f"Attempt {retry_count + 1} failed: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"Waiting before retry...")
                    time.sleep(2)  # Wait before retrying
        
        # If we get here, all retries failed
        logger.error(f"Error initializing ChromaDB after {max_retries} attempts: {last_error}")
        return None, None
    
    except Exception as e:
        logger.error(f"Error initializing ChromaDB: {e}")
        return None, None


def reset_database():
    """
    Reset the entire ChromaDB by removing the database directory and reinitializing it.
    
    Returns:
        tuple: (success_flag, message)
    """
    if not config.CHROMA_AVAILABLE:
        return False, "ChromaDB is not available."
    
    try:
        # Check if the database directory exists
        if not os.path.exists(config.DB_DIR):
            return False, "Database directory does not exist."
        
        # Log the reset operation
        logger.info(f"Resetting ChromaDB at {config.DB_DIR}")
        
        # Remove the database directory
        shutil.rmtree(config.DB_DIR)
        logger.info("Database directory removed successfully.")
        
        # Recreate the directory (empty)
        os.makedirs(config.DB_DIR, exist_ok=True)
        
        # Initialize a fresh database with retry mechanism
        client, collection = init_db()
        
        if client is None or collection is None:
            return False, "Failed to initialize new database after reset."
        
        # Additional verification step
        try:
            # Test adding a simple document to verify the collection is working
            test_id = "test_reset_doc"
            test_content = "This is a test document to verify the database is working."
            collection.add(
                ids=[test_id],
                documents=[test_content],
                metadatas=[{"source": "test", "type": "test"}]
            )
            
            # Delete the test document
            collection.delete(ids=[test_id])
            logger.info("Database reset verified with test document.")
        except Exception as e:
            logger.error(f"Database reset verification failed: {e}")
            return False, f"Database reset succeeded but verification failed: {str(e)}"
            
        return True, "Database reset successfully. Please reindex your documents."
        
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return False, f"Error resetting database: {str(e)}"