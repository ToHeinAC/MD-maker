"""Pure helpers for image and PDF handling. No Streamlit imports."""

import base64
import io

from collections.abc import Iterator

import fitz  # PyMuPDF
from PIL import Image

TEXT_THRESHOLD = 40  # chars; below this a page is treated as image-only


def image_to_base64(pil_image: Image.Image) -> str:
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def pdf_to_images(pdf_bytes: bytes, dpi: int = 150) -> list[Image.Image]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    scale = dpi / 72
    matrix = fitz.Matrix(scale, scale)
    pages: list[Image.Image] = []
    for page in doc:
        pix = page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB)
        pages.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
    doc.close()
    return pages


def iter_pdf_pages(
    pdf_bytes: bytes, dpi: int = 150
) -> Iterator[tuple[str, str | Image.Image]]:
    """Yield ('text', str) for pages with extractable text, ('image', PIL.Image) otherwise."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    scale = dpi / 72
    matrix = fitz.Matrix(scale, scale)
    for page in doc:
        text = page.get_text("text").strip()
        if len(text) >= TEXT_THRESHOLD:
            yield "text", text
        else:
            pix = page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB)
            yield "image", Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
