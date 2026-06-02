# MD-maker

Drop a PDF, DOCX or image, get a well-structured Markdown file. Runs 100% locally via [Ollama](https://ollama.com) vision models. Apache-2.0 licensed.

## Quick start

```bash
# 1. Install Ollama and pull at least the default model
ollama pull deepseek-ocr:3b
# Optional: ollama pull gemma4:e4b ; ollama pull gemma4:e2b

# 2. Install Python deps
uv sync

# 3. Run the app
uv run streamlit run src/app.py --server.port 8521
```

Open <http://localhost:8521>, drag in a PDF, DOCX or image, click **📖 Convert to Markdown**, then **👁 Show result** and **⬇️ Download .md** (all in the left panel). PDFs route digital-text pages through a fast rewrite model and only OCR scanned pages — a status box shows which path each page took. DOCX files are converted directly to Markdown (no LLM); legacy `.doc` must be re-saved as `.docx` first.

## Models

| Label (UI) | Ollama tag | License | Role |
|---|---|---|---|
| DeepSeek-OCR 3B (fast, MIT) — default | `deepseek-ocr:3b` | MIT | OCR (vision) |
| Gemma 4 E4B (fast, general) | `gemma4:e4b` | Apache-2.0 | PDF text rewrite |
| Gemma 4 E2B (ultra-light) | `gemma4:e2b` | Apache-2.0 | PDF text rewrite |

DeepSeek-OCR is the only vision-capable model and is required for image/scanned-page OCR. Gemma 4 variants are text-only and used only to reformat already-extracted PDF text. DeepSeek-OCR requires Ollama ≥ v0.13.0.

## Documentation

- [IMPLEMENTATION.md](IMPLEMENTATION.md) — module map and dataflow
- [docs/architecture.md](docs/architecture.md) — design rationale
- [docs/models.md](docs/models.md) — per-model prompt quirks

## License

Apache-2.0 — see [LICENSE](LICENSE).
