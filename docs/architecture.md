# Architecture

## Goals
- Convert a dropped PDF or image into structured Markdown using a local Ollama vision model.
- Keep the implementation small, dependency-light, and on-prem.

## Module responsibilities

- **`src/app.py`** — Streamlit-only concerns: two-column layout, file upload, model pickers (OCR + rewrite), DPI slider, conversion lock, live status box, gated result tabs, download, safe-exit button. No prompt strings.
- **`src/models.py`** — `AVAILABLE_MODELS` map, `VISION_MODELS` guard, `convert_image()` (vision OCR, deepseek-ocr only), `rewrite_text()` (text → Markdown via rewrite model).
- **`src/prompts.py`** — prompt constants only, per project rule (CLAUDE.md §5.3): `SYSTEM_PROMPT`, `USER_PROMPT`, `DEEPSEEK_PROMPT`, `REWRITE_PROMPT`.
- **`src/pdf_utils.py`** — pure functions usable in any context (CLI, tests, notebook): `pdf_to_images()` for the preview pane and `iter_pdf_pages()` for the per-page text-or-image dispatcher used during conversion.
- **`src/docx_utils.py`** — pure function `extract_docx_text()`: walks the DOCX body in order and emits Markdown (headings, lists, contiguous table blocks) directly. No Streamlit, no LLM.

## Why per-page calls
Vision models receive a single image per request. A multi-page PDF is processed sequentially; pages with extractable digital text (≥ 40 chars from `page.get_text`) are routed through `rewrite_text()` (cheap, lossless reformatting) and the rest are rasterized at `dpi` and OCR'd via `convert_image()`. The page boundary is preserved as `\n\n---\n\n` in the joined output so the user can locate any page in the resulting `.md`.

## Why DOCX bypasses the LLM
A `.docx` is already structured XML, so `extract_docx_text()` produces final Markdown directly — no OCR and no rewrite pass. Routing it through `rewrite_text()` would risk the model dropping or altering content (notably tables) for no benefit. The conversion loop yields a `('markdown', str)` item that is appended verbatim. Legacy `.doc` (binary CFB) has no light pure-Python parser and is rejected with a `ValueError` advising re-save as `.docx`.

## UI flow and failsafe lock
The Streamlit UI keeps all action buttons in the left column (Convert / Show result / Download / Stop). Clicking **Convert** stashes the uploaded bytes into `st.session_state`, sets `converting=True`, and forces a rerun so every input widget on the next render is `disabled=True` — only **Stop server** stays clickable. The conversion loop then runs inside `st.status(..., expanded=True)` in the right column, writing one line per page (`PyMuPDF` text vs `OCR via …`) alongside a progress bar. The result is cached in session state and only rendered (Raw / Rendered tabs) after the user clicks **Show result**, keeping the right column quiet by default.

## DPI tradeoff
- 72–100 dpi: fast, fine for clean print.
- 150 dpi (default): good balance for typical documents.
- 200–300 dpi: dense small-print or scans; slower and produces larger images that may stress the model context.

## Why no abstraction over models
One vision model (`deepseek-ocr:3b`) and one `if` branch in `convert_image`. A Strategy/Registry pattern would add files for no benefit. Gemma 4 variants are text-only and used only in `rewrite_text()`, which needs no branching.

## Safe exit
Per global CLAUDE.md, the app exposes a button that runs `lsof -ti:8521 | xargs -r kill -9`. The port is hardcoded to the run port (8521), not derived from `os.getpid()`'s parent — this means it kills the streamlit server cleanly and does not affect ssh sessions.
