import base64
import os
import uuid
from typing import Dict, Any, Optional

from config import Config
from openai_service import OpenAIService

_service = OpenAIService(api_key=Config.OPENAI_API_KEY)


def _build_public_url(filename: str) -> Optional[str]:
    base = (Config.IMAGE_PUBLIC_BASE_URL or "").strip()
    if not base:
        return None
    return f"{base.rstrip('/')}/{filename}"


def generate_image(prompt: str, size: Optional[str] = None, quality: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
    if not Config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured")

    selected_model = model or Config.OPENAI_IMAGE_MODEL or "gpt-image-2"
    selected_size = size or Config.OPENAI_IMAGE_SIZE or "1024x1024"
    selected_quality = quality or Config.OPENAI_IMAGE_QUALITY or "medium"

    first = _service.generate_image(
        prompt=prompt,
        model=selected_model,
        size=selected_size,
        quality=selected_quality,
        output_format=Config.OPENAI_IMAGE_OUTPUT_FORMAT,
        moderation=Config.OPENAI_IMAGE_MODERATION,
        background=Config.OPENAI_IMAGE_BACKGROUND,
        n=1,
    )

    result: Dict[str, Any] = {
        "image_url": None,
        "image_path": None,
        "image_prompt": prompt,
        "source": None,
    }

    b64_json = getattr(first, "b64_json", None)
    if b64_json:
        raw = base64.b64decode(b64_json)
        os.makedirs(Config.IMAGE_UPLOAD_DIR, exist_ok=True)
        filename = f"generated_{uuid.uuid4().hex[:12]}.png"
        path = os.path.join(Config.IMAGE_UPLOAD_DIR, filename)
        with open(path, "wb") as handle:
            handle.write(raw)
        public_url = _build_public_url(filename)
        result.update(
            {
                "image_url": public_url,
                "image_path": path,
                "source": "stored_file",
            }
        )
    else:
        # Fallback for providers/accounts that only return hosted URLs.
        url = getattr(first, "url", None)
        if url:
            result.update({"image_url": url, "source": "openai_url"})
        else:
            raise ValueError("Image generation succeeded but no usable image payload was returned")

    revised_prompt = getattr(first, "revised_prompt", None)
    if revised_prompt:
        result["revised_prompt"] = revised_prompt

    return result
