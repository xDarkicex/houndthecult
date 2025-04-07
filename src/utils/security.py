import hashlib

def hash_user_id(user_id: str) -> str:
    """
    One-way hash user IDs for privacy (SHA-256).
    
    Args:
        user_id (str): The user ID to be hashed.
    
    Returns:
        str: The hashed user ID as a hexadecimal string.
    """
    return hashlib.sha256(user_id.encode()).hexdigest()
