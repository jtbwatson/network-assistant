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
            logger.error(f"Error updating document count: {e}")
    
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
                logger.info(f"Using Ollama for embeddings: {config.OLLAMA_HOST} with model {config.OLLAMA_EMBEDDING_MODEL}")
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
                logger.info(f"Initializing ChromaDB (attempt {retry_count + 1}/{MAX_RETRIES})")
                
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
                    logger.info(f"Found existing collection: {db_status.collection_name}")
                except ValueError:
                    collection = client.create_collection(
                        name=db_status.collection_name, 
                        embedding_function=emb_fn
                    )
                    logger.info(f"Created new collection: {db_status.collection_name}")
                
                # Update status
                db_status.initialized = True
                db_status.initialization_time = time.time() - start_time
                db_status.update_document_count(collection)
                
                logger.info(f"ChromaDB initialized successfully in {db_status.initialization_time:.2f}s with {db_status.document_count} documents")
                return client, collection
                
            except Exception as e:
                logger.warning(f"Attempt {retry_count + 1} failed: {e}")
                db_status.last_error = str(e)
                
                if retry_count < MAX_RETRIES - 1:
                    logger.info(f"Waiting {RETRY_DELAY}s before retry...")
                    time.sleep(RETRY_DELAY)
        
        # If we get here, all retries failed
        logger.error(f"Error initializing ChromaDB after {MAX_RETRIES} attempts: {db_status.last_error}")
        return None, None
    
    except Exception as e:
        logger.error(f"Error initializing ChromaDB: {e}")
        db_status.last_error = str(e)
        return None, None


