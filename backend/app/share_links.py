import uuid
from datetime import datetime, timedelta
from app.supabase_client import supabase
from app.config import SHARE_TOKEN_TTL_HOURS

def create_share_token(file_id: str):
    token = uuid.uuid4().hex
    expires = datetime.utcnow() + timedelta(hours=SHARE_TOKEN_TTL_HOURS)

    supabase.table("shares").insert({
        "token": token,
        "file_id": file_id,
        "expires_at": expires.isoformat()
    }).execute()

    return token
