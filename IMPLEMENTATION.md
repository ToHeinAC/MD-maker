# IMPLEMENTATION

Compact reference for the current implementation state. Deeper details live under [docs/](docs/).

## Module map

| File | Responsibility |
|---|---|
| `src/app.py` | Streamlit UI, file upload, page preview, convert button, download, safe-exit. |
| `src/models.py` | `AVAILABLE_MODELS`, `DEFAULT_MODEL_LABEL`, `DEFAULT_REWRITE_MODEL_LABEL`, `convert_image()` (OCR), `rewrite_text()` (text→MD). |
| `src/prompts.py` | All prompt strings (`SYSTEM_PROMPT`, `USER_PROMPT`, `DEEPSEEK_PROMPT`, `REWRITE_PROMPT`). |
| `src/pdf_utils.py` | `pdf_to_images()` (preview), `iter_pdf_pages()` (per-page text-or-image), `image_to_base64()`. |

## Dataflow

```
upload (PDF/image) → bytes
    ├── PDF  → iter_pdf_pages(bytes, dpi)
    │           ├── ('text',  str)  → rewrite_text(rewrite_model, text)  → markdown
    │           └── ('image', img)  → convert_image(ocr_model, img)      → markdown
    └── image → convert_image(ocr_model, img) → markdown
join with "\n\n---\n\n" → display (Raw / Rendered tabs) + download .md
```

Per-page detection: a PDF page is treated as text when `page.get_text("text").strip()` ≥ 40 chars; otherwise rasterized and OCR'd. Mixed PDFs (text + scanned pages) are handled transparently.

## Vision guard and prompt routing (`models.convert_image`)

- `VISION_MODELS` frozenset lists Ollama tags that accept an `images` payload (`deepseek-ocr:3b` only). `convert_image()` raises `ValueError` for any other model; `app.py` catches it and shows `st.error()`. Gemma 4 variants are text-only and blocked from the OCR path.
- `deepseek-ocr:*` → `DEEPSEEK_PROMPT = "<|grounding|>Convert the document to markdown."` Short prompt + grounding token required; verbose instructions degrade output. Single user message, no system role.
- `gemma4:*` → rewrite path only via `rewrite_text()`.

See [docs/models.md](docs/models.md).

## UI behavior (`src/app.py`)

- **Layout** — left column: model pickers, DPI, file uploader, **📖 Convert**, **👁 Show result**, **⬇️ Download .md**, divider, **🛑 Stop server**. Right column: file preview, live status box during a run, optional result tabs (Raw / Rendered).
- **Failsafe lock** — `st.session_state.converting` is flipped to `True` on Convert click; the click stashes file bytes in session state and triggers a rerun so all input widgets (model selectors, DPI, uploader, preview page input, Convert button) render with `disabled=True`. Only **Stop server** stays enabled. The flag resets in a `finally` block followed by `st.rerun()`.
- **Verbose status** — per-page lines emitted into `st.status("Converting…", expanded=True)`: `Page i/N — plain text extraction (PyMuPDF)` or `Page i/N — OCR via {model_label}`. A progress bar updates alongside.
- **Result gating** — result is cached in `st.session_state.result`; the Raw/Rendered tabs only render after the user clicks **Show result** (which sets `show_result=True`). Download button is a real `st.download_button` once a result exists, otherwise a disabled placeholder.

## Config knobs

- **OCR model** — selectbox; default `DeepSeek-OCR 3B`. Used for image uploads and scanned PDF pages.
- **Rewrite model** — selectbox; default `Gemma 4 E4B`. Reformats extracted PDF text to Markdown without altering wording.
- **DPI** — 72–300, default 150 (PDF rasterization, only used for image-only pages and the preview pane).
- **Port** — hardcoded to 8521 (matches CLAUDE.md and the safe-exit button).
- **`OLLAMA_HOST`** — env var, default `http://localhost:11434`. Loaded from `.env` if present.

## Run

```bash
uv run streamlit run src/app.py --server.port 8521
```

## Out of scope (today)

Tests, batch CLI, async/streaming, output caching, retries, auth.
