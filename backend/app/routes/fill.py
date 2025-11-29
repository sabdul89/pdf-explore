from fastapi import APIRouter
import requests

from app.supabase_client import supabase
from app.storage import get_public_url, upload_to_bucket
from app.fill_pdf import fill_pdf
from app.flatten_pdf import flatten_pdf

router = APIRouter()

@router.post("/")
def fill(data: dict):
    file_id = data["file_id"]
    values = data["values"]

    original_url = get_public_url(f"original/{file_id}.pdf")
    pdf_bytes = requests.get(original_url).content

    filled_pdf = fill_pdf(pdf_bytes, values)
    flattened_pdf = flatten_pdf(filled_pdf)

    path = f"filled/{file_id}.pdf"
    upload_to_bucket(path, flattened_pdf)

    supabase.table("files").update({
        "final_values": values,
        "final_pdf_path": path,
        "status": "filled"
    }).eq("file_id", file_id).execute()

    return {"filled_path": path}
