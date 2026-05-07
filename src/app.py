"""MD-maker Streamlit UI: drop PDF(s)/image(s), convert each to Markdown via Ollama."""

import io
import zipfile

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
st.caption("100% local via Ollama. Drop PDF(s) or image(s), get Markdown.")

st.session_state.setdefault("converting", False)
st.session_state.setdefault("results", [])       # list[{filename, content}]
st.session_state.setdefault("pending_files", []) # list[{bytes, name, is_pdf}]
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
        "Drop PDF(s) or image(s) here",
        type=["pdf", "png", "jpg", "jpeg", "webp", "tiff"],
        accept_multiple_files=True,
        disabled=busy,
    )

    convert_clicked = st.button(
        "📖 Convert to Markdown",
        type="primary",
        disabled=busy or len(uploaded) == 0,
    )

    has_result = bool(st.session_state.results) and not busy
    if st.button("👁 Show result", disabled=not has_result):
        st.session_state.show_result = True
    if has_result:
        results = st.session_state.results
        if len(results) == 1:
            r = results[0]
            out_name = r["filename"].rsplit(".", 1)[0] + ".md"
            st.download_button(
                "⬇️ Download .md",
                data=r["content"].encode(),
                file_name=out_name,
                mime="text/markdown",
            )
        else:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for r in results:
                    zf.writestr(
                        r["filename"].rsplit(".", 1)[0] + ".md",
                        r["content"].encode(),
                    )
            st.download_button(
                "⬇️ Download .zip",
                data=buf.getvalue(),
                file_name="converted.zip",
                mime="application/zip",
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
            "converting": False, "results": [], "pending_files": [],
            "show_result": False,
        }.items():
            st.session_state[key] = default
        st.rerun()

with col_right:
    if uploaded and not busy:
        # Read all file bytes upfront to avoid double-read issues
        all_files = [
            {
                "bytes": u.read(),
                "name": u.name,
                "is_pdf": u.type == "application/pdf" or u.name.lower().endswith(".pdf"),
            }
            for u in uploaded
        ]

        if len(all_files) > 1:
            names = [f["name"] for f in all_files]
            sel_idx = st.selectbox(
                "Preview file", range(len(names)), format_func=lambda i: names[i]
            )
        else:
            sel_idx = 0
        sel = all_files[sel_idx]

        if sel["is_pdf"]:
            pages = pdf_to_images(sel["bytes"], dpi=dpi)
            st.info(f"{len(all_files)} file(s) selected — \"{sel['name']}\" has {len(pages)} page(s).")
            preview_idx = st.number_input(
                "Preview page", 1, len(pages), 1, disabled=busy,
            ) - 1
            st.image(pages[preview_idx], caption=f"Page {preview_idx + 1}", use_container_width=True)
        else:
            st.info(f"{len(all_files)} file(s) selected.")
            st.image(
                Image.open(io.BytesIO(sel["bytes"])).convert("RGB"),
                caption=sel["name"],
                use_container_width=True,
            )

        if convert_clicked:
            st.session_state.converting = True
            st.session_state.results = []
            st.session_state.pending_files = all_files
            st.rerun()

    elif busy:
        pending_files = st.session_state.pending_files
        accumulated: list[dict] = []
        total_files = len(pending_files)
        try:
            with st.status("Converting…", expanded=True) as status:
                prog = st.progress(0.0)
                for fi, pf in enumerate(pending_files):
                    file_label = f"[{fi + 1}/{total_files}] {pf['name']}"
                    if pf["is_pdf"]:
                        items = list(iter_pdf_pages(pf["bytes"], dpi=dpi))
                    else:
                        img = Image.open(io.BytesIO(pf["bytes"])).convert("RGB")
                        items = [("image", img)]
                    page_results: list[str] = []
                    total_pages = len(items)
                    for pi, (kind, payload) in enumerate(items):
                        page_no = pi + 1
                        if kind == "text":
                            status.write(
                                f"{file_label} — Page {page_no}/{total_pages} — plain text (pypdfium2)"
                            )
                            page_results.append(rewrite_text(rewrite_model_id, payload))
                        else:
                            prefix = f"Page {page_no}/{total_pages} — " if total_pages > 1 else ""
                            status.write(f"{file_label} — {prefix}OCR via {model_label}")
                            page_results.append(convert_image(model_id, payload))
                        prog.progress((fi + page_no / total_pages) / total_files)
                    accumulated.append({
                        "filename": pf["name"],
                        "content": PAGE_SEPARATOR.join(page_results),
                    })
                status.update(label="Done.", state="complete")
            st.session_state.results = accumulated
            st.session_state.show_result = False
        except ValueError as e:
            st.error(str(e))
        finally:
            st.session_state.converting = False
            st.session_state.pending_files = []
        st.rerun()

    elif not st.session_state.results:
        st.info("Upload a PDF or image to begin.")

    if st.session_state.results and not busy and st.session_state.show_result:
        results = st.session_state.results
        if len(results) == 1:
            r = results[0]
            st.subheader(r["filename"])
            tab_raw, tab_preview = st.tabs(["Raw Markdown", "Rendered Preview"])
            with tab_raw:
                st.code(r["content"], language="markdown")
            with tab_preview:
                st.markdown(r["content"])
        else:
            names = [r["filename"] for r in results]
            sel = st.selectbox(
                "View result", range(len(names)), format_func=lambda i: names[i]
            )
            r = results[sel]
            tab_raw, tab_preview = st.tabs(["Raw Markdown", "Rendered Preview"])
            with tab_raw:
                st.code(r["content"], language="markdown")
            with tab_preview:
                st.markdown(r["content"])
