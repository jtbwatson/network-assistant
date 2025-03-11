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
from dotenv import load_dotenv  # Added for .env file support

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Configuration from environment variables ---
DOCS_DIR = os.getenv("DOCS_DIR", "./network_docs")
DB_DIR = os.getenv("DB_DIR", "./chroma_db")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
SEARCH_RESULTS = int(os.getenv("SEARCH_RESULTS", "5"))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "network-assistant")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

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


def index_documents(docs_dir=DOCS_DIR, force_reindex=False):
    """
    Index all documentation files into the vector database

    Parameters:
    - docs_dir: Directory containing documents to index
    - force_reindex: If True, reindex all documents even if previously indexed
    """
    if not CHROMA_AVAILABLE or collection is None:
        return {"error": "ChromaDB not available", "indexed": 0}

    files_indexed = 0
    files_updated = 0
    os.makedirs(docs_dir, exist_ok=True)

    # Get list of all files
    for file_path in glob.glob(f"{docs_dir}/**/*.*", recursive=True):
        file_path = os.path.normpath(file_path)

        # Skip files that are not supported
        if not file_path.endswith((".txt", ".md", ".yaml", ".yml")):
            continue

        file_id = hashlib.md5(file_path.encode()).hexdigest()

        # Get file modification time
        try:
            mtime = os.path.getmtime(file_path)
        except OSError:
            mtime = 0

        # Check if file is already indexed and get its metadata
        indexed_mtime = None
        try:
            existing = collection.get(ids=[file_id + "_0"])
            if existing and existing["ids"] and not force_reindex:
                # Try to get the modification time from metadata
                if existing.get("metadatas") and existing["metadatas"][0]:
                    indexed_mtime = existing["metadatas"][0].get("mtime")

                # If file hasn't been modified since indexing, skip it
                if indexed_mtime is not None and float(indexed_mtime) >= mtime:
                    continue
                else:
                    # File has been modified, delete old entries to reindex
                    try:
                        # Find all chunks with this file_id prefix
                        all_ids = collection.get(where={"source": file_path})
                        if all_ids and all_ids["ids"]:
                            collection.delete(ids=all_ids["ids"])
                    except Exception as e:
                        print(f"Error removing old chunks for {file_path}: {e}")
        except Exception:
            # Not found or error, continue to index
            pass

        try:
            # Process file based on extension
            if file_path.endswith((".txt", ".md")):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Split into smaller chunks with overlap
                chunks = split_into_chunks(content)

                # Add chunks to collection with modification time
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{file_id}_{i}"
                    try:
                        collection.add(
                            ids=[chunk_id],
                            documents=[chunk],
                            metadatas=[
                                {"source": file_path, "chunk": i, "mtime": str(mtime)}
                            ],
                        )
                    except Exception as e:
                        print(f"Error adding chunk {i} from {file_path}: {e}")
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
                                {
                                    "source": file_path,
                                    "type": "config",
                                    "mtime": str(mtime),
                                }
                            ],
                        )
                    except Exception as e:
                        print(f"Error processing YAML file {file_path}: {e}")
                        continue

            if indexed_mtime is not None:
                files_updated += 1
            else:
                files_indexed += 1

        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            continue

    return {"status": "success", "indexed": files_indexed, "updated": files_updated}


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


# Track conversation state
class ConversationState:
    def __init__(self):
        self.conversations = {}  # session_id -> conversation data

    def get_or_create(self, session_id):
        if session_id not in self.conversations:
            self.conversations[session_id] = {
                "history": [],
                "gathering_info": False,
                "problem_type": None,
                "gathered_details": {},
                "required_details": {},
            }
        return self.conversations[session_id]


# Initialize state manager
conversation_state = ConversationState()

