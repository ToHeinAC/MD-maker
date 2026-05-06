# Architecture

## Goals
- Convert a dropped PDF or image into structured Markdown using a local Ollama vision model.
- Keep the implementation small, dependency-light, and on-prem.

## Module responsibilities

- **`src/app.py`** — Streamlit-only concerns: layout, file upload, model picker, DPI slider, progress, result tabs, download, safe-exit button. No prompt strings.
- **`src/models.py`** — single source of truth for the `{label → ollama tag}` map and the per-model prompt branching inside `convert_image`.
- **`src/prompts.py`** — prompt constants only, per project rule (CLAUDE.md §5.3).
- **`src/pdf_utils.py`** — pure functions usable in any context (CLI, tests, notebook).

## Why per-page calls
Vision models receive a single image per request. A multi-page PDF is rasterized to N images and processed sequentially; the page boundary is preserved as `\n\n---\n\n` in the joined output so the user can locate any page in the resulting `.md`.

## DPI tradeoff
- 72–100 dpi: fast, fine for clean print.
- 150 dpi (default): good balance for typical documents.
- 200–300 dpi: dense small-print or scans; slower and produces larger images that may stress the model context.

## Why no abstraction over models
Two prompt branches (`deepseek-ocr` vs `gemma4`) is one `if`. A Strategy/Registry pattern would add files for no benefit — the entire routing is ~10 lines.

## Safe exit
Per global CLAUDE.md, the app exposes a button that runs `lsof -ti:8521 | xargs -r kill -9`. The port is hardcoded to the run port (8521), not derived from `os.getpid()`'s parent — this means it kills the streamlit server cleanly and does not affect ssh sessions.
