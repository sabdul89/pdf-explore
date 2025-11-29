import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "pdf-mvp")

SHARE_TOKEN_TTL_HOURS = int(os.getenv("SHARE_TOKEN_TTL_HOURS", 24))
