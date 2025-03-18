import os
import logging
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv
import time
import threading

# Import modules
from modules.chromadb_handler import init_db
from modules.document_manager import get_document_status, index_documents, query_vector_db
from modules.conversation import ConversationTracker
from modules.ollama_client import fetch_model_info, generate_response
import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Load environment variables
load_dotenv()

# Initialize database at application start
db_client, collection = init_db()

# Initialize conversation tracker
conversation_tracker = ConversationTracker()

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
        result = index_documents(collection, specific_files=specific_files)
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
        status = get_document_status(config.DOCS_DIR, collection, config.CHROMA_AVAILABLE)
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
    doc_status = get_document_status(config.DOCS_DIR, collection, config.CHROMA_AVAILABLE)
    model_info = fetch_model_info()
    return jsonify(
        {
            "chroma_available": config.CHROMA_AVAILABLE,
            "ollama_host": config.OLLAMA_HOST,
            "ollama_model": config.OLLAMA_MODEL,
            "model_base": model_info["base"],
            "indexed_docs": len(doc_status["indexed"]),
            "doc_files": [os.path.basename(p) for p in doc_status["indexed"]],
        }
    )


@app.route("/list_docs", methods=["GET"])
def list_docs_endpoint():
    """Return a list of all documents in the docs directory"""
    from modules.document_manager import list_documents
    try:
        doc_files = list_documents()
        return jsonify({"status": "success", "files": doc_files})
    except Exception as e:
        logger.error(f"Error listing docs: {e}")
        return jsonify({"status": "error", "error": str(e), "files": []})


@app.route("/get_doc/<path:file_path>", methods=["GET"])
def get_doc_endpoint(file_path):
    """Return contents of a specific document"""
    from modules.document_manager import get_document_content
    try:
        result = get_document_content(file_path)
        if result.get("status") == "error":
            return jsonify(result), result.get("code", 500)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting document {file_path}: {e}", exc_info=True)
        return jsonify({"status": "error", "error": str(e)}), 500
        
@app.route("/reindex_all", methods=["POST"])
def reindex_all_endpoint():
    """Force reindex of all documents"""
    try:
        result = index_documents(collection, force_reindex=True)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in reindex_all endpoint: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "indexed": 0,
            "updated": 0, 
            "skipped": 0,
        })

@app.route("/save_doc/<path:file_path>", methods=["POST"])
def save_doc_endpoint(file_path):
    """Save updated contents to a document"""
    from modules.document_manager import save_document_content
    try:
        data = request.get_json(silent=True, force=True)
        if not data or "content" not in data:
            return jsonify({"status": "error", "error": "No content provided"}), 400
            
        content = data["content"]
        result = save_document_content(file_path, content)
        
        if result.get("status") == "error":
            return jsonify(result), 400
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error saving document {file_path}: {e}", exc_info=True)
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/doc_viewer")
def doc_viewer():
    """Serve the document viewer page"""
    return render_template("doc_viewer.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True, force=True)
        message = data.get("message", "")
        session_id = data.get("session_id", "default")
        
        # Add user message to conversation history
        conversation_tracker.add_message(session_id, "user", message)
        
        # Get relevant context from vector database
        context = query_vector_db(collection, message)
        
        # Get conversation history
        history = conversation_tracker.get_conversation(session_id)
        
        # Generate response
        assistant_response, success = generate_response(message, context, history)
        
        # Add assistant response to conversation
        conversation_tracker.add_message(session_id, "assistant", assistant_response)
        
        # Get sources for the response
        sources = []
        if config.CHROMA_AVAILABLE and collection is not None:
            try:
                # Specify include parameter to prevent adding new vectors
                results = collection.query(query_texts=[message], include=["metadatas"])
                if results.get("metadatas") and results["metadatas"][0]:
                    sources = [
                        os.path.basename(m["source"]) for m in results["metadatas"][0]
                    ]
            except Exception as e:
                logger.error(f"Error getting sources: {e}")
                
        return jsonify({
            "response": assistant_response,
            "context_used": bool(context),
            "sources": sources,
        })
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({
            "response": f"An error occurred: {str(e)}",
            "context_used": False,
            "sources": [],
        })


if __name__ == "__main__":
    os.makedirs(config.DOCS_DIR, exist_ok=True)
    
    # Check Ollama connection
    from modules.ollama_client import check_ollama_connection
    check_ollama_connection()
    
    # Start the Flask app
    app.run(debug=True, host="0.0.0.0", port=5000)