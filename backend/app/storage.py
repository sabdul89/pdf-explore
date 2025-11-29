from app.supabase_client import supabase
from app.config import SUPABASE_BUCKET

def upload_to_bucket(path: str, data: bytes, content_type="application/pdf"):
    res = supabase.storage.from_(SUPABASE_BUCKET).upload(
        path, data, {"content-type": content_type, "upsert": True}
    )
    return res

def get_public_url(path: str) -> str:
    return supabase.storage.from_(SUPABASE_BUCKET).get_public_url(path)
