# Models

The UI offers three on-prem Ollama models. DeepSeek-OCR is the only vision-capable model and is the default OCR choice. Gemma 4 variants are **text-only** and are used solely for the PDF text-rewrite path.

| Label | Tag | Size | License | Vision? | Role |
|---|---|---|---|---|---|
| DeepSeek-OCR 3B (fast, MIT) — default | `deepseek-ocr:3b` | ~6.7 GB | MIT | Yes | OCR / image conversion |
| Gemma 4 E4B (fast, general) | `gemma4:e4b` | ~9.6 GB | Apache-2.0 | No | PDF text rewrite only |
| Gemma 4 E2B (ultra-light) | `gemma4:e2b` | ~7.2 GB | Apache-2.0 | No | PDF text rewrite only |

## Vision guard

`models.VISION_MODELS` is a `frozenset` of Ollama tags that accept an `images` payload. `convert_image()` raises `ValueError` immediately if the selected OCR model is not in this set — Ollama silently drops images for text-only models, producing hallucinated output with no error.

## Prompt-format quirks

### DeepSeek-OCR
- Expects a **short, punctuated prompt** on its own line after the image. Verbose multi-sentence instructions degrade output quality.
- The `<|grounding|>` token activates layout-aware OCR mode; omitting it produces inferior structure.
- Effective prompt: `<|grounding|>Convert the document to markdown.`
- Does not honor a `system` role — instruction goes in the user message only.
- Temperature is baked into model params at 0.

### Gemma 4
- Text-only; not eligible as OCR model. Used only for `rewrite_text()` (PDF text → Markdown reformatting).

The single `if model_id.startswith("deepseek-ocr")` branch in `convert_image` handles the only vision-capable model.

## Pulling

```bash
ollama pull deepseek-ocr:3b
ollama pull gemma4:e4b
ollama pull gemma4:e2b
```

DeepSeek-OCR requires Ollama ≥ v0.13.0.
