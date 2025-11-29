import fitz
from app.utils.parser import extract_fields_pymupdf
from app.utils.ocr import extract_with_ocr

HYBRID_THRESHOLD = 2   # how many fields needed to accept PyMuPDF result


def extract_hybrid(pdf_path: str):
    """
    Hybrid extraction logic:
    1. Try PyMuPDF heuristic parser for underline & label detection
    2. If too few fields OR no useful structure → fallback to OCR
    3. Return unified JSON describing how extraction succeeded
    """
    try:
        doc = fitz.open(pdf_path)
        pymupdf_fields = extract_fields_pymupdf(doc)
        doc.close()
    except Exception as e:
        return {
            "method": "error",
            "error": f"PyMuPDF parsing failed: {str(e)}"
        }

    # -----------------------------------------------
    # Decision logic: Is PyMuPDF extraction “good enough”?
    # -----------------------------------------------
    if pymupdf_fields and len(pymupdf_fields) >= HYBRID_THRESHOLD:
        return {
            "method": "pymupdf",
            "fields": pymupdf_fields
        }

    # -----------------------------------------------
    # Otherwise → fallback to OCR
    # -----------------------------------------------
    try:
        ocr_result = extract_with_ocr(pdf_path)
        return {
            "method": "ocr",
            "fields": ocr_result
        }
    except Exception as e:
        return {
            "method": "ocr_error",
            "error": f"OCR failed: {str(e)}"
        }
