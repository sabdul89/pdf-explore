import uuid

def new_id() -> str:
    """
    Generate a new UUID4 hex string.
    """
    return uuid.uuid4().hex


def is_valid_uuid(value: str) -> bool:
    """
    Checks if a string is a valid UUID hex.
    """
    try:
        uuid.UUID(hex=value)
        return True
    except Exception:
        return False
