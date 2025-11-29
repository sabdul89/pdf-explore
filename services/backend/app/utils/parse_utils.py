
import fitz, re

def extract_fields_pymupdf_from_doc(doc):
    fields = []
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        blocks = page.get_text("blocks")
        for b in blocks:
            text = b[4].strip()
            if not text:
                continue
            # heuristic: labels with underscores or sequences of dots
            if re.search(r'_{3,}', text) or re.search(r'\.{3,}', text):
                fields.append({"page": page_num, "type":"underline_field", "text_raw": text, "bbox": b[:4]})
            # labeled field pattern: 'Name: ______'
            if ':' in text and re.search(r'_{2,}', text):
                label = text.split(':')[0].strip()
                fields.append({"page": page_num, "type":"labeled_field", "label": label, "text_raw": text, "bbox": b[:4]})
    return fields

def extract_acroform_fields(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        if not doc.is_form_pdf:
            doc.close()
            return []
        # PyMuPDF form access - parse widgets on all pages
        fields = []
        for p in range(doc.page_count):
            page = doc.load_page(p)
            for widget in page.widgets():
                name = getattr(widget, "field_name", None)
                ft = getattr(widget, "field_type", None)
                if name:
                    fields.append({"page": p, "key": name, "type": "acrofield", "field_type": ft})
        doc.close()
        return fields
    except Exception:
        return []
