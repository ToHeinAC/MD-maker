# IMPLEMENTATION

Compact reference for the current implementation state. Deeper details live under [docs/](docs/).

## Module map

| File | Responsibility |
|---|---|
| `src/app.py` | Streamlit UI, file upload, page preview, convert button, download, safe-exit. |
| `src/models.py` | `AVAILABLE_MODELS`, `DEFAULT_MODEL_LABEL`, `convert_image()` — routes prompts per model. |
| `src/prompts.py` | All prompt strings (`SYSTEM_PROMPT`, `USER_PROMPT`, `DEEPSEEK_PROMPT`). |
| `src/pdf_utils.py` | `pdf_to_images()`, `image_to_base64()` — pure helpers, no Streamlit. |

## Dataflow

```
upload (PDF/image) → bytes
    ├── PDF → pdf_to_images(bytes, dpi)  → [PIL.Image, …]
    └── image → [PIL.Image]
for each page:
    image → base64 → ollama.chat(model, messages) → markdown
join with "\n\n---\n\n" → display (Raw / Rendered tabs) + download .md
```

## Per-model prompt routing (`models.convert_image`)

- `deepseek-ocr:*` → single user message with `<|grounding|>` prefix; no system role. Temperature is fixed at 0 in model params.
- `gemma4:*` → Gemma does not honor a system role; `SYSTEM_PROMPT` and `USER_PROMPT` are concatenated into one user message.

See [docs/models.md](docs/models.md).

## Config knobs

- **Model** — selectbox; default `DeepSeek-OCR 3B`.
- **DPI** — 72–300, default 150 (PDF rasterization).
- **Port** — hardcoded to 8521 (matches CLAUDE.md and the safe-exit button).
- **`OLLAMA_HOST`** — env var, default `http://localhost:11434`. Loaded from `.env` if present.

## Run

```bash
uv run streamlit run src/app.py --server.port 8521
```

## Out of scope (today)

Tests, batch CLI, async/streaming, output caching, retries, auth.
