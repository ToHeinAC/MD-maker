# MD-maker

Drop a PDF or image, get a well-structured Markdown file. Runs 100% locally via [Ollama](https://ollama.com) vision models. Apache-2.0 licensed.

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

Open <http://localhost:8521>, drag in a PDF or image, click **Convert**, download the `.md`.

## Models

| Label (UI) | Ollama tag | License |
|---|---|---|
| DeepSeek-OCR 3B (fast, MIT) — default | `deepseek-ocr:3b` | MIT |
| Gemma 4 E4B (fast, general) | `gemma4:e4b` | Apache-2.0 |
| Gemma 4 E2B (ultra-light) | `gemma4:e2b` | Apache-2.0 |

DeepSeek-OCR requires Ollama ≥ v0.13.0.

## Documentation

- [IMPLEMENTATION.md](IMPLEMENTATION.md) — module map and dataflow
- [docs/architecture.md](docs/architecture.md) — design rationale
- [docs/models.md](docs/models.md) — per-model prompt quirks

## License

Apache-2.0 — see [LICENSE](LICENSE).
