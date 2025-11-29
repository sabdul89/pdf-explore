from pydantic import BaseModel

class UploadResponse(BaseModel):
    file_id: str
    storage_path: str

class ParseResponse(BaseModel):
    fields: list
    ocr_text: str | None = None

class FillRequest(BaseModel):
    file_id: str
    values: dict
