from pypdf import PdfReader, PdfWriter

def fill_pdf(pdf_bytes: bytes, values: dict):
    reader = PdfReader(pdf_bytes)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.update_page_form_field_values(writer.pages[0], values)

    output = bytes()
    with open("/tmp/output.pdf", "wb") as f:
        writer.write(f)
    return open("/tmp/output.pdf", "rb").read()
