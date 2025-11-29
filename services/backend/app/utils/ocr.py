import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import tempfile
import os

def extract_with_ocr(pdf_path: str):
    """
    Extract text from a PDF using OCR. Used as fallback if PyMuPDF
    cannot find structured fields.
    """
    results = []

    doc = fitz.open(pdf_path)

    for page_index, page in enumerate(doc):
        pix = page.get_pixmap(dpi=200)

        # Save page as temporary image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(pix.tobytes("png"))
            temp_img_path = f.name

        # OCR the image
        text = pytesseract.image_to_string(Image.open(temp_img_path))

        results.append({
            "page": page_index + 1,
            "text": text.strip()
        })

        os.remove(temp_img_path)

    doc.close()

    return {
        "type": "ocr",
        "pages": results
    }
