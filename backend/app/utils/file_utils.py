import os
import uuid

def save_temp_file(bytes_data: bytes, suffix=".pdf") -> str:
    """
    Saves bytes to a temporary file in /tmp and returns the path.
    Useful for libraries that require filesystem input.
    """
    file_id = uuid.uuid4().hex
    path = f"/tmp/{file_id}{suffix}"

    with open(path, "wb") as f:
        f.write(bytes_data)

    return path


def load_file(path: str) -> bytes:
    """
    Reads a file from disk and returns bytes.
    """
    with open(path, "rb") as f:
        return f.read()


def delete_file(path: str):
    """
    Deletes a temporary file if it exists.
    """
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
