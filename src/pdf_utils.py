"""Pure helpers for image and PDF handling. No Streamlit imports."""

import base64
import io

from collections.abc import Iterator

import pypdfium2 as pdfium
from PIL import Image

TEXT_THRESHOLD = 40  # chars; below this a page is treated as image-only


def image_to_base64(pil_image: Image.Image) -> str:
    buf = io.BytesIO()
    pil_image.convert("RGB").save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def pdf_to_images(pdf_bytes: bytes, dpi: int = 150) -> list[Image.Image]:
    scale = dpi / 72
    doc = pdfium.PdfDocument(pdf_bytes)
    pages: list[Image.Image] = []
    for page in doc:
        bitmap = page.render(scale=scale)
        pages.append(bitmap.to_pil())
    return pages


def iter_pdf_pages(
    pdf_bytes: bytes, dpi: int = 150
) -> Iterator[tuple[str, str | Image.Image]]:
    """Yield ('text', str) for pages with extractable text, ('image', PIL.Image) otherwise."""
    scale = dpi / 72
    doc = pdfium.PdfDocument(pdf_bytes)
    for page in doc:
        textpage = page.get_textpage()
        text = textpage.get_text_range().strip()
        if len(text) >= TEXT_THRESHOLD:
            yield "text", text
        else:
            bitmap = page.render(scale=scale)
            yield "image", bitmap.to_pil()
