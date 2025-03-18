import re
import logging
import config

logger = logging.getLogger(__name__)

def split_into_chunks(text, chunk_size=config.CHUNK_SIZE, overlap=config.CHUNK_OVERLAP):
    """
    Split text into overlapping chunks while preserving paragraph boundaries when possible.
    
    Args:
        text (str): The text to split
        chunk_size (int): Maximum size of each chunk
        overlap (int): Number of characters to overlap between chunks
        
    Returns:
        list: List of text chunks
    """
    # Handle empty or very small text
    if not text or len(text) <= chunk_size:
        return [text] if text else []
        
    chunks = []
    # Split text into paragraphs (preserving empty lines)
    paragraphs = re.split(r"(\n\s*\n)", text)
    
    # Recombine paragraph with its separator
    para_texts = []
    for i in range(0, len(paragraphs), 2):
        if i + 1 < len(paragraphs):
            para_texts.append(paragraphs[i] + paragraphs[i+1])
        else:
            para_texts.append(paragraphs[i])
    
    current_chunk = ""
    
    for para in para_texts:
        # If paragraph is too big for a chunk, split it by sentences
        if len(para) > chunk_size:
            logger.debug(f"Paragraph size {len(para)} exceeds chunk size {chunk_size}, splitting by sentences")
            sentences = re.split(r'(?<=[.!?])\s+', para)
            para_chunks = []
            para_chunk = ""
            
            for sentence in sentences:
                # If the sentence itself is too long, we'll need to split it arbitrarily
                if len(sentence) > chunk_size:
                    logger.debug(f"Sentence size {len(sentence)} exceeds chunk size {chunk_size}, splitting by characters")
                    # If we have content in para_chunk, save it first
                    if para_chunk:
                        para_chunks.append(para_chunk)
                        para_chunk = ""
                    
                    # Split the long sentence
                    for i in range(0, len(sentence), chunk_size - overlap):
                        para_chunks.append(sentence[i:i + chunk_size])
                        
                # Otherwise, follow normal logic
                elif len(para_chunk) + len(sentence) <= chunk_size:
                    para_chunk += sentence + " "
                else:
                    para_chunks.append(para_chunk)
                    para_chunk = sentence + " "
            
            # Don't forget the last chunk
            if para_chunk:
                para_chunks.append(para_chunk)
                
            # Now we have chunks for this paragraph, add them to main chunks
            for pc in para_chunks:
                if current_chunk and len(current_chunk) + len(pc) <= chunk_size:
                    current_chunk += pc
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = pc
                    
        # Normal paragraph that fits within chunk size
        elif len(current_chunk) + len(para) <= chunk_size:
            current_chunk += para
        else:
            chunks.append(current_chunk.strip())
            current_chunk = para
    
    # Don't forget the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    # Handle overlap for chunks if needed
    if overlap > 0 and len(chunks) > 1:
        overlapped_chunks = [chunks[0]]
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]
            current_chunk = chunks[i]
            
            # Take the last 'overlap' characters from previous chunk
            overlap_text = prev_chunk[-overlap:] if len(prev_chunk) > overlap else prev_chunk
            
            # Only add overlap if it doesn't make the chunk too big
            if len(overlap_text) + len(current_chunk) <= chunk_size:
                overlapped_chunks.append(overlap_text + current_chunk)
            else:
                overlapped_chunks.append(current_chunk)
                
        chunks = overlapped_chunks
    
    logger.debug(f"Split text into {len(chunks)} chunks")
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


def format_file_size(size_bytes):
    """
    Format file size from bytes to human-readable format.
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        str: Formatted size (e.g., "4.2 KB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def get_file_type_by_extension(filename):
    """
    Determine file type based on extension.
    
    Args:
        filename (str): Filename with extension
        
    Returns:
        str: File type description
    """
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if ext in ['txt']:
        return 'Text'
    elif ext in ['md', 'markdown']:
        return 'Markdown'
    elif ext in ['yml', 'yaml']:
        return 'YAML'
    elif ext in ['json']:
        return 'JSON'
    elif ext in ['py']:
        return 'Python'
    elif ext in ['js']:
        return 'JavaScript'
    elif ext in ['html', 'htm']:
        return 'HTML'
    elif ext in ['css']:
        return 'CSS'
    elif ext in ['sh', 'bash']:
        return 'Shell Script'
    else:
        return 'Unknown'