
import os
from app.utils.parse_utils import extract_acroform_fields, extract_fields_pymupdf_from_doc
from app.utils.ocr_utils import ocr_pdf_text, ocr_pdf_pages_with_confidence
from app.utils.ocr_to_fields import parse_ocr_to_fields
import fitz

FIELD_THRESHOLD = 2

def extract_hybrid_raw(pdf_path):
    # try acroform first
    acro = extract_acroform_fields(pdf_path)
    if acro and len(acro) > 0:
        # convert to schema
        fields = [{"key": f.get("key"), "label": f.get("key")} for f in acro]
        return {"method":"form","fields":fields,"json_schema":{"type":"object","properties":{f['key']:{'type':'string'} for f in fields}}}

    # try layout heuristic
    try:
        doc = fitz.open(pdf_path)
        layout_fields = extract_fields_pymupdf_from_doc(doc)
        doc.close()
    except Exception:
        layout_fields = []

    if layout_fields and len(layout_fields) >= FIELD_THRESHOLD:
        # basic conversion
        fields = []
        props = {}
        for i,f in enumerate(layout_fields):
            k = f"field_{i+1}"
            fields.append({"key":k,"label":f.get("label", f.get("text_raw","field"))})
            props[k] = {"type":"string","title":f.get("label", f.get("text_raw","field"))}
        return {"method":"layout","fields":fields,"json_schema":{"type":"object","properties":props}}

    # fallback to OCR with preprocessing and confidence
    pages = ocr_pdf_pages_with_confidence(pdf_path)
    # If average confidence across pages is high, parse text into fields
    avg_conf = sum([p['avg_conf'] for p in pages]) / (len(pages) or 1)
    full_text = "\\n\\n".join([p['text'] for p in pages])
    parsed = parse_ocr_to_fields(full_text)
    parsed['_metadata'] = {"avg_confidence": avg_conf, "pages": len(pages)}
    return {"method":"ocr","fields": parsed["fields"], "json_schema": parsed["json_schema"], "metadata": parsed["_metadata"]}
