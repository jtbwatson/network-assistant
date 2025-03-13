import os
import json
import yaml
import re
import hashlib
import requests
import logging
from collections import defaultdict
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

load_dotenv()

# --- Configuration ---
DOCS_DIR = "./network_docs"
DB_DIR = "./chroma_db"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
SEARCH_RESULTS = 5
OLLAMA_HOST = os.getenv("OLLAMA_HOST")  # Get OLLAMA_HOST from environment variables
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")  # Get OLLAMA_MODEL from environment variables

# Safely import ChromaDB
try:
    import chromadb

    CHROMA_AVAILABLE = True
except ImportError as e:
    logger.error(f"ChromaDB import error: {e}")
    CHROMA_AVAILABLE = False


# --- Database Initialization ---
def init_db():
    """Initialize ChromaDB"""
    if not CHROMA_AVAILABLE:
        logger.warning("ChromaDB not available. Vector search will be disabled.")
        return None, None

    os.makedirs(DB_DIR, exist_ok=True)
    try:
        client = chromadb.PersistentClient(path=DB_DIR)
        try:
            from chromadb.utils.embedding_functions import (
                SentenceTransformerEmbeddingFunction,
            )

            emb_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        except Exception as e:
            logger.error(f"Error loading sentence transformer: {e}")
            emb_fn = None
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


# Initialize database at module level
db_client, collection = init_db()


