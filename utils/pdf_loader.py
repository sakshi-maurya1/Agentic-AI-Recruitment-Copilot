import fitz
import os
from langchain_core.documents import Document

# OCR is only imported/used when a page has no extractable text layer —
# this keeps normal text-based PDFs fast and avoids a hard OCR dependency
# for people who never touch scanned resumes.
try:
    import pytesseract
    from PIL import Image
    import io

    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Below this many non-whitespace characters, treat the page as having no
# real text layer (image-only / scanned page) and fall back to OCR.
MIN_TEXT_LENGTH = 20


def _ocr_page(page, dpi: int = 300) -> str:
    """Render a PDF page to an image and run OCR on it."""
    if not OCR_AVAILABLE:
        raise RuntimeError(
            "This PDF appears to be image-based (scanned) and has no "
            "extractable text layer, but OCR dependencies aren't installed. "
            "Run: pip install pytesseract pillow, and install the Tesseract "
            "binary itself (e.g. `brew install tesseract` on Mac, "
            "`sudo apt install tesseract-ocr` on Linux, or the Windows "
            "installer from https://github.com/UB-Mannheim/tesseract/wiki)."
        )

    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    pixmap = page.get_pixmap(matrix=matrix)
    image = Image.open(io.BytesIO(pixmap.tobytes("png")))
    return pytesseract.image_to_string(image)


def load_pdf(pdf_path: str):

    pdf = fitz.open(pdf_path)

    documents = []

    for page_number, page in enumerate(pdf):

        text = page.get_text()
        native_text_length = len(text.strip())

        # If the page has little/no real text, it's likely a scanned image
        # (e.g. a resume photographed or scanned as a picture-only PDF).
        # Fall back to OCR instead of silently passing empty text downstream.
        used_ocr = native_text_length < MIN_TEXT_LENGTH
        if used_ocr:
            text = _ocr_page(page)

        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source": os.path.basename(pdf_path),
                    "page": page_number + 1,
                    "ocr_used": used_ocr,
                }
            )
        )

    pdf.close()

    return documents