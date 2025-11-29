
import fitz
import tempfile, os
from PIL import Image
import pytesseract
import cv2
import numpy as np

def pdf_page_to_image(pdf_path, page_num=0, dpi=200):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
    return img

def deskew_image_pil(pil_img):
    # Convert PIL to OpenCV
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)
    # threshold
    _, th = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(th < 255))
    if coords.shape[0] < 10:
        return pil_img  # nothing to deskew
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = img.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(np.array(pil_img), M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return Image.fromarray(rotated)

def enhance_image_for_ocr(pil_img):
    # convert to grayscale, increase contrast, denoise, adaptive threshold
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)
    img = cv2.GaussianBlur(img, (3,3), 0)
    img = cv2.adaptiveThreshold(img,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,11,2)
    return Image.fromarray(img)

def ocr_pdf_text(pdf_path, pages=None, lang='eng'):
    texts = []
    doc = fitz.open(pdf_path)
    total_pages = doc.page_count
    pages_to_run = pages if pages is not None else list(range(total_pages))
    for p in pages_to_run:
        pil = pdf_page_to_image(pdf_path, page_num=p, dpi=300)
        try:
            pil = deskew_image_pil(pil)
        except Exception:
            pass
        pil = enhance_image_for_ocr(pil)
        text = pytesseract.image_to_string(pil, lang=lang)
        texts.append(text)
    doc.close()
    return "\\n\\n".join(texts)

def ocr_pdf_pages_with_confidence(pdf_path, lang='eng'):
    # returns list of pages with (text, confidence_average)
    results = []
    doc = fitz.open(pdf_path)
    for p in range(doc.page_count):
        pil = pdf_page_to_image(pdf_path, page_num=p, dpi=300)
        try:
            pil = deskew_image_pil(pil)
        except Exception:
            pass
        pil = enhance_image_for_ocr(pil)
        # pytesseract image_to_data gives word-level confidences
        data = pytesseract.image_to_data(pil, lang=lang, output_type=pytesseract.Output.DICT)

        text = " ".join([w for w in data.get("text", []) if w.strip() != ""])

        raw_confs = data.get("conf", [])
        confs = []

        for c in raw_confs:
            if isinstance(c, int):
                if c >= 0:
                    confs.append(c)
                continue
            if isinstance(c, str) and c.isdigit():
                if int(c) >= 0:
                    confs.append(int(c))

        avg_conf = float(sum(confs)) / len(confs) if len(confs) > 0 else 0.0

        results.append({"page": p, "text": text, "avg_conf": avg_conf})

    doc.close()
    return results
