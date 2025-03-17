import re
import config

def split_into_chunks(text, chunk_size=config.CHUNK_SIZE, overlap=config.CHUNK_OVERLAP):
    """
    Split text into overlapping chunks.
    
    Args:
        text (str): The text to split
        chunk_size (int): Maximum size of each chunk
        overlap (int): Number of words to overlap between chunks
        
    Returns:
        list: List of text chunks
    """
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


def escape_html(unsafe):
    """
    Escape HTML special characters in a string.
    
    Args:
        unsafe (str): String that may contain HTML special characters
        
    Returns:
        str: Escaped string safe for HTML inclusion
    """
    return unsafe \
        .replace("&", "&amp;") \
        .replace("<", "&lt;") \
        .replace(">", "&gt;") \
        .replace('"', "&quot;") \
        .replace("'", "&#039;")