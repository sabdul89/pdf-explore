from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid, datetime, os
from app.supabase_client import supabase
from app.config import SUPABASE_BUCKET, TEMP_DIR, MAX_UPLOAD_MB
from app.utils.hybrid_extractor import extract_hybrid_raw

router = APIRouter(prefix="/upload")

@router.post("/")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail='Only PDF allowed')
        contents = await file.read()
        if len(contents) > MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail='File too large')

        file_id = str(uuid.uuid4())
        temp_path = os.path.join(TEMP_DIR, f"{file_id}.pdf")
        with open(temp_path, 'wb') as f:
            f.write(contents)

        storage_path = f"original/{file_id}.pdf"
        upload_res = supabase.storage.from_(SUPABASE_BUCKET).upload(storage_path, temp_path)
        if upload_res is None or getattr(upload_res, 'error', None):
            raise HTTPException(status_code=500, detail='Storage upload failed')

        # Run hybrid extraction in background-style (synchronous here)
        extraction = extract_hybrid_raw(temp_path)

        # insert DB record
        record = {
            'file_id': file_id,
            'storage_path': storage_path,
            'original_filename': file.filename,
            'status': 'uploaded'
        }
        supabase.table('files').insert(record).execute()

        # cleanup temp
        try:
            os.remove(temp_path)
        except:
            pass

        return {'file_id': file_id, 'storage_path': storage_path, 'extraction_summary': extraction.get('method')}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Upload error: {str(e)}')
