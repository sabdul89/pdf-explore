from fastapi import APIRouter, UploadFile
from app.storage import upload_to_bucket
from app.supabase_client import supabase

router = APIRouter()

@router.post("/")
async def upload(file: UploadFile):
    file_bytes = await file.read()

    record = supabase.table("files").insert({
        "original_name": file.filename
    }).execute()

    file_id = record.data[0]["file_id"]
    path = f"original/{file_id}.pdf"

    upload_to_bucket(path, file_bytes)

    return {"file_id": file_id, "path": path}