def reset_database():
    """
    Reset the ChromaDB by completely removing and recreating the database directory.
    Handles permission issues and locked files.
    
    Returns:
        tuple: (success_flag, message)
    """
    if not config.CHROMA_AVAILABLE:
        return False, "ChromaDB is not available."
    
    import chromadb
    import shutil
    import time
    import tempfile
    import stat
    import sys
    
    # Log the reset operation
    logger.info(f"Resetting ChromaDB at {config.DB_DIR}")
    
    # Step 1: Try to close any existing connections
    try:
        logger.info("Closing any existing database connections...")
        try:
            temp_client = chromadb.PersistentClient(path=config.DB_DIR)
            collections = temp_client.list_collections()
            logger.info(f"Found {len(collections)} collections")
            
            # Try to delete collections explicitly
            for collection in collections:
                try:
                    logger.info(f"Attempting to delete collection: {collection.name}")
                    temp_client.delete_collection(collection.name)
                except Exception as e:
                    logger.warning(f"Could not delete collection {collection.name}: {e}")
                    
            # Delete the client
            del temp_client
            logger.info("Closed database connections")
        except Exception as e:
            logger.warning(f"Error handling existing connections: {e}")
        
        # Force garbage collection to release file handles
        import gc
        gc.collect()
        
        # Wait a moment to ensure file handles are released
        logger.info("Waiting for file handles to be released...")
        time.sleep(2)
    except Exception as e:
        logger.warning(f"Error during connection cleanup: {e}")
    
    # Step 2: Create a backup if possible
    backup_dir = None
    if os.path.exists(config.DB_DIR):
        backup_dir = f"{config.DB_DIR}_backup_{int(time.time())}"
        try:
            logger.info(f"Creating backup at {backup_dir}")
            shutil.copytree(config.DB_DIR, backup_dir)
            logger.info(f"Backup created at {backup_dir}")
        except Exception as e:
            logger.warning(f"Could not create backup: {e}")
            backup_dir = None
    
    # Step 3: Completely remove the database directory with error handling
    success = False
    
    # Use a temporary directory as an intermediary step
    temp_dir = None
    try:
        if os.path.exists(config.DB_DIR):
            # First try to fix permissions
            logger.info("Checking and fixing permissions...")
            try:
                for root, dirs, files in os.walk(config.DB_DIR):
                    for d in dirs:
                        try:
                            os.chmod(os.path.join(root, d), stat.S_IRWXU)
                        except Exception:
                            pass
                    for f in files:
                        try:
                            os.chmod(os.path.join(root, f), stat.S_IRWXU)
                        except Exception:
                            pass
            except Exception as e:
                logger.warning(f"Error fixing permissions: {e}")
            
            # Try direct remove first
            logger.info(f"Attempting to remove directory: {config.DB_DIR}")
            try:
                shutil.rmtree(config.DB_DIR)
                logger.info("Successfully removed database directory")
                success = True
            except Exception as e:
                logger.warning(f"Could not remove directory directly: {e}")
                
                # If direct removal failed, try rename and then remove
                if not success:
                    try:
                        # Create a temporary directory
                        temp_dir = tempfile.mkdtemp(prefix="chroma_temp_")
                        temp_target = os.path.join(temp_dir, "old_db")
                        
                        logger.info(f"Attempting to rename directory to {temp_target}")
                        # On Windows, this can often work even when rmtree fails
                        os.rename(config.DB_DIR, temp_target)
                        
                        # Now try to remove the renamed directory
                        try:
                            shutil.rmtree(temp_target)
                        except Exception as e2:
                            logger.warning(f"Could not remove renamed directory: {e2}")
                            # Not fatal, we've at least renamed it out of the way
                            
                        success = True
                        logger.info("Successfully renamed directory out of the way")
                    except Exception as e2:
                        logger.error(f"Could not rename directory: {e2}")
                        
                        # One last desperate attempt - try to empty the directory
                        if not success:
                            try:
                                logger.info("Attempting to empty directory contents...")
                                for item in os.listdir(config.DB_DIR):
                                    item_path = os.path.join(config.DB_DIR, item)
                                    try:
                                        if os.path.isfile(item_path):
                                            os.unlink(item_path)
                                        elif os.path.isdir(item_path):
                                            shutil.rmtree(item_path)
                                    except Exception as e3:
                                        logger.warning(f"Could not remove {item_path}: {e3}")
                                
                                success = True
                                logger.info("Successfully emptied directory")
                            except Exception as e3:
                                logger.error(f"Could not empty directory: {e3}")
    except Exception as e:
        logger.error(f"Error during database directory removal: {e}")
    
    # Clean up temp directory if it exists
    if temp_dir and os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass
    
    # Step 4: Create a fresh directory
    try:
        logger.info(f"Creating fresh database directory at {config.DB_DIR}")
        os.makedirs(config.DB_DIR, exist_ok=True)
        
        # Ensure proper permissions
        os.chmod(config.DB_DIR, stat.S_IRWXU)
        
        logger.info("Successfully created fresh database directory")
    except Exception as e:
        logger.error(f"Could not create fresh directory: {e}")
        return False, f"Failed to create database directory: {str(e)}"
    
    # Step 5: Initialize a fresh database
    try:
        # Wait a moment before creating new client
        logger.info("Waiting before initializing new database...")
        time.sleep(2)
        
        logger.info("Initializing new ChromaDB client...")
        new_client = chromadb.PersistentClient(path=config.DB_DIR)
        
        # Get embedding function
        emb_fn = get_embedding_function()
        
        # Create a new collection
        collection_name = "network_docs"
        logger.info(f"Creating new collection: {collection_name}")
        new_collection = new_client.create_collection(
            name=collection_name, 
            embedding_function=emb_fn
        )
        
        # Test with a simple document
        logger.info("Testing new collection with sample document...")
        test_id = "test_reset_doc"
        test_content = "This is a test document to verify the database is working."
        
        new_collection.add(
            ids=[test_id],
            documents=[test_content],
            metadatas=[{"source": "test", "type": "test"}]
        )
        
        # Verify retrieval
        result = new_collection.get(ids=[test_id])
        if not result or not result["ids"]:
            raise Exception("Could not retrieve test document")
            
        # Delete the test document
        new_collection.delete(ids=[test_id])
        logger.info("Database reset verified with test document")
        
        # Clean up
        del new_collection
        del new_client
        
        # Force garbage collection again
        gc.collect()
        
        # Success
        return True, "Database reset successfully. For best results, please restart the application."
        
    except Exception as e:
        logger.error(f"Error setting up new database: {e}")
        error_msg = str(e)
        
        # Special handling for specific errors
        if "readonly database" in error_msg.lower():
            # Add more detailed message for this common error
            return False, "Database appears to be locked or have permission issues. Please restart the application and try again."
        
        return False, f"Error creating new database: {error_msg}"


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