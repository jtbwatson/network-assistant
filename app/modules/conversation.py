from collections import defaultdict

class ConversationTracker:
    """
    Tracks conversation history between users and the assistant.
    Each conversation is identified by a unique session_id.
    """
    def __init__(self):
        self.conversations = defaultdict(list)

    def add_message(self, session_id, role, content):
        """
        Add a message to the conversation history.
        
        Args:
            session_id (str): Unique identifier for the conversation
            role (str): Either 'user' or 'assistant'
            content (str): The message content
        """
        self.conversations[session_id].append({"role": role, "content": content})

    def get_conversation(self, session_id):
        """
        Get the full conversation history for a session.
        
        Args:
            session_id (str): Unique identifier for the conversation
            
        Returns:
            list: List of message dictionaries with 'role' and 'content' keys
        """
        return self.conversations[session_id]