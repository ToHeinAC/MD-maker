<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# I want to build a small python streamlit app that should be able to receive a file per drag\&drop, either a pdf or an image, and convert it into a well structured markdown file preserving the original content as much as possible. Restrictions: Must be using permissive (<= Apache 2.0) ollama llm runnable on premise on a edge device, say < 10GB model size. What are your recommendations for the llm selection (take also the newest ollama models into account) and the prompt to best achieve this?

Good — I have enough to write a comprehensive, technically precise answer with code. Let me now compose the full response with the Streamlit app code.

Here's a concise, opinionated guide covering model selection and a ready-to-use Streamlit app.

***

## Model Recommendations

Given your constraints (Apache 2.0 license, ≤10 GB, Ollama, edge device, document/image-to-markdown), here are the top candidates ranked by fit:


| Model | Ollama tag | Size | License | Vision | OCR Quality |
| :-- | :-- | :-- | :-- | :-- | :-- |
| **olmOCR-2 7B** *(top pick)* | `richardyoung/olmocr2:7b-q8` | ~8.85 GB | Apache 2.0 | ✅ | 🏆 Specialized (82.4 olmOCR-Bench) |
| **Gemma 4 E4B** *(best balance)* | `gemma4:e4b` | ~9.6 GB | Apache 2.0 | ✅ | 🟢 Good, fast |
| **Gemma 4 E2B** *(ultra-light)* | `gemma4:e2b` | ~7.2 GB | Apache 2.0 | ✅ | 🟡 Basic text only |
| **Qwen2.5-VL 7B** | `qwen2.5vl:7b` | ~5 GB | Apache 2.0 | ✅ | 🟢 Very good, DocVQA-strong |

**Primary recommendation: `olmOCR-2 7B`** — it's a Qwen2.5-VL-7B fine-tuned specifically for document OCR-to-markdown by the Allen Institute, licensed Apache 2.0, and scores 82.4 on olmOCR-Bench. It excels at tables, equations, and complex layouts. At 8.85 GB Q8, it fits your edge constraint.[^1][^2][^3]

**Second choice: `gemma4:e4b`** — Google's April 2026 release under Apache 2.0, 9.6 GB download, tight vision encoder integration with good OCR on headers and general content. Unique benefit: supports tool calling alongside vision.[^4][^5][^6][^7][^8]

> **Note:** Mistral Small 3.1 24B is Apache 2.0 and excellent at vision, but its Q4 quantization is ~15 GB  — it slightly exceeds your constraint and needs ≥32 GB RAM.[^9][^10][^11]

***

## PDF Handling Strategy

Since Ollama vision models receive images, not raw PDF bytes, you need to rasterize each PDF page to an image first using `PyMuPDF` (`fitz`). Each page is then sent as a base64-encoded image to the VLM. This is exactly what tools like `llama-scan` do with `qwen2.5vl:latest` as default.[^12][^13][^14]

***

## The Prompt

This is the most important tuning knob. Use a structured system + user prompt:

```
SYSTEM:
You are a precise document transcription assistant.
Your sole task is to convert the content of the provided document image
into well-structured Markdown, preserving the original structure faithfully.

Rules:
- Reproduce ALL text exactly as it appears — do not paraphrase or summarize.
- Use Markdown headings (#, ##, ###) that match the visual hierarchy.
- Render tables as proper Markdown tables (|col|col|).
- Preserve bullet/numbered lists exactly.
- Wrap code blocks in triple backticks with language hint if detectable.
- For mathematical expressions, use LaTeX notation: $...$ inline, $...$ block.
- For figures/diagrams with no extractable text, write: [Figure: <brief description>]
- Do NOT add explanatory text, preamble, or commentary.
- Output ONLY the Markdown content — nothing else.

USER:
Convert this document page to Markdown.
```

For olmOCR-2 specifically, the model was trained with a metadata-augmented prompt  — but the above generic prompt works well in Ollama without that overhead.[^15]

***

## Full Streamlit App

