import requests
import numpy as np
from typing import List
import logging

logger = logging.getLogger(__name__)

class OllamaEmbeddingFunction:
    """
    Custom embedding function that uses Ollama's embedding API
    to generate embeddings for ChromaDB.
    """
    
    def __init__(self, ollama_base_url, model_name, batch_size=10):
        """
        Initialize the Ollama embedding function.
        
        Args:
            ollama_base_url: Base URL of the Ollama API (e.g., "http://localhost:11434")
            model_name: Name of the Ollama model to use for embeddings
            batch_size: Number of texts to batch together in one request
        """
        self.ollama_base_url = ollama_base_url.rstrip('/')
        self.model_name = model_name
        self.batch_size = batch_size
        self.embedding_endpoint = f"{self.ollama_base_url}/api/embeddings"
        
        # Verify connection to Ollama
        try:
            self._test_connection()
            logger.info(f"Successfully connected to Ollama embedding API at {self.ollama_base_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama embedding API: {e}")
            raise
            
    def _test_connection(self):
        """Test the connection to the Ollama API"""
        response = requests.post(
            self.embedding_endpoint,
            json={"model": self.model_name, "prompt": "test"}
        )
        if response.status_code != 200:
            raise ConnectionError(f"Failed to connect to Ollama API: {response.text}")
    
    def _get_embedding(self, text):
        """Get embedding for a single text"""
        try:
            response = requests.post(
                self.embedding_endpoint,
                json={"model": self.model_name, "prompt": text}
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.text}")
                # Return zeros as fallback
                return np.zeros(1536)  # Default embedding size
                
            embedding = response.json().get("embedding", [])
            return np.array(embedding)
            
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            # Return zeros as fallback
            return np.zeros(1536)  # Default embedding size
    
    def __call__(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings as numpy arrays
        """
        all_embeddings = []
        
        # Process in batches to avoid overloading Ollama
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            # Get embeddings one by one (Ollama doesn't support batching yet)
            batch_embeddings = []
            for text in batch:
                embedding = self._get_embedding(text)
                batch_embeddings.append(embedding)
            
            all_embeddings.extend(batch_embeddings)
            
            # Log progress for long batches
            if len(texts) > self.batch_size:
                logger.info(f"Processed {min(i + self.batch_size, len(texts))}/{len(texts)} embeddings")
        
        return all_embeddings