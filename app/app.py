import os
from flask import Flask, request, render_template, jsonify
import subprocess
import json
import yaml
import glob
import re
import hashlib
from pathlib import Path
import requests  # Added for remote Ollama API calls
import time

app = Flask(__name__)

# --- Configuration ---
DOCS_DIR = "./network_docs"
DB_DIR = "./chroma_db"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
SEARCH_RESULTS = 5
OLLAMA_HOST = "http://10.13.37.233:11434"  # Your desktop IP where Ollama is running
OLLAMA_MODEL = "network-assistant"  # Model to use

# Safely import ChromaDB with Python 3.12 compatibility
try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError as e:
    print(f"ChromaDB import error: {e}")
    CHROMA_AVAILABLE = False


# --- Database Initialization ---
def init_db():
    """Initialize ChromaDB with Python 3.12 compatibility"""
    if not CHROMA_AVAILABLE:
        print("WARNING: ChromaDB not available. Vector search will be disabled.")
        return None, None

    # Create DB directory
    os.makedirs(DB_DIR, exist_ok=True)

    try:
        # Initialize client using the most recent API
        client = chromadb.PersistentClient(path=DB_DIR)

        # Load the embedding model with error handling
        try:
            # Import embedding functions from the correct location
            from chromadb.utils.embedding_functions import (
                SentenceTransformerEmbeddingFunction,
            )

            emb_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        except Exception as e:
            print(f"Error loading sentence transformer: {e}")
            emb_fn = None

        # Create or get collection
        try:
            # Try to get existing collection first
            collection = client.get_collection(name="network_docs")
            print("Found existing collection: network_docs")
        except ValueError:
            # Create new collection if it doesn't exist
            collection = client.create_collection(
                name="network_docs", embedding_function=emb_fn
            )
            print("Created new collection: network_docs")

        return client, collection
    except Exception as e:
        print(f"Error initializing ChromaDB: {e}")
        return None, None


# Initialize database at module level
db_client, collection = init_db()


