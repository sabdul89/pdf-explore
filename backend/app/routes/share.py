from fastapi import APIRouter, HTTPException
from app.share_links import create_share_token
from app.supabase_client import supabase

router = APIRouter()

@router.post("/create/{file_id}")
def create_link(file_id: str):
    token = create_share_token(file_id)
    return {"share_url": f"/share/get/{token}"}

@router.get("/get/{token}")
def get_shared(token: str):
    record = supabase.table("shares").select("*").eq("token", token).single().execute().data

    if not record:
        raise HTTPException(status_code=404, detail="Link not found or expired")

    file = supabase.table("files").select("*").eq("file_id", record["file_id"]).single().execute().data
    return file
