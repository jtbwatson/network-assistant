import os
import json
import yaml
import re
import hashlib
import logging
from datetime import datetime
import config
from modules.utils import split_into_chunks

logger = logging.getLogger(__name__)

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


def index_documents(collection, docs_dir=config.DOCS_DIR, specific_files=None):
    """
    Index documentation files into the vector database.
    Returns status and counts for indexing, updating, and skipped files.
    """
    if not config.CHROMA_AVAILABLE or collection is None:
        return {
            "status": "error",
            "error": "ChromaDB not available",
            "indexed": 0,
            "updated": 0,
            "skipped": 0,
        }

    files_indexed, files_updated, files_skipped = 0, 0, 0
    os.makedirs(docs_dir, exist_ok=True)
    doc_status = get_document_status(docs_dir, collection, config.CHROMA_AVAILABLE)
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
            
            # Remove existing document chunks if updating
            if is_update:
                try:
                    results = collection.get(where={"source": file_path})
                    if results and results["ids"]:
                        collection.delete(ids=results["ids"])
                except Exception as e:
                    logger.error(f"Error removing old chunks for {file_path}: {e}")
                    
            mtime = str(os.path.getmtime(file_path))
            
            # Handle text and markdown files
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
                        
            # Handle YAML/YML files
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
                
            # Update counters based on whether this was an update or new file
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


def query_vector_db(collection, query, n_results=config.SEARCH_RESULTS):
    """Search the vector database for relevant context"""
    if not config.CHROMA_AVAILABLE or collection is None:
        return "Vector search not available. Using default knowledge."
    try:
        # Set include parameter to fetch all relevant metadata but avoid adding new vectors
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

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


def list_documents():
    """Return a list of all documents in the docs directory"""
    valid_ext = (".txt", ".md", ".yaml", ".yml")
    doc_files = []
    
    for root, _, files in os.walk(config.DOCS_DIR):
        for file in files:
            if not file.startswith(".") and file.endswith(valid_ext):
                rel_path = os.path.relpath(os.path.join(root, file), config.DOCS_DIR)
                file_path = os.path.join(config.DOCS_DIR, rel_path)
                try:
                    mtime = os.path.getmtime(file_path)
                    size = os.path.getsize(file_path)
                    doc_files.append(
                        {
                            "name": file,
                            "path": rel_path,
                            "size": size,
                            "mtime": mtime,
                            "modified": datetime.fromtimestamp(mtime).strftime(
                                "%Y-%m-%d %H:%M"
                            ),
                        }
                    )
                except Exception as e:
                    logger.error(f"Error getting file info for {file_path}: {e}")

    # Sort files by name
    doc_files.sort(key=lambda x: x["name"].lower())
    return doc_files


def get_document_content(file_path):
    """Return contents of a specific document"""
    # Log for debugging
    logger.info(f"Attempting to open document: {file_path}")

    # Handle URL-encoded paths
    file_path = file_path.replace("%20", " ")

    # Ensure file path is within DOCS_DIR by checking for path traversal
    abs_path = os.path.abspath(os.path.join(config.DOCS_DIR, file_path))
    logger.info(f"Absolute path resolved to: {abs_path}")

    if not abs_path.startswith(os.path.abspath(config.DOCS_DIR)):
        logger.warning(f"Path traversal attempt detected: {file_path}")
        return {
            "status": "error",
            "error": "Invalid file path - attempted path traversal",
            "code": 403
        }

    if not os.path.exists(abs_path):
        logger.warning(f"File not found: {abs_path}")
        return {
            "status": "error",
            "error": f"File not found: {file_path}",
            "code": 404
        }

    # Get file contents based on extension
    file_ext = os.path.splitext(abs_path)[1].lower()
    content = ""
    content_type = "text"

    logger.info(f"Reading file with extension: {file_ext}")

    if file_ext in (".txt", ".md"):
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            with open(abs_path, "r", encoding="latin-1") as f:
                content = f.read()
    elif file_ext in (".yaml", ".yml"):
        with open(abs_path, "r", encoding="utf-8") as f:
            try:
                # For YAML files, we have two options:
                # 1. Convert to JSON for editing and convert back when saving (easier editing)
                # 2. Keep as raw YAML (preserves comments and formatting)
                
                # Option 1: Convert to JSON (uncomment if preferred)
                # yaml_content = yaml.safe_load(f)
                # content = json.dumps(yaml_content, indent=2)
                
                # Option 2: Keep as raw YAML (better for syntax highlighting)
                content = f.read()
                content_type = "yaml"
            except Exception as e:
                logger.error(f"Error parsing YAML: {e}")
                return {
                    "status": "error",
                    "error": f"Error parsing YAML: {str(e)}",
                    "code": 400
                }
    else:
        logger.warning(f"Unsupported file type: {file_ext}")
        return {
            "status": "error",
            "error": f"Unsupported file type: {file_ext}",
            "code": 400
        }

    logger.info(f"Successfully read file: {file_path}")
    return {
        "status": "success",
        "content": content,
        "name": os.path.basename(abs_path),
        "type": content_type,
        "path": file_path,
    }


def save_document_content(file_path, content):
    """Save updated content to a document file"""
    # Handle URL-encoded paths
    file_path = file_path.replace("%20", " ")

    # Ensure file path is within DOCS_DIR by checking for path traversal
    abs_path = os.path.abspath(os.path.join(config.DOCS_DIR, file_path))
    logger.info(f"Saving to path: {abs_path}")

    if not abs_path.startswith(os.path.abspath(config.DOCS_DIR)):
        logger.warning(f"Path traversal attempt detected: {file_path}")
        return {
            "status": "error",
            "error": "Invalid file path - attempted path traversal"
        }

    # Verify the file exists (we're only allowing updates, not creating new files)
    if not os.path.exists(abs_path):
        logger.warning(f"File not found: {abs_path}")
        return {
            "status": "error",
            "error": f"File not found: {file_path}"
        }

    # Get file extension
    file_ext = os.path.splitext(abs_path)[1].lower()

    try:
        # Handle different file types
        if file_ext in (".txt", ".md"):
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
        elif file_ext in (".yaml", ".yml"):
            # For YAML files, just write the content directly
            # This preserves the original format, comments, etc.
            try:
                with open(abs_path, "w", encoding="utf-8") as f:
                    f.write(content)
                # Optionally validate the YAML after saving
                try:
                    with open(abs_path, "r", encoding="utf-8") as f:
                        yaml.safe_load(f)  # Just for validation
                except Exception as e:
                    logger.warning(f"Saved YAML may have syntax issues: {e}")
            except Exception as e:
                logger.error(f"Error saving YAML file: {e}")
                return {
                    "status": "error",
                    "error": f"Error saving YAML file: {str(e)}"
                }
        else:
            logger.warning(f"Unsupported file type for saving: {file_ext}")
            return {
                "status": "error",
                "error": f"Unsupported file type for saving: {file_ext}"
            }

        logger.info(f"Successfully saved content to: {file_path}")
        
        # If the file is indexed, mark it as needing reindexing
        # This will add it to the "modified" list in document_status
        # We don't reindex here to keep the save operation fast
        
        return {
            "status": "success",
            "message": "Document saved successfully"
        }
    except Exception as e:
        logger.error(f"Error saving document {file_path}: {e}", exc_info=True)
        return {
            "status": "error",
            "error": f"Error saving document: {str(e)}"
        }