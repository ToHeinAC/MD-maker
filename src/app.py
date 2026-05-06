"""MD-maker Streamlit UI: drop a PDF/image, convert to Markdown via Ollama."""

import io

import ollama
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

from models import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL_LABEL,
    DEFAULT_REWRITE_MODEL_LABEL,
    convert_image,
    rewrite_text,
)
from pdf_utils import iter_pdf_pages, pdf_to_images

load_dotenv()

APP_PORT = 8521
PAGE_SEPARATOR = "\n\n---\n\n"

st.set_page_config(page_title="Doc → Markdown", layout="wide")
st.title("📄 Document → Markdown")
st.caption("100% local via Ollama. Drop a PDF or image, get Markdown.")

st.session_state.setdefault("converting", False)
st.session_state.setdefault("result", None)
st.session_state.setdefault("result_filename", None)
st.session_state.setdefault("pending_file_bytes", None)
st.session_state.setdefault("pending_file_name", None)
st.session_state.setdefault("pending_is_pdf", False)
st.session_state.setdefault("show_result", False)

busy = st.session_state.converting

col_left, col_right = st.columns(2)

with col_left:
    labels = list(AVAILABLE_MODELS.keys())
    model_label = st.selectbox(
        "OCR model (images & scanned pages)",
        labels,
        index=labels.index(DEFAULT_MODEL_LABEL),
        disabled=busy,
    )
    model_id = AVAILABLE_MODELS[model_label]
    st.caption(f"Ollama tag: `{model_id}`")

    rewrite_label = st.selectbox(
        "Rewrite model (PDF text pages)",
        labels,
        index=labels.index(DEFAULT_REWRITE_MODEL_LABEL),
        disabled=busy,
    )
    rewrite_model_id = AVAILABLE_MODELS[rewrite_label]
    st.caption(f"Ollama tag: `{rewrite_model_id}`")

    dpi = st.slider(
        "Render DPI (PDF only)", 72, 300, 150,
        help="Higher = better OCR accuracy, slower.",
        disabled=busy,
    )

    uploaded = st.file_uploader(
        "Drop PDF or image here",
        type=["pdf", "png", "jpg", "jpeg", "webp", "tiff"],
        disabled=busy,
    )

    convert_clicked = st.button(
        "📖 Convert to Markdown",
        type="primary",
        disabled=busy or uploaded is None,
    )

    has_result = bool(st.session_state.result) and not busy
    if st.button("👁 Show result", disabled=not has_result):
        st.session_state.show_result = True
    if has_result:
        out_name = (st.session_state.result_filename or "document").rsplit(".", 1)[0] + ".md"
        st.download_button(
            "⬇️ Download .md",
            data=st.session_state.result.encode(),
            file_name=out_name,
            mime="text/markdown",
        )
    else:
        st.button("⬇️ Download .md", disabled=True)

    st.divider()
    if st.button("🔄 Reset session & unload models", disabled=busy):
        for m in {model_id, rewrite_model_id}:
            try:
                ollama.generate(model=m, prompt="", keep_alive=0, stream=False)
            except Exception:
                pass
        for key, default in {
            "converting": False, "result": None, "result_filename": None,
            "pending_file_bytes": None, "pending_file_name": None,
            "pending_is_pdf": False, "show_result": False,
        }.items():
            st.session_state[key] = default
        st.rerun()

with col_right:
    if uploaded is not None and not busy:
        file_bytes = uploaded.read()
        is_pdf = uploaded.type == "application/pdf" or uploaded.name.lower().endswith(".pdf")

        if is_pdf:
            pages = pdf_to_images(file_bytes, dpi=dpi)
            st.info(f"PDF detected — {len(pages)} page(s).")
            preview_idx = st.number_input(
                "Preview page", 1, len(pages), 1, disabled=busy,
            ) - 1
            st.image(pages[preview_idx], caption=f"Page {preview_idx + 1}", use_container_width=True)
        else:
            pages = [Image.open(io.BytesIO(file_bytes)).convert("RGB")]
            st.image(pages[0], caption="Uploaded image", use_container_width=True)

        if convert_clicked:
            st.session_state.converting = True
            st.session_state.result = None
            st.session_state.result_filename = None
            st.session_state.pending_file_bytes = file_bytes
            st.session_state.pending_file_name = uploaded.name
            st.session_state.pending_is_pdf = is_pdf
            st.rerun()

    elif busy:
        file_bytes = st.session_state.pending_file_bytes
        is_pdf = st.session_state.pending_is_pdf
        file_name = st.session_state.pending_file_name

        if is_pdf:
            items = list(iter_pdf_pages(file_bytes, dpi=dpi))
        else:
            img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            items = [("image", img)]

        results: list[str] = []
        try:
            with st.status("Converting…", expanded=True) as status:
                prog = st.progress(0.0)
                total = len(items)
                for i, (kind, payload) in enumerate(items):
                    page_no = i + 1
                    if kind == "text":
                        status.write(
                            f"Page {page_no}/{total} — plain text extraction (PyMuPDF)"
                        )
                        results.append(rewrite_text(rewrite_model_id, payload))
                    else:
                        prefix = f"Page {page_no}/{total} — " if total > 1 else ""
                        status.write(f"{prefix}OCR via {model_label}")
                        results.append(convert_image(model_id, payload))
                    prog.progress(page_no / total)
                status.update(label="Done.", state="complete")

            st.session_state.result = PAGE_SEPARATOR.join(results)
            st.session_state.result_filename = file_name
            st.session_state.show_result = False
        finally:
            st.session_state.converting = False
            st.session_state.pending_file_bytes = None
            st.session_state.pending_file_name = None
        st.rerun()

    elif st.session_state.result is None:
        st.info("Upload a PDF or image to begin.")

    if st.session_state.result and not busy and st.session_state.show_result:
        combined = st.session_state.result
        st.subheader("Result")
        tab_raw, tab_preview = st.tabs(["Raw Markdown", "Rendered Preview"])
        with tab_raw:
            st.code(combined, language="markdown")
        with tab_preview:
            st.markdown(combined)
