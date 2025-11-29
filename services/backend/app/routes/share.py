from fastapi import APIRouter, HTTPException
import uuid, datetime
from app.supabase_client import supabase
from app.config import SHARE_TOKEN_TTL_HOURS

router = APIRouter(prefix="/share")

@router.post("/create/{file_id}")
async def create_link(file_id: str):
    token = uuid.uuid4().hex
    expires = (datetime.datetime.utcnow() + datetime.timedelta(hours=SHARE_TOKEN_TTL_HOURS)).isoformat()
    supabase.table('shares').insert({'token': token, 'file_id': file_id, 'expires_at': expires}).execute()
    return {'share_url': f'/share/get/{token}'}

@router.get("/get/{token}")
async def get_shared(token: str):
    rec = supabase.table('shares').select('*').eq('token', token).single().execute()
    if not rec.data:
        raise HTTPException(status_code=404, detail='Not found')
    file = supabase.table('files').select('*').eq('file_id', rec.data['file_id']).single().execute().data
    return file