# Default questions as fallback
DEFAULT_QUESTIONS = {
    "connectivity": {
        "device_type": "What type of device are you troubleshooting? (e.g., router, switch, server)",
        "ip_address": "What is the IP address of the device?",
        "connection_type": "Is this a wired or wireless connection?",
        "error_message": "Are there any specific error messages you're seeing?",
    },
    "performance": {
        "affected_services": "Which services are experiencing performance issues?",
        "when_started": "When did the performance issues begin?",
        "load_changes": "Has there been any change in network load recently?",
        "monitoring_data": "Do you have any monitoring data showing the issue?",
    },
    "security": {
        "alert_type": "What type of security alert or concern are you seeing?",
        "affected_systems": "Which systems are affected?",
        "observed_behavior": "What unusual behavior have you observed?",
        "recent_changes": "Were there any recent changes to your security configuration?",
    },
    "configuration": {
        "device_info": "What device are you trying to configure?",
        "current_config": "What is the current configuration?",
        "desired_config": "What configuration change are you trying to make?",
        "previous_attempts": "What have you tried so far?",
    },
    "hardware": {
        "device_model": "What is the make and model of the device?",
        "symptoms": "What symptoms is the device showing?",
        "age": "How old is the device?",
        "environment": "Are there any environmental factors (heat, moisture, etc.)?",
    },
    "software": {
        "application": "Which application or service is having issues?",
        "version": "What version of the software are you running?",
        "recent_changes": "Were there any recent updates or changes?",
        "error_logs": "Are there any relevant logs or error messages?",
    },
}


# --- Web Routes ---
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/index_docs", methods=["POST"])
def index_endpoint():
    try:
        # Check if force reindex is requested
        data = request.json or {}
        force_reindex = data.get("force_reindex", False)

        result = index_documents(force_reindex=force_reindex)

        # Add total count for UI
        if "indexed" in result and "updated" in result:
            result["total"] = result["indexed"] + result["updated"]

        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/determine_questions", methods=["POST"])
def determine_questions():
    """Dynamically determine what questions to ask based on the issue"""
    try:
        data = request.json
        initial_description = data.get("description", "")
        problem_type = data.get("problem_type", "")

        # Build a prompt for the LLM to determine needed information
        prompt = f"""
You are a network troubleshooting assistant. A user has described a {problem_type} issue:
"{initial_description}"

List the specific information you need to troubleshoot this issue effectively. 
Format your response as a JSON object with question IDs as keys and the questions as values.
Only include essential diagnostic questions (maximum 5).

Example format:
{{
  "device_info": "What type of device are you troubleshooting?",
  "connection_type": "Is this a wired or wireless connection?",
  ...
}}
"""

        # Call Ollama to generate the questions
        try:
            response = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2},
                },
                timeout=30,
            )

            if response.status_code != 200:
                return jsonify(
                    {
                        "error": f"Error from Ollama API: {response.text}",
                        "questions": DEFAULT_QUESTIONS.get(problem_type, {}),
                    }
                )

            result = response.json()
            questions_text = result.get("response", "")

            # Extract JSON object from the response
            json_match = re.search(r"({.*})", questions_text, re.DOTALL)
            if json_match:
                questions_json = json_match.group(1)
                try:
                    questions = json.loads(questions_json)
                    return jsonify({"questions": questions})
                except json.JSONDecodeError:
                    # Fallback to default questions if JSON parsing fails
                    return jsonify(
                        {"questions": DEFAULT_QUESTIONS.get(problem_type, {})}
                    )
            else:
                return jsonify({"questions": DEFAULT_QUESTIONS.get(problem_type, {})})

        except Exception as e:
            return jsonify(
                {
                    "error": f"Error determining questions: {str(e)}",
                    "questions": DEFAULT_QUESTIONS.get(problem_type, {}),
                }
            )

    except Exception as e:
        return jsonify(
            {
                "error": f"Error in determine_questions endpoint: {str(e)}",
                "questions": {},
            }
        )


