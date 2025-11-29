import uuid
import datetime
import os
import fitz  # PyMuPDF
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.supabase_client import supabase
from app.config import SUPABASE_BUCKET
from app.utils.ocr import extract_with_ocr
from app.utils.parser import extract_fields_pymupdf
from app.utils.hybrid_extractor import extract_hybrid

router = APIRouter()

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        # -------------------------------
        # 1. Validate file type
        # -------------------------------
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

        # -------------------------------
        # 2. Store temporarily in /tmp
        # -------------------------------
        file_id = str(uuid.uuid4())
        temp_path = f"/tmp/{file_id}.pdf"

        with open(temp_path, "wb") as temp_file:
            temp_file.write(await file.read())

        # -------------------------------
        # 3. Upload to Supabase Storage
        # -------------------------------
        storage_path = f"original/{file_id}.pdf"

        upload_res = supabase.storage.from_(SUPABASE_BUCKET).upload(
            storage_path,
            temp_path
        )

        # Upload error?
        if "error" in upload_res:
            raise HTTPException(status_code=500, detail="Failed to upload to storage.")

        # -------------------------------
        # 4. Extract Fields (Hybrid Parser)
        # -------------------------------
        try:
            doc = fitz.open(temp_path)
            fields = extract_hybrid(temp_path)  # Your text/underline parser
            doc.close()

            # If we found nothing, fallback to OCR
            if not fields:
                fields = extract_with_ocr(temp_path)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")

        # -------------------------------
        # 5. Insert DB Record (Now Safe)
        # -------------------------------
        record = {
            "file_id": file_id,
            "storage_path": storage_path,
            "original_filename": file.filename,
            "status": "uploaded",
            "created_at": datetime.datetime.utcnow().isoformat(),
            "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(hours=24)).isoformat()
        }

        db_res = supabase.table("files").insert(record).execute()

        if hasattr(db_res, "error") and db_res.error:
            raise HTTPException(status_code=500, detail=f"DB insert failed: {db_res.error.message}")

        # -------------------------------
        # 6. Cleanup
        # -------------------------------
        if os.path.exists(temp_path):
            os.remove(temp_path)

        # -------------------------------
        # 7. Return response
        # -------------------------------
        return {
            "file_id": file_id,
            "storage_path": storage_path,
            "fields": fields,
            "status": "uploaded"
        }

    except HTTPException:
        raise  # rethrow clean FastAPI error

    except Exception as e:
        # Catch ALL unexpected errors to avoid 500s leaking internal info
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
