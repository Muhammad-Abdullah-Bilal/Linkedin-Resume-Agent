import os

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts clean text from a PDF file using pdfminer.six.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at path: {pdf_path}")

    # Method 1: Try pdfminer.six (pure Python, highly reliable)
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(pdf_path).strip()
        if text:
            return text
    except Exception as e:
        print(f"pdfminer extraction failed: {e}")

    # Method 2: Try PyMuPDF (fitz)
    try:
        import fitz
        doc = fitz.open(pdf_path)
        text = "\n".join([page.get_text() for page in doc]).strip()
        if text:
            return text
    except Exception:
        pass

    # Method 3: Try pypdf
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        text_content = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text)
        text = "\n".join(text_content).strip()
        if text:
            return text
    except Exception:
        pass

    raise ValueError(f"Could not extract readable text from {pdf_path}.")
