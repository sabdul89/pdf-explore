from fastapi import APIRouter
import requests

from app.supabase_client import supabase
from app.storage import get_public_url
from app.parse_pdf import extract_text_blocks, detect_form_fields
from app.ocr_fallback import ocr_pdf

router = APIRouter()

@router.get("/{file_id}")
def parse(file_id: str):
    file = supabase.table("files").select("*").eq("file_id", file_id).single().execute().data

    url = get_public_url(f"original/{file_id}.pdf")
    pdf_bytes = requests.get(url).content

    blocks = extract_text_blocks(pdf_bytes)
    fields = detect_form_fields(blocks)

    # OCR fallback if no structured fields detected
    ocr_text = None
    if len(fields) == 0:
        ocr_text = ocr_pdf(pdf_bytes)

    # Save into DB
    supabase.table("files").update({
        "extracted_json": fields,
        "ocr_text": ocr_text
    }).eq("file_id", file_id).execute()

    return {"fields": fields, "ocr_text": ocr_text}
