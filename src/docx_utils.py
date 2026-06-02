"""Helpers for extracting structured Markdown from .docx files."""

import io

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph


def _paragraph_md(para: Paragraph) -> str | None:
    """Map a paragraph to a Markdown line, or None to skip empty paragraphs."""
    text = para.text.strip()
    if not text:
        return None
    style = para.style.name
    if style.startswith("Heading 1"):
        return f"# {text}"
    if style.startswith("Heading 2"):
        return f"## {text}"
    if style.startswith("Heading 3"):
        return f"### {text}"
    if "Bullet" in style:
        return f"- {text}"
    if "Number" in style:
        return f"1. {text}"
    return text


def _table_md(table: Table) -> str | None:
    """Render a table as a single contiguous Markdown table block."""
    rows = table.rows
    if not rows:
        return None
    lines = []
    header = [c.text.strip() for c in rows[0].cells]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join("---" for _ in header) + " |")
    for row in rows[1:]:
        cells = [c.text.strip() for c in row.cells]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def extract_docx_text(docx_bytes: bytes) -> str:
    """Convert a .docx file to Markdown, preserving document order.

    Headings, lists, paragraphs and tables are emitted in the order they
    appear in the document. The result is final Markdown (no LLM step).
    """
    doc = Document(io.BytesIO(docx_bytes))
    parts: list[str] = []

    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            md = _paragraph_md(Paragraph(child, doc))
        elif child.tag == qn("w:tbl"):
            md = _table_md(Table(child, doc))
        else:
            md = None
        if md:
            parts.append(md)

    return "\n\n".join(parts)