# --- Document Processing ---
def split_into_chunks(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks with Python 3.12 compatibility"""
    chunks = []

    # Split by paragraphs first
    paragraphs = re.split(r"\n\s*\n", text)
    current_chunk = ""

    for para in paragraphs:
        # If adding this paragraph exceeds chunk size, save current chunk and start a new one
        if len(current_chunk) + len(para) > chunk_size:
            chunks.append(current_chunk.strip())
            # Start new chunk with overlap from the previous chunk
            words = current_chunk.split()
            if len(words) > overlap:
                current_chunk = " ".join(words[-overlap:]) + "\n" + para
            else:
                current_chunk = para
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para

    # Add the last chunk if it has content
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def get_document_status(docs_dir, collection, chroma_available):
    """
    Get the status of all documents - indexed, unindexed, and modified.
    
    Returns:
    {
        "indexed": [list of indexed files],
        "unindexed": [list of unindexed files],
        "modified": [list of modified files],
        "needs_indexing": boolean
    }
    """
    indexed_files = []
    unindexed_files = []
    modified_files = []
    
    # Create docs directory if it doesn't exist
    os.makedirs(docs_dir, exist_ok=True)
    
    # Path to the document tracking file
    tracking_file = os.path.join(docs_dir, ".doc_tracking.json")
    
    # Load existing tracking data if available
    tracking_data = {}
    if os.path.exists(tracking_file):
        try:
            with open(tracking_file, 'r', encoding='utf-8') as f:
                tracking_data = json.load(f)
        except Exception as e:
            print(f"Error loading tracking data: {e}")
    
    # Scan all documents in the directory
    doc_files = []
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.startswith('.'):  # Skip hidden files
                continue
                
            file_path = os.path.join(root, file)
            if file_path.endswith((".txt", ".md", ".yaml", ".yml")):
                doc_files.append(file_path)
    
    # Update tracking for all current files
    new_tracking_data = {}
    
    for file_path in doc_files:
        rel_path = os.path.relpath(file_path, docs_dir)
        file_id = hashlib.md5(file_path.encode()).hexdigest()
        
        # Get current file info
        try:
            mtime = os.path.getmtime(file_path)
            size = os.path.getsize(file_path)
            file_info = {
                "mtime": mtime,
                "size": size,
                "id": file_id
            }
            new_tracking_data[rel_path] = file_info
            
            # Check if file is indexed
            is_indexed = False
            if chroma_available and collection is not None:
                try:
                    # Check if at least one chunk exists in the collection
                    result = collection.get(ids=[file_id + "_0"])
                    is_indexed = bool(result["ids"])
                except Exception:
                    is_indexed = False
            
            # Check if file has been modified since last indexing
            is_modified = False
            if rel_path in tracking_data:
                old_info = tracking_data[rel_path]
                if old_info["mtime"] != mtime or old_info["size"] != size:
                    is_modified = True
            
            # Categorize the file
            if is_indexed and not is_modified:
                indexed_files.append(rel_path)
            elif is_indexed and is_modified:
                modified_files.append(rel_path)
            else:
                unindexed_files.append(rel_path)
                
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            unindexed_files.append(rel_path)
    
    # Save updated tracking data
    try:
        with open(tracking_file, 'w', encoding='utf-8') as f:
            json.dump(new_tracking_data, f, indent=2)
    except Exception as e:
        print(f"Error saving tracking data: {e}")
    
    # Return the document status
    return {
        "indexed": sorted(indexed_files),
        "unindexed": sorted(unindexed_files),
        "modified": sorted(modified_files),
        "needs_indexing": len(unindexed_files) > 0 or len(modified_files) > 0
    }


def index_documents(docs_dir=DOCS_DIR, specific_files=None):
    """
    Index all documentation files into the vector database
    
    Parameters:
    - docs_dir: Directory containing documents to index
    - specific_files: List of specific file paths to index (relative to docs_dir)
    
    Returns:
    {
        "status": "success" or "error",
        "indexed": Number of new files indexed,
        "updated": Number of existing files updated,
        "skipped": Number of files skipped,
        "error": Error message (if any)
    }
    """
    if not CHROMA_AVAILABLE or collection is None:
        return {"status": "error", "error": "ChromaDB not available", "indexed": 0, "updated": 0, "skipped": 0}

    files_indexed = 0
    files_updated = 0
    files_skipped = 0
    os.makedirs(docs_dir, exist_ok=True)
    
    # Get document status
    doc_status = get_document_status(docs_dir, collection, CHROMA_AVAILABLE)
    
    # Determine which files to process
    files_to_process = []
    if specific_files:
        # Convert relative paths to absolute
        for rel_path in specific_files:
            abs_path = os.path.join(docs_dir, rel_path)
            if os.path.exists(abs_path):
                files_to_process.append(abs_path)
    else:
        # Process unindexed and modified files
        for rel_path in doc_status["unindexed"] + doc_status["modified"]:
            files_to_process.append(os.path.join(docs_dir, rel_path))
    
    # Process each file
    for file_path in files_to_process:
        try:
            file_path = os.path.normpath(file_path)
            file_id = hashlib.md5(file_path.encode()).hexdigest()
            rel_path = os.path.relpath(file_path, docs_dir)
            
            # Check if this file was previously indexed
            is_update = rel_path in doc_status["modified"]
            
            # If this is an update, remove old entries first
            if is_update:
                try:
                    # Find all chunks with this file_id prefix
                    results = collection.get(where={"source": file_path})
                    if results and results["ids"]:
                        collection.delete(ids=results["ids"])
                except Exception as e:
                    print(f"Error removing old chunks for {file_path}: {e}")
            
            # Process file based on extension
            if file_path.endswith((".txt", ".md")):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Split into smaller chunks with overlap
                chunks = split_into_chunks(content)

                # Get current modification time
                mtime = str(os.path.getmtime(file_path))
                
                # Add chunks to collection
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{file_id}_{i}"
                    try:
                        collection.add(
                            ids=[chunk_id],
                            documents=[chunk],
                            metadatas=[{"source": file_path, "chunk": i, "mtime": mtime}],
                        )
                    except Exception as e:
                        print(f"Error adding chunk {i} from {file_path}: {e}")
                        continue

            elif file_path.endswith((".yaml", ".yml")):
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = yaml.safe_load(f)
                        content = json.dumps(data, indent=2)

                        # Get current modification time
                        mtime = str(os.path.getmtime(file_path))
                        
                        collection.add(
                            ids=[file_id],
                            documents=[content],
                            metadatas=[{"source": file_path, "type": "config", "mtime": mtime}],
                        )
                    except Exception as e:
                        print(f"Error processing YAML file {file_path}: {e}")
                        continue
            else:
                # Skip files with unsupported extensions
                files_skipped += 1
                continue
                
            # Update counters
            if is_update:
                files_updated += 1
            else:
                files_indexed += 1
                
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            files_skipped += 1

    return {
        "status": "success", 
        "indexed": files_indexed, 
        "updated": files_updated, 
        "skipped": files_skipped
    }


def query_vector_db(query, n_results=SEARCH_RESULTS):
    """Search the vector database for relevant context"""
    if not CHROMA_AVAILABLE or collection is None:
        return "Vector search not available. Using default knowledge."

    try:
        results = collection.query(query_texts=[query], n_results=n_results)

        # Combine results into a single context string
        context = ""
        if results and len(results.get("documents", [[]])[0]) > 0:
            for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
                source = os.path.basename(metadata["source"])
                context += f"\n--- From {source} ---\n{doc}\n"

        return context
    except Exception as e:
        print(f"Error querying vector database: {e}")
        return "Error retrieving context from database."


# Track conversation history
class ConversationTracker:
    def __init__(self):
        self.conversations = {}  # session_id -> conversation history
        
    def add_message(self, session_id, role, content):
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        self.conversations[session_id].append({"role": role, "content": content})
        
    def get_conversation(self, session_id):
        return self.conversations.get(session_id, [])

# Initialize conversation tracker
conversation_tracker = ConversationTracker()


# --- Web Routes ---
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/index_docs", methods=["POST"])
def index_endpoint():
    """Index documents into the vector database"""
    try:
        # Check if specific files were requested
        specific_files = None
        if request.is_json:
            data = request.get_json()
            if data and "files" in data:
                specific_files = data["files"]
        
        # Call the indexing function
        result = index_documents(specific_files=specific_files)
        return jsonify(result)
    except Exception as e:
        print(f"Error in index_docs endpoint: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "indexed": 0,
            "updated": 0,
            "skipped": 0
        })


@app.route("/document_status", methods=["GET"])
def document_status_endpoint():
    """Return status information about indexed and unindexed documents"""
    try:
        status = get_document_status(DOCS_DIR, collection, CHROMA_AVAILABLE)
        
        # Add summary counts
        status["counts"] = {
            "indexed": len(status["indexed"]),
            "unindexed": len(status["unindexed"]),
            "modified": len(status["modified"]),
            "total": len(status["indexed"]) + len(status["unindexed"]) + len(status["modified"])
        }
        
        return jsonify(status)
    except Exception as e:
        print(f"Error in document_status endpoint: {e}")
        return jsonify({
            "error": str(e),
            "indexed": [],
            "unindexed": [],
            "modified": [],
            "counts": {"indexed": 0, "unindexed": 0, "modified": 0, "total": 0},
            "needs_indexing": False
        })


@app.route("/status", methods=["GET"])
def status_endpoint():
    """Return status information about the application"""
    # Count indexed documents
    indexed_docs = 0
    if CHROMA_AVAILABLE and collection is not None:
        try:
            all_ids = collection.get()
            if all_ids and "ids" in all_ids:
                indexed_docs = len(all_ids["ids"])
        except Exception as e:
            print(f"Error getting document count: {e}")
    
    # Get document files
    doc_files = []
    try:
        for file_path in glob.glob(f"{DOCS_DIR}/**/*.*", recursive=True):
            if file_path.endswith((".txt", ".md", ".yaml", ".yml")):
                doc_files.append(os.path.basename(file_path))
    except Exception as e:
        print(f"Error listing documents: {e}")
    
    # Get model information from Ollama
    model_info = {
        "name": OLLAMA_MODEL,
        "base": "Unknown",
        "size": ""
    }
    
    try:
        # Call Ollama API with POST method (important!)
        response = requests.post(f"{OLLAMA_HOST}/api/show", json={"name": OLLAMA_MODEL})
        
        if response.status_code == 200:
            model_data = response.json()
            
            # Extract base model information
            if "details" in model_data:
                details = model_data["details"]
                if "parent_model" in details:
                    model_info["base"] = details["parent_model"]
                elif "family" in details:
                    model_info["base"] = details["family"]
                
                # Get parameter size
                if "parameter_size" in details:
                    model_info["size"] = details["parameter_size"]
            
            # Try extracting from model_info if still unknown
            if model_info["base"] == "Unknown" and "model_info" in model_data:
                info = model_data["model_info"]
                if "general.basename" in info:
                    model_info["base"] = info["general.basename"]
                
                if "general.parameter_count" in info:
                    try:
                        count = int(info["general.parameter_count"])
                        model_info["size"] = f"{count / 1_000_000_000:.1f}B"
                    except:
                        pass
            
            # Try extracting from modelfile as a fallback
            if model_info["base"] == "Unknown" and "modelfile" in model_data:
                for line in model_data["modelfile"].split("\n"):
                    if line.startswith("FROM "):
                        from_value = line.replace("FROM ", "").strip()
                        # Only use if it's not a blob SHA or path
                        if not ("sha256" in from_value or "\\" in from_value or "/" in from_value):
                            model_info["base"] = from_value
                            break
    
    except Exception as e:
        print(f"Error getting model information: {e}")
    
    # Format the base model with size if available
    if model_info["size"] and model_info["base"] != "Unknown":
        model_info["base"] = f"{model_info['base']} ({model_info['size']})"
    
    return jsonify({
        "chroma_available": CHROMA_AVAILABLE,
        "ollama_host": OLLAMA_HOST,
        "ollama_model": OLLAMA_MODEL,
        "model_base": model_info["base"],
        "indexed_docs": indexed_docs,
        "doc_files": doc_files
    })


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        message = data.get("message", "")
        session_id = data.get("session_id", "default")
        
        # Add message to conversation history
        conversation_tracker.add_message(session_id, "user", message)
        
        # Get relevant context from the vector database
        context = query_vector_db(message)
        
        # Prepare system prompt with conversation history
        history = conversation_tracker.get_conversation(session_id)
        history_prompt = "\nConversation history:\n"
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_prompt += f"{role}: {msg['content']}\n"
        
        # Build the full prompt for Ollama
        if context and len(context.strip()) > 10:
            prompt = f"""You are a helpful network troubleshooting assistant. 
Here's some context from the knowledge base that might be relevant:

{context}

{history_prompt}

User's latest message: {message}

Respond in a helpful and informative way. All troubleshooting should be done through natural conversation.
"""
        else:
            prompt = f"""You are a helpful network troubleshooting assistant.

{history_prompt}

User's latest message: {message}

Respond in a helpful and informative way. All troubleshooting should be done through natural conversation.
"""
        
        # Call the Ollama API
        try:
            response = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7
                    }
                },
                timeout=60
            )
            
            if response.status_code != 200:
                return jsonify({
                    "response": f"Error from Ollama API: {response.text}",
                    "context_used": bool(context),
                    "sources": [],
                })
                
            result = response.json()
            assistant_response = result.get("response", "")
            
        except Exception as e:
            assistant_response = f"Error running Ollama: {str(e)}"
        
        # Add assistant response to history
        conversation_tracker.add_message(session_id, "assistant", assistant_response)
        
        # Get sources for the frontend
        sources = []
        if CHROMA_AVAILABLE and collection is not None:
            try:
                results = collection.query(query_texts=[message])
                if results.get("metadatas") and results["metadatas"][0]:
                    sources = [os.path.basename(m["source"]) for m in results["metadatas"][0]]
            except Exception as e:
                print(f"Error getting sources: {e}")
        
        return jsonify({
            "response": assistant_response,
            "context_used": bool(context),
            "sources": sources
        })
    
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({
            "response": f"An error occurred: {str(e)}",
            "context_used": False,
            "sources": [],
        })


if __name__ == "__main__":
    # Make sure the docs directory exists
    os.makedirs(DOCS_DIR, exist_ok=True)

    # Check if we can connect to Ollama at startup
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags")
        if response.status_code == 200:
            print(f"Successfully connected to Ollama at {OLLAMA_HOST}")
        else:
            print(f"Warning: Ollama responded with status code {response.status_code}")
    except Exception as e:
        print(f"WARNING: Could not connect to Ollama at {OLLAMA_HOST}: {e}")

    # Start the application
    app.run(debug=True, host="0.0.0.0", port=5000)