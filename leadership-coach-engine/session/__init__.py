from llama_index.core.storage.chat_store import SimpleChatStore

# Create a singleton instance of our in-memory store
_chat_store = None

def get_store():
    """
    Get singleton instance of chat store
    
    :return: chat store instance
    """
    global _chat_store
    if _chat_store is None:
        _chat_store = SimpleChatStore()
    return _chat_store