```python
# app.py
# Requirements: pip install streamlit ollama pymupdf pillow

import io
import base64
import streamlit as st
import ollama
import fitz  # PyMuPDF
from PIL import Image

# ── Config ──────────────────────────────────────────────────────────────────
AVAILABLE_MODELS = {
    "olmOCR-2 7B (best for docs)": "richardyoung/olmocr2:7b-q8",
    "Gemma 4 E4B (fast, general)": "gemma4:e4b",
    "Gemma 4 E2B (ultra-light)": "gemma4:e2b",
    "Qwen2.5-VL 7B (strong DocVQA)": "qwen2.5vl:7b",
}

SYSTEM_PROMPT = """You are a precise document transcription assistant.
Your sole task is to convert the content of the provided document image
into well-structured Markdown, preserving the original structure faithfully.

Rules:
- Reproduce ALL text exactly as it appears — do not paraphrase or summarize.
- Use Markdown headings (#, ##, ###) that match the visual hierarchy.
- Render tables as proper Markdown tables (|col|col|).
- Preserve bullet/numbered lists exactly.
- Wrap code blocks in triple backticks with a language hint if detectable.
- For mathematical expressions, use LaTeX: $...$ inline, $...$ block.
- For figures/diagrams with no extractable text, write: [Figure: <brief description>]
- Do NOT add explanatory text, preamble, or commentary.
- Output ONLY the Markdown content — nothing else."""

USER_PROMPT = "Convert this document page to Markdown."


# ── Helpers ─────────────────────────────────────────────────────────────────
def image_to_base64(pil_image: Image.Image) -> str:
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def pdf_to_images(pdf_bytes: bytes, dpi: int = 150) -> list[Image.Image]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        images.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
    return images


def process_image_with_ollama(model: str, pil_image: Image.Image) -> str:
    img_b64 = image_to_base64(pil_image)
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT,
                "images": [img_b64],
            },
        ],
    )
    return response["message"]["content"]


# ── UI ───────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Doc → Markdown", layout="wide")
st.title("📄 Document → Markdown Converter")
st.caption("Runs 100% locally via Ollama. Drop a PDF or image to convert.")

col_left, col_right = st.columns(2)

with col_left:
    model_label = st.selectbox("Model", list(AVAILABLE_MODELS.keys()))
    model_id = AVAILABLE_MODELS[model_label]
    st.caption(f"Ollama tag: `{model_id}`")

    dpi = st.slider("Render DPI (PDF only)", 72, 300, 150,
                    help="Higher = better OCR accuracy, slower processing.")

    uploaded = st.file_uploader(
        "Drop PDF or image here",
        type=["pdf", "png", "jpg", "jpeg", "webp", "tiff"],
        help="Drag & drop supported natively by Streamlit's file uploader.",
    )

with col_right:
    if uploaded:
        file_bytes = uploaded.read()
        is_pdf = uploaded.type == "application/pdf"

        if is_pdf:
            pages = pdf_to_images(file_bytes, dpi=dpi)
            st.info(f"PDF detected — {len(pages)} page(s) found.")
            preview_idx = st.number_input("Preview page", 1, len(pages), 1) - 1
            st.image(pages[preview_idx], caption=f"Page {preview_idx + 1}", use_container_width=True)
        else:
            pages = [Image.open(io.BytesIO(file_bytes)).convert("RGB")]
            st.image(pages[^0], caption="Uploaded image", use_container_width=True)

        if st.button("🚀 Convert to Markdown", type="primary"):
            all_md = []
            prog = st.progress(0, text="Processing…")

            for i, page_img in enumerate(pages):
                prog.progress((i) / len(pages), text=f"Processing page {i + 1}/{len(pages)}…")
                md = process_image_with_ollama(model_id, page_img)
                all_md.append(md)

            prog.progress(1.0, text="Done!")
            combined = "\n\n---\n\n".join(all_md)  # page separator for multi-page PDFs

            st.subheader("Result")
            tab_raw, tab_preview = st.tabs(["Raw Markdown", "Rendered Preview"])

            with tab_raw:
                st.code(combined, language="markdown")
                st.download_button(
                    "⬇️ Download .md",
                    data=combined.encode(),
                    file_name=uploaded.name.rsplit(".", 1)[^0] + ".md",
                    mime="text/markdown",
                )
            with tab_preview:
                st.markdown(combined)
```


***

## Key Design Decisions

