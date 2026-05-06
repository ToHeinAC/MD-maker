"""Model registry and per-model Ollama call routing."""

import ollama
from PIL import Image

from pdf_utils import image_to_base64
from prompts import DEEPSEEK_PROMPT, REWRITE_PROMPT, SYSTEM_PROMPT, USER_PROMPT

AVAILABLE_MODELS: dict[str, str] = {
    "DeepSeek-OCR 3B (fast, MIT)": "deepseek-ocr:3b",
    "Gemma 4 E4B (fast, general)": "gemma4:e4b",
    "Gemma 4 E2B (ultra-light)": "gemma4:e2b",
}

DEFAULT_MODEL_LABEL = "DeepSeek-OCR 3B (fast, MIT)"
DEFAULT_REWRITE_MODEL_LABEL = "Gemma 4 E4B (fast, general)"


def convert_image(model_id: str, pil_image: Image.Image) -> str:
    img_b64 = image_to_base64(pil_image)
    if model_id.startswith("deepseek-ocr"):
        messages = [
            {"role": "user", "content": DEEPSEEK_PROMPT, "images": [img_b64]},
        ]
    else:
        # Gemma 4 does not honor a system role — merge instructions into user message.
        messages = [
            {
                "role": "user",
                "content": f"{SYSTEM_PROMPT}\n\n{USER_PROMPT}",
                "images": [img_b64],
            },
        ]
    response = ollama.chat(model=model_id, messages=messages, options={"temperature": 0})
    return response["message"]["content"]


def rewrite_text(model_id: str, text: str) -> str:
    """Reformat already-extracted PDF text into Markdown without altering wording."""
    response = ollama.chat(
        model=model_id,
        messages=[{"role": "user", "content": REWRITE_PROMPT + text}],
        options={"temperature": 0},
    )
    return response["message"]["content"]
