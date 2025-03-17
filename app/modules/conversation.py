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
        
    def format_history_for_prompt(self, session_id):
        """
        Format conversation history for inclusion in a prompt.
        
        Args:
            session_id (str): Unique identifier for the conversation
            
        Returns:
            str: Formatted conversation history
        """
        history = self.get_conversation(session_id)
        return "\nConversation history:\n" + "\n".join(
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in history
        )
        
    def clear_conversation(self, session_id):
        """
        Clear the conversation history for a session.
        
        Args:
            session_id (str): Unique identifier for the conversation
        """
        if session_id in self.conversations:
            del self.conversations[session_id]