# Helper functions for information gathering system
def detect_problem_type(message):
    """Determine what kind of network issue the user is describing with more detail"""
    # Don't detect problem type for initial greeting or very short messages
    if (
        len(message.strip()) < 15
        or "hello" in message.lower()
        or "hi " in message.lower()
    ):
        return None

    # Use the LLM to classify the problem type and extract key details
    prompt = f"""
Analyze this network issue description: "{message}"
What type of network problem is this? Classify as one of:
- connectivity (connection issues, can't reach resources)
- performance (slowness, latency, bandwidth problems)
- security (breaches, suspicious activity, access issues)
- configuration (setup problems, misconfiguration)
- hardware (physical device failures)
- software (application or service issues)
- other (if it doesn't fit the above categories)
- none (if no specific network problem is described yet)

Respond with only the category name in lowercase.
"""

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2},
            },
            timeout=10,
        )

        if response.status_code == 200:
            result = response.json()
            problem_type = result.get("response", "").strip().lower()

            # Basic validation that we got a valid category
            valid_types = [
                "connectivity",
                "performance",
                "security",
                "configuration",
                "hardware",
                "software",
                "other",
                "none",
            ]

            if problem_type in valid_types:
                # Return None if the model indicates no problem is described yet
                if problem_type == "none":
                    return None
                return problem_type
    except Exception as e:
        print(f"Error classifying problem type: {e}")

    # Fallback to keyword-based detection
    message_lower = message.lower()

    # Skip detection for greetings or short messages
    if "hello" in message_lower or "hi " in message_lower or len(message_lower) < 20:
        return None

    if any(
        word in message_lower for word in ["connect", "reach", "ping", "access", "down"]
    ):
        return "connectivity"
    elif any(
        word in message_lower
        for word in ["slow", "performance", "latency", "bandwidth", "speed"]
    ):
        return "performance"
    elif any(
        word in message_lower
        for word in ["security", "breach", "attack", "vulnerability", "suspicious"]
    ):
        return "security"
    elif any(
        word in message_lower
        for word in ["configure", "setup", "install", "change", "settings"]
    ):
        return "configuration"

    return None  # Don't assume a problem type if we can't detect one


def get_next_question(state):
    """Get the next question to ask based on what information is still needed"""
    if not state["required_details"]:
        return "I have all the information I need. Let me analyze your issue."

    # Get the next detail key and question
    detail_key = next(iter(state["required_details"]))
    question = state["required_details"][detail_key]

    return f"{question}"


def store_detail_from_answer(state, answer):
    """Store the user's answer to the previous question"""
    if not state["required_details"]:
        return

    # Get the key for the detail we just asked about
    detail_key = next(iter(state["required_details"]))

    # Store the answer
    state["gathered_details"][detail_key] = answer

    # Remove this detail from required_details
    state["required_details"].pop(detail_key)


def construct_detailed_query(state):
    """Create a detailed query based on all gathered information"""
    problem_type = state["problem_type"]
    details = state["gathered_details"]

    query = f"Network {problem_type} issue with the following details:\n"
    for key, value in details.items():
        query += f"{key}: {value}\n"

    return query


def construct_informed_prompt(query, context, state):
    """Create a detailed prompt for the LLM with all gathered information"""
    history_prompt = "Conversation history:\n"
    for message in state["history"]:
        role = "User" if message["role"] == "user" else "Assistant"
        history_prompt += f"{role}: {message['content']}\n"

    system_instruction = f"""
You are a network troubleshooting assistant. You've gathered the following information about 
the user's {state['problem_type']} issue:

"""

    for key, value in state["gathered_details"].items():
        system_instruction += f"- {key}: {value}\n"

    if context:
        prompt = f"{system_instruction}\n\nHere is some relevant information from the knowledge base:\n\n{context}\n\n{history_prompt}\n\nBased on all this information, provide troubleshooting steps and a solution to the user's network issue."
    else:
        prompt = f"{system_instruction}\n\n{history_prompt}\n\nBased on this information, provide troubleshooting steps and a solution to the user's network issue."

    return prompt


