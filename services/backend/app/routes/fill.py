from fastapi import APIRouter, HTTPException
import tempfile, os, json
from app.supabase_client import supabase
from app.config import SUPABASE_BUCKET
from pypdf import PdfReader, PdfWriter

router = APIRouter(prefix="/fill")

@router.post("/{file_id}")
async def fill_pdf(file_id: str, payload: dict):
    try:
        db_res = supabase.table('files').select('*').eq('file_id', file_id).execute()
        if not db_res.data:
            raise HTTPException(status_code=404, detail='File not found')
        row = db_res.data[0]
        storage_path = row.get('storage_path')

        download = supabase.storage.from_(SUPABASE_BUCKET).download(storage_path)
        if not download:
            raise HTTPException(status_code=404, detail='PDF missing in storage')

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(download)
            tmp_path = tmp.name

        reader = PdfReader(tmp_path)
        writer = PdfWriter()
        for p in reader.pages:
            writer.add_page(p)

        # try update form fields if present
        try:
            writer.update_page_form_field_values(writer.pages[0], payload)
        except Exception:
            pass

        out_path = f"/tmp/{file_id}_filled.pdf"
        with open(out_path, 'wb') as f:
            writer.write(f)

        filled_path = f"filled/{file_id}.pdf"
        supabase.storage.from_(SUPABASE_BUCKET).upload(filled_path, out_path)
        supabase.table('files').update({'final_pdf_path': filled_path, 'status':'filled'}).eq('file_id', file_id).execute()

        return {'status':'filled','filled_path': filled_path}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Fill failed: {str(e)}')
    finally:
        try: os.remove(tmp_path)
        except: pass