- **PDF rasterization** at 150 DPI is a practical default — it's fast and gives the VLM enough resolution without hitting Ollama's image size limits. Raise to 200–300 DPI for dense small-print documents.[^15]
- **System prompt separation** — olmOCR-2 and Qwen2.5-VL both honor a system role. Gemma 4 requires all instructions in the user message  — you may need to merge both into the user role if using Gemma 4.[^2][^16]
- **Page separator `---`** keeps multi-page PDFs readable as a single Markdown file.
- **`st.file_uploader`** natively renders as a drag-and-drop zone in Streamlit — no custom JS needed.[^17]
- **Tab layout** (Raw | Rendered Preview) lets you validate formatting before downloading.


## Quick Start

```bash
# 1. Pull your model
ollama pull richardyoung/olmocr2:7b-q8   # primary recommendation

# 2. Install Python deps
pip install streamlit ollama pymupdf pillow

# 3. Run
streamlit run app.py
```

<span style="display:none">[^18][^19][^20][^21][^22][^23][^24][^25][^26][^27][^28][^29][^30][^31][^32][^33][^34][^35][^36][^37][^38][^39][^40][^41][^42][^43][^44][^45][^46][^47][^48][^49][^50][^51][^52][^53][^54][^55][^56]</span>

<div align="center">⁂</div>

[^1]: https://www.kdnuggets.com/top-7-open-source-ocr-models

[^2]: https://ollama.com/richardyoung/olmocr2

[^3]: https://deepinfra.com/allenai/olmOCR-2-7B-1025

[^4]: https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/

[^5]: https://help.apiyi.com/en/google-gemma-4-open-model-apache2-multimodal-guide-en.html

[^6]: https://www.promptquorum.com/local-llms/top-open-source-models-ollama

[^7]: https://www.gemma4.wiki/ollama/gemma-4-ollama-vision-guide

[^8]: https://avenchat.com/blog/run-gemma-4-in-ollama

[^9]: https://registry.ollama.ai/library/mistral-small3.1:24b

[^10]: https://huggingface.co/muranAI/Mistral-Small-3.1-24B-Instruct-2503-GGUF/raw/main/README.md

[^11]: https://docs.clore.ai/guides/guides_v2-es/modelos-de-lenguaje/mistral-small

[^12]: https://pypi.org/project/llama-scan/0.1.4/

[^13]: https://github.com/ngafar/llama-scan

[^14]: https://blog.csdn.net/weixin_37657487/article/details/149882386

[^15]: https://alpha-ollama.hf-mirror.com/Mungert/olmOCR-7B-0725-GGUF

[^16]: https://kenhuangus.substack.com/p/use-local-google-gemma-4-model-to

[^17]: https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader

[^18]: https://ollama.com/blog/multimodal-models

[^19]: https://www.aiforswes.com/p/understanding-open-model-licenses

[^20]: https://www.serverman.co.uk/ai/ollama/ollama-multimodal-vision-models/

[^21]: https://www.qnovi.de/en/blog/ocr-benchmarks-2025-the-best-open-source-models-in-a-practical-test/

[^22]: https://huggingface.co/blog/daya-shankar/open-source-llms

[^23]: https://www.serverman.co.uk/ai/ollama/best-ollama-models-for-vision/

[^24]: https://www.promptquorum.com/local-llms/multimodal-local-llms

[^25]: https://modal.com/blog/8-top-open-source-ocr-models-compared

[^26]: https://www.youtube.com/watch?v=YAgjtZKLVKo

[^27]: https://ollama.com/library/gpt-oss

[^28]: https://huggingface.co/allenai/olmOCR-7B-0825-FP8/raw/main/README.md

[^29]: https://www.youtube.com/watch?v=VGdkWXujMXs

[^30]: https://ollama.com/library/gemma4

[^31]: https://ollama.com/library/qwen2.5vl:7b

[^32]: https://ollama.com/richardyoung/olmocr2:7b-q8

[^33]: https://www.gemma4.wiki/ko/ollama/gemma-4-ollama-vision-guide

[^34]: https://localaimaster.com/models/qwen-2-5-7b

[^35]: https://ollama.com/library/qwen2.5vl:7b-q4_K_M

[^36]: https://ollama.com/pdevine/gemma4

[^37]: https://www.labellerr.com/blog/run-qwen2-5-vl-locally/