@app.route("/get_docs_status", methods=["GET"])
def get_docs_status():
    """Get status of available documents and whether they're indexed"""
    try:
        # Create docs directory if it doesn't exist
        os.makedirs(DOCS_DIR, exist_ok=True)

        # Get all files in the docs directory
        all_files = []
        for file_path in glob.glob(f"{DOCS_DIR}/**/*.*", recursive=True):
            file_path = os.path.normpath(file_path)
            if file_path.endswith((".txt", ".md", ".yaml", ".yml")):
                file_id = hashlib.md5(file_path.encode()).hexdigest()

                # Check if file is indexed
                is_indexed = False
                if CHROMA_AVAILABLE and collection is not None:
                    try:
                        existing = collection.get(ids=[file_id + "_0"])
                        if existing and existing["ids"]:
                            is_indexed = True
                    except Exception:
                        pass

                all_files.append(
                    {
                        "path": file_path,
                        "name": os.path.basename(file_path),
                        "indexed": is_indexed,
                    }
                )

        return jsonify(
            {
                "status": "success",
                "files": all_files,
                "chroma_available": CHROMA_AVAILABLE,
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        message = data.get("message", "")
        session_id = data.get("session_id", "default")

        # Get or create conversation state
        state = conversation_state.get_or_create(session_id)
        state["history"].append({"role": "user", "content": message})

        # Check if this is an initial greeting that needs a simple response without information gathering
        message_lower = message.lower()
        if len(state["history"]) <= 1 and (
            message_lower.startswith("hi")
            or message_lower.startswith("hello")
            or message_lower.startswith("hey")
            or len(message_lower) < 10
        ):

            # Respond with a greeting without accessing the knowledge base
            greeting_response = (
                "I'm ready to help. Go ahead and ask your networking question!"
            )
            state["history"].append({"role": "assistant", "content": greeting_response})

            return jsonify(
                {
                    "response": greeting_response,
                    "gathering_info": False,
                    "context_used": False,
                    "sources": [],
                }
            )

        # Check if we need to start information gathering
        if not state["gathering_info"] and not state["problem_type"]:
            # Detect problem type
            problem_type = detect_problem_type(message)

            if problem_type and problem_type != "other":
                # Dynamically determine required questions
                try:
                    # Use the application URL to call our own endpoint
                    server_url = request.host_url.rstrip("/")
                    questions_response = requests.post(
                        f"{server_url}/determine_questions",
                        json={"description": message, "problem_type": problem_type},
                        timeout=30,
                    )

                    if questions_response.status_code == 200:
                        questions_data = questions_response.json()
                        required_details = questions_data.get("questions", {})

                        if required_details:
                            state["gathering_info"] = True
                            state["problem_type"] = problem_type
                            state["required_details"] = required_details

                            # Ask the first question
                            next_question = get_next_question(state)
                            state["history"].append(
                                {"role": "assistant", "content": next_question}
                            )

                            return jsonify(
                                {
                                    "response": next_question,
                                    "gathering_info": True,
                                    "context_used": False,
                                    "sources": [],
                                }
                            )
                    else:
                        # If dynamic question generation fails, fall back to default questions
                        if problem_type in DEFAULT_QUESTIONS:
                            state["gathering_info"] = True
                            state["problem_type"] = problem_type
                            state["required_details"] = DEFAULT_QUESTIONS[
                                problem_type
                            ].copy()

                            # Ask the first question
                            next_question = get_next_question(state)
                            state["history"].append(
                                {"role": "assistant", "content": next_question}
                            )

                            return jsonify(
                                {
                                    "response": next_question,
                                    "gathering_info": True,
                                    "context_used": False,
                                    "sources": [],
                                }
                            )

                except Exception as e:
                    print(f"Error getting dynamic questions: {e}")
                    # Try fallback to static questions
                    if problem_type in DEFAULT_QUESTIONS:
                        state["gathering_info"] = True
                        state["problem_type"] = problem_type
                        state["required_details"] = DEFAULT_QUESTIONS[
                            problem_type
                        ].copy()

                        # Ask the first question
                        next_question = get_next_question(state)
                        state["history"].append(
                            {"role": "assistant", "content": next_question}
                        )

                        return jsonify(
                            {
                                "response": next_question,
                                "gathering_info": True,
                                "context_used": False,
                                "sources": [],
                            }
                        )

        # Continue information gathering if in progress
        if state["gathering_info"]:
            # Store the answer to the previous question
            store_detail_from_answer(state, message)

            # Check if we need more information
            if state["required_details"]:
                # Ask the next question
                next_question = get_next_question(state)
                state["history"].append({"role": "assistant", "content": next_question})

                return jsonify(
                    {
                        "response": next_question,
                        "gathering_info": True,
                        "context_used": False,
                        "sources": [],
                    }
                )
            else:
                # We have all required information, proceed with troubleshooting
                state["gathering_info"] = False

                # Construct a detailed query based on gathered information
                detailed_query = construct_detailed_query(state)

                # The rest proceeds as in the original chat function...
                context = query_vector_db(detailed_query)

                if context and len(context.strip()) > 10:
                    prompt = construct_informed_prompt(detailed_query, context, state)
                else:
                    prompt = construct_informed_prompt(detailed_query, None, state)

                # Call Ollama with the detailed prompt
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
                                "gathering_info": False,
                                "context_used": bool(context),
                                "sources": [],
                            }
                        )

                    result = response.json()
                    assistant_response = result.get("response", "")

                except Exception as e:
                    assistant_response = f"Error running Ollama: {str(e)}"

                # Get sources
                sources = []
                if CHROMA_AVAILABLE and collection is not None:
                    try:
                        results = collection.query(query_texts=[detailed_query])
                        if results.get("metadatas") and results["metadatas"][0]:
                            sources = [
                                os.path.basename(m["source"])
                                for m in results["metadatas"][0]
                            ]
                    except Exception as e:
                        print(f"Error getting sources: {e}")

                state["history"].append(
                    {"role": "assistant", "content": assistant_response}
                )

                return jsonify(
                    {
                        "response": assistant_response,
                        "gathering_info": False,
                        "context_used": bool(context),
                        "sources": sources,
                    }
                )

        # If not gathering info, handle as general query
        # Add instruction to prevent making assumptions
        prompt_prefix = """
You are a network troubleshooting assistant. The user is asking a question:

"""
        # Only access the knowledge base if the question is substantial enough
        if len(message.strip()) >= 15 and not any(
            greeting in message.lower() for greeting in ["hello", "hi ", "hey"]
        ):
            context = query_vector_db(message)
        else:
            context = ""

        if context and len(context.strip()) > 10:
            prompt = f"{prompt_prefix}\n{message}\n\nHere is some relevant information from the knowledge base:\n\n{context}\n\nProvide a helpful response but do NOT make assumptions about their network unless explicitly stated in their question. Do not refer to wireless issues unless the user has specifically mentioned wireless networks."
        else:
            prompt = f"{prompt_prefix}\n{message}\n\nRespond helpfully without making assumptions about their network. Keep the response general unless the user has provided specific details."

        # Call the Ollama API
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
                        "gathering_info": False,
                        "context_used": bool(context),
                        "sources": [],
                    }
                )

            result = response.json()
            assistant_response = result.get("response", "")

        except Exception as e:
            assistant_response = f"Error running Ollama: {str(e)}"

        # Get sources
        sources = []
        if context and CHROMA_AVAILABLE and collection is not None:
            try:
                results = collection.query(query_texts=[message])
                if results.get("metadatas") and results["metadatas"][0]:
                    sources = [
                        os.path.basename(m["source"]) for m in results["metadatas"][0]
                    ]
            except Exception as e:
                print(f"Error getting sources: {e}")

        state["history"].append({"role": "assistant", "content": assistant_response})

        return jsonify(
            {
                "response": assistant_response,
                "gathering_info": False,
                "context_used": bool(context),
                "sources": sources,
            }
        )

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify(
            {
                "response": f"An error occurred: {str(e)}",
                "gathering_info": False,
                "context_used": False,
                "sources": [],
            }
        )


if __name__ == "__main__":
    # Make sure the docs directory exists
    os.makedirs(DOCS_DIR, exist_ok=True)

    # Print current configuration
    print("=== Network Troubleshooting Assistant Configuration ===")
    print(f"DOCS_DIR: {DOCS_DIR}")
    print(f"DB_DIR: {DB_DIR}")
    print(f"OLLAMA_HOST: {OLLAMA_HOST}")
    print(f"OLLAMA_MODEL: {OLLAMA_MODEL}")
    print(f"CHUNK_SIZE: {CHUNK_SIZE}")
    print(f"CHUNK_OVERLAP: {CHUNK_OVERLAP}")
    print(f"SEARCH_RESULTS: {SEARCH_RESULTS}")
    print(f"DEBUG_MODE: {DEBUG_MODE}")
    print("====================================================")

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
    app.run(debug=DEBUG_MODE, host="0.0.0.0", port=int(os.getenv("PORT", "5000")))