"""Pure helpers for image and PDF handling. No Streamlit imports."""

import base64
import io

import fitz  # PyMuPDF
from PIL import Image


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
