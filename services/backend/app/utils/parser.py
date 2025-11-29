import fitz

def extract_fields_pymupdf(doc):
    """
    Attempts to extract fillable-looking regions from a *non-form* PDF
    using underline heuristics + text proximity.
    """

    extracted = []

    for page_index, page in enumerate(doc):
        blocks = page.get_text("blocks")

        for b in blocks:
            text = b[4].strip()

            if not text:
                continue

            # Heuristic: detect underlines or blank lines
            if "____" in text or "______" in text or "_____" in text:
                extracted.append({
                    "page": page_index + 1,
                    "type": "underline_field",
                    "text_raw": text
                })

            # Detect common fill patterns like: “Name: ________”
            elif ":" in text and ("____" in text or "______" in text):
                label = text.split(":")[0].strip()
                extracted.append({
                    "page": page_index + 1,
                    "type": "labeled_field",
                    "label": label,
                    "text_raw": text
                })

    return extracted
