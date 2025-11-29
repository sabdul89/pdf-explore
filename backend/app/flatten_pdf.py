from pypdf import PdfReader, PdfWriter

def flatten_pdf(pdf_bytes: bytes):
    reader = PdfReader(pdf_bytes)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.remove_annotations()
    writer.remove_form_fields()

    with open("/tmp/flat.pdf", "wb") as f:
        writer.write(f)

    return open("/tmp/flat.pdf", "rb").read()