[^38]: https://discuss.streamlit.io/t/drag-and-drop-pdf-file-streamlit/59264

[^39]: https://www.youtube.com/watch?v=bvycomQHEVQ

[^40]: https://github.com/ChingWeiChan/ollama-streamlit-demo

[^41]: https://gbaian10.github.io/python_book/streamlit/ch01-03-file_upload.html

[^42]: https://decoder.sh/videos/llm-chat-app-in-python-w_-ollama_py-and-streamlit

[^43]: https://github.com/ollama/ollama-python

[^44]: https://www.youtube.com/watch?v=vwFR2bXXzTw

[^45]: https://www.youtube.com/watch?v=2fttxuaHlRQ

[^46]: https://mcp.csdn.net/691546215511483559e9cc92.html

[^47]: https://www.gemma4.wiki/guide/gemma-4-model-sizes-parameters-vram-requirements-ollama

[^48]: https://www.betterclaw.io/blog/openclaw-local-model-hardware

[^49]: https://ollama.com/library/mistral-small3.1

[^50]: https://ollama.com/library/command-r

[^51]: https://localllm.in/blog/ollama-vram-requirements-for-local-llms

[^52]: https://www.reddit.com/r/ollama/comments/1gwbl0k/what_are_the_minimum_hardware_requirements_to_run/

[^53]: https://www.gemma4.wiki/ollama/gemma-4-ollama-pull-command

[^54]: https://huggingface.co/allenai/olmOCR-7B-0225-preview-GGUF/discussions/2

[^55]: https://www.danilchenko.dev/posts/2026-04-07-run-gemma-4-locally-ollama-llama-cpp-vllm/

[^56]: https://www.kaggle.com/models/mistral-ai/mistral-small-3.1/

Simple update — just add the model to the dict and note its special prompt format. Here's what to change:

## Changes to the App

**1. Add to `AVAILABLE_MODELS` dict:**

```python
AVAILABLE_MODELS = {
    "olmOCR-2 7B (best for docs)":     "richardyoung/olmocr2:7b-q8",
    "DeepSeek-OCR 3B (fast, MIT)":     "deepseek-ocr:3b",         # ← add this
    "Gemma 4 E4B (fast, general)":     "gemma4:e4b",
    "Gemma 4 E2B (ultra-light)":       "gemma4:e2b",
    "Qwen2.5-VL 7B (strong DocVQA)":   "qwen2.5vl:7b",
}
```

**2. Replace the `process_image_with_ollama` function** with a model-aware version, because deepseek-ocr uses a dedicated `<|grounding|>` prompt token format  instead of a system/user split:

```python
def process_image_with_ollama(model: str, pil_image: Image.Image) -> str:
    img_b64 = image_to_base64(pil_image)

    # deepseek-ocr uses a special grounding-prompt format (no system role)
    if model.startswith("deepseek-ocr"):
        response = ollama.chat(
            model=model,
            messages=[{
                "role": "user",
                "content": "<|grounding|>Convert the document to markdown. "
                           "Preserve all headings, tables, lists, and structure faithfully.",
                "images": [img_b64],
            }],
        )
    else:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": USER_PROMPT, "images": [img_b64]},
            ],
        )
    return response["message"]["content"]
```

## deepseek-ocr:3b at a Glance

| Property | Value |
|---|---|
| Size | 6.7 GB (F16, 3.34B params)  |
| License | **MIT** (more permissive than Apache 2.0)  |
| Architecture | `deepseekocr` (custom VLM)  |
| Requires | Ollama ≥ v0.13.0  |
| Prompt style | `<\|grounding\|>` prefix, no system role  |
| Temperature | Fixed at 0 (built into model params)  |

It's a solid pick for edge devices with limited RAM — smaller than all other options at 6.7 GB and token-efficient by design . The `temperature: 0` baked into the model params also makes outputs more deterministic and stable for OCR tasks .

**Quick pull:**
```bash
ollama pull deepseek-ocr:3b
```

**FINAL DECISSION LLMs**
AVAILABLE_MODELS = {
    "DeepSeek-OCR 3B (fast, MIT)": "deepseek-ocr:3b", 
    "Gemma 4 E4B (fast, general)": "gemma4:e4b",
    "Gemma 4 E2B (ultra-light)": "gemma4:e2b",
}
with first as default