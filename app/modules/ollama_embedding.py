import requests
import numpy as np
from typing import List, Union
import logging
import time

logger = logging.getLogger(__name__)

class OllamaEmbeddingFunction:
    """
    Custom embedding function that uses Ollama's embedding API
    to generate embeddings for ChromaDB.
    """
    
    # Default embedding dimension if the API fails
    DEFAULT_EMBEDDING_DIM = 1536
    
    def __init__(self, ollama_base_url, model_name, batch_size=10):
        """
        Initialize the Ollama embedding function.
        
        Args:
            ollama_base_url: Base URL of the Ollama API (e.g., "http://localhost:11434")
            model_name: Name of the Ollama model to use for embeddings
            batch_size: Number of texts to batch together in one request
        """
        logger.info(f"INITIALIZING OllamaEmbeddingFunction with URL: {ollama_base_url} and model: {model_name}")
        self.ollama_base_url = ollama_base_url.rstrip('/')
        self.model_name = model_name
        self.batch_size = batch_size
        self.embedding_endpoint = f"{self.ollama_base_url}/api/embeddings"
        
        # Verify connection to Ollama
        try:
            logger.info(f"Testing connection to {self.embedding_endpoint}")
            self._test_connection()
            logger.info(f"✅ Successfully connected to Ollama embedding API at {self.ollama_base_url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Ollama embedding API: {e}")
            raise
            
    def _test_connection(self):
        """Test the connection to the Ollama API"""
        logger.info(f"Testing API connection with model {self.model_name}")
        response = self._make_api_request("test")
        
        # Log successful response
        result = response.json()
        embedding = result.get("embedding", [])
        logger.info(f"Test connection successful - received embedding of length {len(embedding)}")
    
    def _make_api_request(self, text):
        """Make a request to the Ollama API and handle errors"""
        response = requests.post(
            self.embedding_endpoint,
            json={
                "model": self.model_name, 
                "prompt": text,
                "options": {
                    "gpu_layers": 100  # Try to force GPU usage
                }
            }
        )
        
        if response.status_code != 200:
            error_msg = f"Failed to connect to Ollama API: {response.text}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)
            
        return response
    
    def _get_embedding(self, text):
        """Get embedding for a single text"""
        try:
            logger.debug(f"Requesting embedding for text of length {len(text)}")
            start_time = time.time()
            
            response = self._make_api_request(text)
            
            elapsed = time.time() - start_time
            
            result = response.json()    
            embedding = result.get("embedding", [])
            logger.debug(f"✅ Got embedding in {elapsed:.2f}s - length: {len(embedding)}")
            
            # Convert to list to avoid NumPy array truth value issues
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Error getting embedding: {e}")
            # Return zeros as fallback - as a list, not numpy array
            return [0.0] * self.DEFAULT_EMBEDDING_DIM
    
    def __call__(self, input: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for a text or list of texts.
        
        Args:
            input: Text or list of texts to embed
            
        Returns:
            List of embeddings as lists of floats (not numpy arrays)
        """
        # Handle single string input (convert to list)
        if isinstance(input, str):
            texts = [input]
            logger.info(f"Called with single text of length {len(input)}")
        else:
            texts = input
            logger.info(f"Called with {len(texts)} texts to embed")
            
        all_embeddings = []
        start_time = time.time()
        
        # Process in batches to avoid overloading Ollama
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_start = time.time()
            
            # Get embeddings one by one (Ollama doesn't support batching yet)
            batch_embeddings = []
            for text in batch:
                # Get embedding as a list of floats, not numpy array
                embedding = self._get_embedding(text)
                batch_embeddings.append(embedding)
            
            all_embeddings.extend(batch_embeddings)
            batch_elapsed = time.time() - batch_start
            
            # Log progress for long batches
            if len(texts) > self.batch_size:
                logger.info(f"Processed batch {i//self.batch_size + 1}/{(len(texts)-1)//self.batch_size + 1} in {batch_elapsed:.2f}s")
        
        total_time = time.time() - start_time
        logger.info(f"✅ Generated {len(all_embeddings)} embeddings in {total_time:.2f}s (avg: {total_time/len(all_embeddings):.2f}s per embedding)")
        
        # Ensure we return lists of floats, not numpy arrays
        return all_embeddings