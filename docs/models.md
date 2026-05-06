# Models

The UI offers three on-prem Ollama vision models. DeepSeek-OCR is the default.

| Label | Tag | Size | License | Prompt format |
|---|---|---|---|---|
| DeepSeek-OCR 3B (fast, MIT) — default | `deepseek-ocr:3b` | ~6.7 GB | MIT | `<\|grounding\|>` user-only; temp fixed at 0 |
| Gemma 4 E4B (fast, general) | `gemma4:e4b` | ~9.6 GB | Apache-2.0 | No system role — merge into user |
| Gemma 4 E2B (ultra-light) | `gemma4:e2b` | ~7.2 GB | Apache-2.0 | No system role — merge into user |

## Prompt-format quirks

### DeepSeek-OCR
- Uses a dedicated `<|grounding|>` token to enter document-OCR mode.
- Does not honor a `system` role — instructions go in the user message.
- Temperature is baked into the model params at 0; no need (and no effect) to override.

### Gemma 4
- Multimodal but does not honor a `system` role in chat. Instructions merged into the user message produce reliable behavior.

These two quirks are the only reason `models.convert_image` branches on model id.

## Pulling

```bash
ollama pull deepseek-ocr:3b
ollama pull gemma4:e4b
ollama pull gemma4:e2b
```

DeepSeek-OCR requires Ollama ≥ v0.13.0.
