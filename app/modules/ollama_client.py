import requests
import logging
import config

logger = logging.getLogger(__name__)

def fetch_model_info():
    """
    Fetch information about the currently configured Ollama model.
    
    Returns:
        dict: Information about the model (name, base, size)
    """
    model_info = {"name": config.OLLAMA_MODEL, "base": "Unknown", "size": ""}
    try:
        response = requests.post(
            f"{config.OLLAMA_HOST}/api/show", 
            json={"name": config.OLLAMA_MODEL}
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
            
    except Exception as e:
        logger.error(f"Error getting model information: {e}")
        
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
    
    # Call the Ollama API
    try:
        response = requests.post(
            f"{config.OLLAMA_HOST}/api/generate",
            json={
                "model": config.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7},
            },
            timeout=60,
        )
        
        if response.status_code != 200:
            error_message = f"Error from Ollama API: {response.text}"
            logger.error(error_message)
            return error_message, False
            
        result = response.json()
        assistant_response = result.get("response", "")
        return assistant_response, True
        
    except Exception as e:
        error_message = f"Error running Ollama: {str(e)}"
        logger.error(error_message)
        return error_message, False


def check_ollama_connection():
    """
    Check if Ollama is available at the configured host.
    Logs warnings if not available.
    """
    try:
        response = requests.get(f"{config.OLLAMA_HOST}/api/tags")
        if response.status_code == 200:
            logger.info(f"Successfully connected to Ollama at {config.OLLAMA_HOST}")
        else:
            logger.warning(
                f"Warning: Ollama responded with status code {response.status_code}"
            )
    except Exception as e:
        logger.warning(f"WARNING: Could not connect to Ollama at {config.OLLAMA_HOST}: {e}")