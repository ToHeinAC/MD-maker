"""MD-maker Streamlit UI: drop a PDF/image, convert to Markdown via Ollama."""

import io
import subprocess

import streamlit as st
from dotenv import load_dotenv
from PIL import Image

from models import AVAILABLE_MODELS, DEFAULT_MODEL_LABEL, convert_image
from pdf_utils import pdf_to_images

load_dotenv()

APP_PORT = 8521
PAGE_SEPARATOR = "\n\n---\n\n"

st.set_page_config(page_title="Doc → Markdown", layout="wide")
st.title("📄 Document → Markdown")
st.caption("100% local via Ollama. Drop a PDF or image, get Markdown.")

col_left, col_right = st.columns(2)

with col_left:
    labels = list(AVAILABLE_MODELS.keys())
    model_label = st.selectbox("Model", labels, index=labels.index(DEFAULT_MODEL_LABEL))
    model_id = AVAILABLE_MODELS[model_label]
    st.caption(f"Ollama tag: `{model_id}`")

    dpi = st.slider(
        "Render DPI (PDF only)", 72, 300, 150,
        help="Higher = better OCR accuracy, slower.",
    )

    uploaded = st.file_uploader(
        "Drop PDF or image here",
        type=["pdf", "png", "jpg", "jpeg", "webp", "tiff"],
    )

    st.divider()
    if st.button(f"🛑 Stop server (port {APP_PORT})"):
        st.warning(f"Killing process on port {APP_PORT}…")
        subprocess.run(
            f"lsof -ti:{APP_PORT} | xargs -r kill -9",
            shell=True, check=False,
        )

with col_right:
    if uploaded is not None:
        file_bytes = uploaded.read()
        is_pdf = uploaded.type == "application/pdf" or uploaded.name.lower().endswith(".pdf")

        if is_pdf:
            pages = pdf_to_images(file_bytes, dpi=dpi)
            st.info(f"PDF detected — {len(pages)} page(s).")
            preview_idx = st.number_input("Preview page", 1, len(pages), 1) - 1
            st.image(pages[preview_idx], caption=f"Page {preview_idx + 1}", use_container_width=True)
        else:
            pages = [Image.open(io.BytesIO(file_bytes)).convert("RGB")]
            st.image(pages[0], caption="Uploaded image", use_container_width=True)

        if st.button("🚀 Convert to Markdown", type="primary"):
            results: list[str] = []
            prog = st.progress(0.0, text="Processing…")
            for i, page_img in enumerate(pages):
                prog.progress(i / len(pages), text=f"Page {i + 1}/{len(pages)}…")
                results.append(convert_image(model_id, page_img))
            prog.progress(1.0, text="Done.")

            combined = PAGE_SEPARATOR.join(results)
            st.subheader("Result")
            tab_raw, tab_preview = st.tabs(["Raw Markdown", "Rendered Preview"])
            with tab_raw:
                st.code(combined, language="markdown")
                st.download_button(
                    "⬇️ Download .md",
                    data=combined.encode(),
                    file_name=uploaded.name.rsplit(".", 1)[0] + ".md",
                    mime="text/markdown",
                )
            with tab_preview:
                st.markdown(combined)
    else:
        st.info("Upload a PDF or image to begin.")
