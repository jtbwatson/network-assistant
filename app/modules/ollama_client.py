import requests
import logging
import time
import config

logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 2

def fetch_model_info():
    """
    Fetch information about the currently configured Ollama model.
    
    Returns:
        dict: Information about the model (name, base, size)
    """
    model_info = {"name": config.OLLAMA_MODEL, "base": "Unknown", "size": ""}
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                f"{config.OLLAMA_HOST}/api/show", 
                json={"name": config.OLLAMA_MODEL},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                details = data.get("details", {})
                
                # Try to extract the base model name
                model_info["base"] = details.get("parent_model") or details.get(
                    "family", "Unknown"
                )
                
                # Try to extract the model size
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
                                
                # Format the base model info to include size if available
                if model_info["size"] and model_info["base"] != "Unknown":
                    model_info["base"] = f"{model_info['base']} ({model_info['size']})"
                
                return model_info
            
            elif response.status_code == 404:
                logger.error(f"Model '{config.OLLAMA_MODEL}' not found in Ollama")
                break  # Don't retry if model not found
            
            else:
                logger.warning(f"Attempt {attempt+1}/{MAX_RETRIES}: HTTP {response.status_code} from Ollama API")
                
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt+1}/{MAX_RETRIES}: Connection error: {e}")
        
        # Only sleep if we're going to retry
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)
        
    logger.error(f"Failed to get model information after {MAX_RETRIES} attempts")
    return model_info


def generate_response(message, context, history):
    """
    Generate a response from the Ollama API.
    
    Args:
        message (str): The user message
        context (str): Relevant context from the vector database
        history (list): Conversation history
        
    Returns:
        tuple: (response_text, success_flag)
    """
    # Format the history for inclusion in the prompt
    history_prompt = "\nConversation history:\n" + "\n".join(
        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
        for msg in history[:-1]  # Exclude the latest message which we'll include separately
    )
    
    # Build the prompt based on whether we have context
    if context and context.strip() and len(context.strip()) > 10:
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
    
    # Call the Ollama API with retries
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Generating response, attempt {attempt+1}/{MAX_RETRIES}")
            
            response = requests.post(
                f"{config.OLLAMA_HOST}/api/generate",
                json={
                    "model": config.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 2048,  # Maximum response length
                    },
                },
                timeout=60,  # Increased timeout for longer responses
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_response = result.get("response", "")
                return assistant_response, True
                
            elif response.status_code == 404:
                error_message = f"Model '{config.OLLAMA_MODEL}' not found"
                logger.error(error_message)
                return error_message, False
                
            else:
                logger.warning(f"Attempt {attempt+1}/{MAX_RETRIES}: HTTP {response.status_code} from Ollama API")
                
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt+1}/{MAX_RETRIES}: Request error: {e}")
        
        # Only sleep if we're going to retry
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)
    
    error_message = f"Failed to generate response after {MAX_RETRIES} attempts"
    logger.error(error_message)
    return error_message, False


def check_ollama_connection():
    """
    Check if Ollama is available at the configured host.
    Logs warnings if not available.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    logger.info(f"Checking Ollama connection at {config.OLLAMA_HOST}")
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                f"{config.OLLAMA_HOST}/api/tags",
                timeout=5
            )
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                logger.info(f"Successfully connected to Ollama at {config.OLLAMA_HOST}")
                logger.info(f"Available models: {', '.join([m['name'] for m in models]) if models else 'None'}")
                
                # Check if our configured model is available
                model_names = [m["name"] for m in models]
                if config.OLLAMA_MODEL not in model_names:
                    logger.warning(f"WARNING: Configured model '{config.OLLAMA_MODEL}' not found in available models")
                
                return True
            else:
                logger.warning(
                    f"Attempt {attempt+1}/{MAX_RETRIES}: Ollama responded with status code {response.status_code}"
                )
        except Exception as e:
            logger.warning(f"Attempt {attempt+1}/{MAX_RETRIES}: Could not connect to Ollama: {e}")
        
        # Only sleep if we're going to retry
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)
    
    logger.error(f"Could not connect to Ollama at {config.OLLAMA_HOST} after {MAX_RETRIES} attempts")
    return False