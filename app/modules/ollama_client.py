import logging
import time
import config
import ollama

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
            # Set Ollama host
            ollama.host = config.OLLAMA_HOST
            
            # Get model details - adding error handling in case model doesn't exist
            try:
                response = ollama.show(config.OLLAMA_MODEL)
                logger.debug(f"Ollama show response type: {type(response)}")
            except Exception as e:
                if "not found" in str(e).lower():
                    logger.error(f"🔴 Model '{config.OLLAMA_MODEL}' not found in Ollama")
                    return model_info  # Return early with default info
                else:
                    # Re-raise other exceptions to be caught by outer try/except
                    raise
            
            if response:
                # Try to access details as an attribute first (for typed objects)
                if hasattr(response, 'details'):
                    details = response.details
                    modelfile = getattr(response, 'modelfile', '')
                    model_info_attr = getattr(response, 'model_info', {})
                else:
                    # Fall back to dictionary access (for older versions)
                    details = response.get("details", {})
                    modelfile = response.get("modelfile", "")
                    model_info_attr = response.get("model_info", {})

                # Ensure details is a dict-like object
                if details:
                    # Try to extract the base model name
                    if hasattr(details, 'parent_model'):
                        parent = getattr(details, 'parent_model')
                        if parent:
                            model_info["base"] = parent
                    elif hasattr(details, 'family'):
                        family = getattr(details, 'family')
                        if family:
                            model_info["base"] = family
                    elif isinstance(details, dict):
                        # Fall back to dictionary access
                        model_info["base"] = details.get("parent_model") or details.get("family", "Unknown")
                    
                    # Try to extract the model size
                    if hasattr(details, 'parameter_size'):
                        model_info["size"] = getattr(details, 'parameter_size')
                    elif isinstance(details, dict) and "parameter_size" in details:
                        model_info["size"] = details["parameter_size"]
                
                # Try to extract info from model_info
                if model_info_attr:
                    if hasattr(model_info_attr, 'general.basename'):
                        model_info["base"] = getattr(model_info_attr, 'general.basename')
                    elif isinstance(model_info_attr, dict):
                        model_info["base"] = model_info_attr.get("general.basename", model_info["base"])
                        
                    try:
                        if hasattr(model_info_attr, 'general.parameter_count'):
                            count = int(getattr(model_info_attr, 'general.parameter_count', 0))
                            model_info["size"] = f"{count / 1_000_000_000:.1f}B"
                        elif isinstance(model_info_attr, dict):
                            count = int(model_info_attr.get("general.parameter_count", 0))
                            model_info["size"] = f"{count / 1_000_000_000:.1f}B"
                    except Exception:
                        pass
                
                # Try to extract info from modelfile
                if modelfile and (isinstance(modelfile, str) or hasattr(modelfile, 'split')):
                    # Handle both string and string-like objects
                    model_lines = modelfile.split("\n") if hasattr(modelfile, 'split') else str(modelfile).split("\n")
                    for line in model_lines:
                        if line.startswith("FROM "):
                            from_value = line.replace("FROM ", "").strip()
                            if not any(x in from_value for x in ("sha256", "\\", "/")):
                                model_info["base"] = from_value
                                break
                                
                # Format the base model info to include size if available
                if model_info["size"] and model_info["base"] != "Unknown":
                    model_info["base"] = f"{model_info['base']} ({model_info['size']})"
                
                logger.info(f"🟢 Model info retrieved for {model_info['name']}: {model_info['base']}")
                return model_info
                
        except Exception as e:
            logger.warning(f"🟡 Attempt {attempt+1}/{MAX_RETRIES}: Error getting model info: {e}")
        
        # Only sleep if we're going to retry
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)
        
    logger.error(f"🔴 Failed to get model information after {MAX_RETRIES} attempts")
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
            logger.info(f"🟡 Generating response, attempt {attempt+1}/{MAX_RETRIES}")
            
            # Set Ollama host
            ollama.host = config.OLLAMA_HOST
            
            response = ollama.generate(
                model=config.OLLAMA_MODEL,
                prompt=prompt,
                options={
                    "temperature": 0.7,
                    "num_predict": 2048,  # Maximum response length
                }
            )
            
            if response:
                # Try attribute access first (for typed objects)
                if hasattr(response, 'response'):
                    assistant_response = response.response
                else:
                    # Fall back to dictionary access
                    assistant_response = response.get("response", "")
                
                if not assistant_response:
                    logger.warning("🟡 Empty response received from Ollama")
                    
                logger.info(f"🟢 Response generated successfully ({len(assistant_response)} chars)")
                return assistant_response, True
                
        except Exception as e:
            logger.warning(f"🟡 Attempt {attempt+1}/{MAX_RETRIES}: Request error: {e}")
        
        # Only sleep if we're going to retry
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)
    
    error_message = f"Failed to generate response after {MAX_RETRIES} attempts"
    logger.error(f"🔴 {error_message}")
    return error_message, False