# --- Document Processing ---
def split_into_chunks(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks"""
    chunks = []
    paragraphs = re.split(r"\n\s*\n", text)
    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) > chunk_size:
            chunks.append(current_chunk.strip())
            words = current_chunk.split()
            current_chunk = (
                " ".join(words[-overlap:]) + "\n" + para
                if len(words) > overlap
                else para
            )
        else:
            current_chunk = current_chunk + "\n\n" + para if current_chunk else para
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks


def get_document_status(docs_dir, collection, chroma_available):
    """
    Get status of all documents.
    Returns a dict with indexed, unindexed, modified, and needs_indexing keys.
    """
    os.makedirs(docs_dir, exist_ok=True)
    tracking_file = os.path.join(docs_dir, ".doc_tracking.json")
    try:
        with open(tracking_file, "r", encoding="utf-8") as f:
            tracking_data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading tracking data: {e}")
        tracking_data = {}

    valid_ext = (".txt", ".md", ".yaml", ".yml")
    doc_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(docs_dir)
        for file in files
        if not file.startswith(".") and file.endswith(valid_ext)
    ]

    indexed_files, unindexed_files, modified_files = [], [], []
    new_tracking_data = {}

    # Get all indexed document sources from ChromaDB
    indexed_sources = set()
    if chroma_available and collection is not None:
        try:
            # Get all documents and their metadata
            all_docs = collection.get()
            if all_docs and "metadatas" in all_docs and all_docs["metadatas"]:
                for metadata in all_docs["metadatas"]:
                    if metadata and "source" in metadata:
                        # Normalize the path to handle different path formats
                        normalized_path = os.path.normpath(metadata["source"])
                        indexed_sources.add(normalized_path)

                        # Also add the relative path version
                        try:
                            rel_path = os.path.relpath(normalized_path, docs_dir)
                            indexed_sources.add(os.path.join(docs_dir, rel_path))
                        except ValueError:
                            pass

            logger.info(f"Found {len(indexed_sources)} unique sources in ChromaDB")
            # Debug: print first 5 sources to help diagnose issues
            for i, source in enumerate(list(indexed_sources)[:5]):
                logger.info(f"Sample source {i+1}: {source}")
        except Exception as e:
            logger.error(f"Error fetching sources from ChromaDB: {e}")

    for file_path in doc_files:
        rel_path = os.path.relpath(file_path, docs_dir)
        abs_path = os.path.abspath(file_path)
        normalized_path = os.path.normpath(file_path)
        file_id = hashlib.md5(file_path.encode()).hexdigest()

        try:
            mtime = os.path.getmtime(file_path)
            size = os.path.getsize(file_path)
            file_info = {"mtime": mtime, "size": size, "id": file_id}
            new_tracking_data[rel_path] = file_info

            # Check if this file is indexed using multiple path formats
            is_indexed = (
                file_path in indexed_sources
                or abs_path in indexed_sources
                or normalized_path in indexed_sources
            )

            # If not found by path, try the old ID-based approach as fallback
            if not is_indexed and chroma_available and collection is not None:
                try:
                    # Try with both formats: with and without chunk suffix
                    results = collection.get(ids=[file_id])
                    is_indexed = bool(results.get("ids"))

                    if not is_indexed:
                        results = collection.get(ids=[file_id + "_0"])
                        is_indexed = bool(results.get("ids"))
                except Exception as e:
                    logger.error(f"Error checking {file_path} by ID: {e}")

            # Log the result for debugging
            logger.info(f"File {rel_path}: indexed={is_indexed}")

            is_modified = rel_path in tracking_data and (
                tracking_data[rel_path]["mtime"] != mtime
                or tracking_data[rel_path]["size"] != size
            )

            if is_indexed and not is_modified:
                indexed_files.append(rel_path)
            elif is_indexed and is_modified:
                modified_files.append(rel_path)
            else:
                unindexed_files.append(rel_path)
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            unindexed_files.append(rel_path)

    try:
        with open(tracking_file, "w", encoding="utf-8") as f:
            json.dump(new_tracking_data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving tracking data: {e}")

    # Log the results
    logger.info(
        f"Document status: {len(indexed_files)} indexed, {len(unindexed_files)} unindexed, {len(modified_files)} modified"
    )

    return {
        "indexed": sorted(indexed_files),
        "unindexed": sorted(unindexed_files),
        "modified": sorted(modified_files),
        "needs_indexing": bool(unindexed_files or modified_files),
    }


def index_documents(docs_dir=DOCS_DIR, specific_files=None):
    """
    Index documentation files into the vector database.
    Returns status and counts for indexing, updating, and skipped files.
    """
    if not CHROMA_AVAILABLE or collection is None:
        return {
            "status": "error",
            "error": "ChromaDB not available",
            "indexed": 0,
            "updated": 0,
            "skipped": 0,
        }

    files_indexed, files_updated, files_skipped = 0, 0, 0
    os.makedirs(docs_dir, exist_ok=True)
    doc_status = get_document_status(docs_dir, collection, CHROMA_AVAILABLE)
    files_to_process = []
    if specific_files:
        for rel_path in specific_files:
            abs_path = os.path.join(docs_dir, rel_path)
            if os.path.exists(abs_path):
                files_to_process.append(abs_path)
    else:
        for rel_path in doc_status["unindexed"] + doc_status["modified"]:
            files_to_process.append(os.path.join(docs_dir, rel_path))

    for file_path in files_to_process:
        try:
            file_path = os.path.normpath(file_path)
            file_id = hashlib.md5(file_path.encode()).hexdigest()
            rel_path = os.path.relpath(file_path, docs_dir)
            is_update = rel_path in doc_status["modified"]
            if is_update:
                try:
                    results = collection.get(where={"source": file_path})
                    if results and results["ids"]:
                        collection.delete(ids=results["ids"])
                except Exception as e:
                    logger.error(f"Error removing old chunks for {file_path}: {e}")
            mtime = str(os.path.getmtime(file_path))
            if file_path.endswith((".txt", ".md")):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                chunks = split_into_chunks(content)
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{file_id}_{i}"
                    try:
                        collection.add(
                            ids=[chunk_id],
                            documents=[chunk],
                            metadatas=[
                                {"source": file_path, "chunk": i, "mtime": mtime}
                            ],
                        )
                    except Exception as e:
                        logger.error(f"Error adding chunk {i} from {file_path}: {e}")
                        continue
            elif file_path.endswith((".yaml", ".yml")):
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = yaml.safe_load(f)
                        content = json.dumps(data, indent=2)
                        collection.add(
                            ids=[file_id],
                            documents=[content],
                            metadatas=[
                                {"source": file_path, "type": "config", "mtime": mtime}
                            ],
                        )
                    except Exception as e:
                        logger.error(f"Error processing YAML file {file_path}: {e}")
                        continue
            else:
                files_skipped += 1
                continue
            if is_update:
                files_updated += 1
            else:
                files_indexed += 1
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            files_skipped += 1
    return {
        "status": "success",
        "indexed": files_indexed,
        "updated": files_updated,
        "skipped": files_skipped,
    }


def query_vector_db(query, n_results=SEARCH_RESULTS):
    """Search the vector database for relevant context"""
    if not CHROMA_AVAILABLE or collection is None:
        return "Vector search not available. Using default knowledge."
    try:
        results = collection.query(query_texts=[query], n_results=n_results)
        context = ""
        if (
            results
            and results.get("documents", [[]])
            and len(results.get("documents", [[]])[0]) > 0
        ):
            for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
                source = os.path.basename(metadata["source"])
                context += f"\n--- From {source} ---\n{doc}\n"
        return context
    except Exception as e:
        logger.error(f"Error querying vector database: {e}")
        return "Error retrieving context from database."


# --- Conversation Tracker ---
class ConversationTracker:
    def __init__(self):
        self.conversations = defaultdict(list)

    def add_message(self, session_id, role, content):
        self.conversations[session_id].append({"role": role, "content": content})

    def get_conversation(self, session_id):
        return self.conversations[session_id]


conversation_tracker = ConversationTracker()


# --- Helper: Fetch Model Info ---
def fetch_model_info():
    model_info = {"name": OLLAMA_MODEL, "base": "Unknown", "size": ""}
    try:
        response = requests.post(f"{OLLAMA_HOST}/api/show", json={"name": OLLAMA_MODEL})
        if response.status_code == 200:
            data = response.json()
            details = data.get("details", {})
            model_info["base"] = details.get("parent_model") or details.get(
                "family", "Unknown"
            )
            if "parameter_size" in details:
                model_info["size"] = details["parameter_size"]
            elif "model_info" in data:
                info = data["model_info"]
                model_info["base"] = info.get("general.basename", model_info["base"])
                try:
                    count = int(info.get("general.parameter_count", 0))
                    model_info["size"] = f"{count / 1_000_000_000:.1f}B"
                except Exception:
                    pass
            elif "modelfile" in data:
                for line in data["modelfile"].split("\n"):
                    if line.startswith("FROM "):
                        from_value = line.replace("FROM ", "").strip()
                        if not any(x in from_value for x in ("sha256", "\\", "/")):
                            model_info["base"] = from_value
                            break
        if model_info["size"] and model_info["base"] != "Unknown":
            model_info["base"] = f"{model_info['base']} ({model_info['size']})"
    except Exception as e:
        logger.error(f"Error getting model information: {e}")
    return model_info


# --- Web Routes ---
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/index_docs", methods=["POST"])
def index_endpoint():
    try:
        specific_files = (
            request.get_json(silent=True, force=True).get("files")
            if request.is_json
            else None
        )
        result = index_documents(specific_files=specific_files)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in index_docs endpoint: {e}")
        return jsonify(
            {
                "status": "error",
                "error": str(e),
                "indexed": 0,
                "updated": 0,
                "skipped": 0,
            }
        )


@app.route("/document_status", methods=["GET"])
def document_status_endpoint():
    try:
        status = get_document_status(DOCS_DIR, collection, CHROMA_AVAILABLE)
        status["counts"] = {
            "indexed": len(status["indexed"]),
            "unindexed": len(status["unindexed"]),
            "modified": len(status["modified"]),
            "total": len(status["indexed"])
            + len(status["unindexed"])
            + len(status["modified"]),
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error in document_status endpoint: {e}")
        return jsonify(
            {
                "error": str(e),
                "indexed": [],
                "unindexed": [],
                "modified": [],
                "counts": {"indexed": 0, "unindexed": 0, "modified": 0, "total": 0},
                "needs_indexing": False,
            }
        )


@app.route("/status", methods=["GET"])
def status_endpoint():
    doc_status = get_document_status(DOCS_DIR, collection, CHROMA_AVAILABLE)
    model_info = fetch_model_info()
    return jsonify(
        {
            "chroma_available": CHROMA_AVAILABLE,
            "ollama_host": OLLAMA_HOST,
            "ollama_model": OLLAMA_MODEL,
            "model_base": model_info["base"],
            "indexed_docs": len(doc_status["indexed"]),
            "doc_files": [os.path.basename(p) for p in doc_status["indexed"]],
        }
    )


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True, force=True)
        message = data.get("message", "")
        session_id = data.get("session_id", "default")
        conversation_tracker.add_message(session_id, "user", message)
        context = query_vector_db(message)
        history = conversation_tracker.get_conversation(session_id)
        history_prompt = "\nConversation history:\n" + "\n".join(
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in history
        )
        if context.strip() and len(context.strip()) > 10:
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
        try:
            response = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7},
                },
                timeout=60,
            )
            if response.status_code != 200:
                return jsonify(
                    {
                        "response": f"Error from Ollama API: {response.text}",
                        "context_used": bool(context),
                        "sources": [],
                    }
                )
            result = response.json()
            assistant_response = result.get("response", "")
        except Exception as e:
            assistant_response = f"Error running Ollama: {str(e)}"
        conversation_tracker.add_message(session_id, "assistant", assistant_response)
        sources = []
        if CHROMA_AVAILABLE and collection is not None:
            try:
                results = collection.query(query_texts=[message])
                if results.get("metadatas") and results["metadatas"][0]:
                    sources = [
                        os.path.basename(m["source"]) for m in results["metadatas"][0]
                    ]
            except Exception as e:
                logger.error(f"Error getting sources: {e}")
        return jsonify(
            {
                "response": assistant_response,
                "context_used": bool(context),
                "sources": sources,
            }
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify(
            {
                "response": f"An error occurred: {str(e)}",
                "context_used": False,
                "sources": [],
            }
        )


if __name__ == "__main__":
    os.makedirs(DOCS_DIR, exist_ok=True)
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags")
        if response.status_code == 200:
            logger.info(f"Successfully connected to Ollama at {OLLAMA_HOST}")
        else:
            logger.warning(
                f"Warning: Ollama responded with status code {response.status_code}"
            )
    except Exception as e:
        logger.warning(f"WARNING: Could not connect to Ollama at {OLLAMA_HOST}: {e}")
    app.run(debug=True, host="0.0.0.0", port=5000)
