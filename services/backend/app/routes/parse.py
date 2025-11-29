from fastapi import APIRouter, HTTPException
import tempfile, os
from app.supabase_client import supabase
from app.config import SUPABASE_BUCKET
from app.utils.hybrid_extractor import extract_hybrid_raw
from app.utils.ocr_to_fields import parse_ocr_to_fields

router = APIRouter(prefix="/parse")

@router.get("/{file_id}")
async def parse_pdf(file_id: str):
    try:
        db_res = supabase.table('files').select('*').eq('file_id', file_id).execute()
        if not db_res.data:
            raise HTTPException(status_code=404, detail='File not found')

        row = db_res.data[0]
        storage_path = row.get('storage_path')
        if not storage_path:
            raise HTTPException(status_code=400, detail='Missing storage_path')

        download = supabase.storage.from_(SUPABASE_BUCKET).download(storage_path)
        if not download:
            raise HTTPException(status_code=404, detail='File missing in storage')

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(download)
            tmp_path = tmp.name

        structured = extract_hybrid_raw(tmp_path)
        if structured.get('method') in ('form','layout') and structured.get('fields'):
            schema = {'method': structured['method'], 'fields': structured['fields'], 'json_schema': structured.get('json_schema')}
            supabase.table('files').update({'schema_json': schema}).eq('file_id', file_id).execute()
            return schema

        # OCR fallback: use ocr_to_fields directly
        # hybrid_extractor already did OCR and returned parsed json for 'ocr' as well
        if structured.get('method') == 'ocr' and structured.get('json_schema'):
            supabase.table('files').update({'schema_json': structured['json_schema']}).eq('file_id', file_id).execute()
            return {'method':'ocr','fields': structured.get('fields'),'json_schema': structured.get('json_schema'),'metadata': structured.get('metadata')}

        # Safety fallback: run OCR text and parse
        from app.utils.ocr_utils import ocr_pdf_text
        ocr_text = ocr_pdf_text(tmp_path)
        parsed = parse_ocr_to_fields(ocr_text)
        supabase.table('files').update({'schema_json': parsed['json_schema']}).eq('file_id', file_id).execute()
        return {'method':'ocr_fallback','fields': parsed['fields'],'json_schema': parsed['json_schema']}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Parse failed: {str(e)}')
    finally:
        try: os.remove(tmp_path)
        except: pass
