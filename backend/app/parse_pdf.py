import fitz

def extract_text_blocks(pdf_bytes: bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    blocks = []
    for page_num, page in enumerate(doc):
        for block in page.get_text("blocks"):
            blocks.append({
                "page": page_num,
                "bbox": block[:4],
                "text": block[4].strip()
            })
    return blocks

def detect_form_fields(blocks):
    fields = []
    for blk in blocks:
        text = blk["text"]
        if "_" in text or ":" in text:
            fields.append({
                "label": text.replace("_", "").strip(),
                "value": "",
                "page": blk["page"],
                "bbox": blk["bbox"]
            })
    return fields