def check_ollama_connection():
    """
    Check if Ollama is available at the configured host.
    Logs warnings if not available.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    logger.info(f"🟡 Checking Ollama connection at {config.OLLAMA_HOST}")
    
    for attempt in range(MAX_RETRIES):
        try:
            # Set Ollama host
            ollama.host = config.OLLAMA_HOST
            
            # Get list of models
            list_response = ollama.list()
            logger.info(f"🟢 Successfully connected to Ollama at {config.OLLAMA_HOST}")
            
            # Handle the ListResponse object - we need to access its 'models' attribute
            if hasattr(list_response, 'models'):
                models = list_response.models
                
                if models:
                    # Extract model names
                    model_names = []
                    for model in models:
                        # Try different possible attributes
                        if hasattr(model, 'name'):
                            model_names.append(model.name)
                        elif hasattr(model, 'model'):
                            model_names.append(model.model)
                        # Add any other fields you might need
                    
                    # Log available models
                    if model_names:
                        logger.info(f"🟢 Available models: {', '.join(model_names)}")
                        
                        # Case-insensitive check for our model - strip version tags for comparison
                        config_model_lower = config.OLLAMA_MODEL.lower()
                        model_found = False
                        
                        for name in model_names:
                            # Strip version tag if present (e.g., ":latest")
                            base_name = name.split(':')[0].lower()
                            
                            if base_name == config_model_lower:
                                model_found = True
                                break
                        
                        if not model_found:
                            logger.warning(f"🟡 Configured model '{config.OLLAMA_MODEL}' not found in available models. Make sure it's downloaded.")
                    else:
                        logger.info("🟡 No model names found in response")
                else:
                    logger.info("🟡 No models returned from Ollama")
            else:
                # Try to access as dictionary or list
                try:
                    # For backwards compatibility with older versions
                    if isinstance(list_response, dict) and 'models' in list_response:
                        models = list_response['models']
                        model_names = [m.get('name', '') for m in models if isinstance(m, dict)]
                        logger.info(f"🟢 Available models: {', '.join(filter(None, model_names))}")
                    elif isinstance(list_response, list):
                        models = list_response
                        model_names = [m.get('name', '') for m in models if isinstance(m, dict)]
                        logger.info(f"🟢 Available models: {', '.join(filter(None, model_names))}")
                    else:
                        # Last resort - try to convert to a string representation for logging
                        try:
                            list_str = str(list_response)
                            logger.debug(f"Response raw string: {list_str[:200]}...")  # Truncate for log readability
                        except:
                            pass
                        logger.warning(f"🟡 Unexpected response format from ollama.list() - trying to continue")
                except Exception as e:
                    logger.warning(f"🟡 Error parsing response: {e}")
                
            return True
                
        except Exception as e:
            logger.warning(f"🟡 Attempt {attempt+1}/{MAX_RETRIES}: Could not connect to Ollama: {e}")
        
        # Only sleep if we're going to retry
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)
    
    logger.error(f"🔴 Could not connect to Ollama at {config.OLLAMA_HOST} after {MAX_RETRIES} attempts")
    return False