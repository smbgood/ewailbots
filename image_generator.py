import base64
import os
import uuid
from typing import Dict, Any, Optional

from openai import OpenAI
from config import Config

_client = OpenAI(api_key=Config.OPENAI_API_KEY)


def _build_public_url(filename: str) -> Optional[str]:
    base = (Config.IMAGE_PUBLIC_BASE_URL or "").strip()
    if not base:
        return None
    return f"{base.rstrip('/')}/{filename}"


def generate_image(prompt: str, size: Optional[str] = None, quality: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
    if not Config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured")

    selected_model = model or Config.OPENAI_IMAGE_MODEL or "gpt-image-1"
    selected_size = size or Config.OPENAI_IMAGE_SIZE or "1024x1024"
    selected_quality = quality or Config.OPENAI_IMAGE_QUALITY or "standard"

    use_upload = bool(Config.IMAGE_UPLOAD_DIR and Config.IMAGE_PUBLIC_BASE_URL)
    response_format = "b64_json" if use_upload else "url"

    kwargs: Dict[str, Any] = {
        "model": selected_model,
        "prompt": prompt,
        "size": selected_size,
        "quality": selected_quality,
        "n": 1,
        "response_format": response_format,
    }

    resp = _client.images.generate(**kwargs)
    data = getattr(resp, "data", None) or []
    first = data[0] if data else None
    if not first:
        raise ValueError("No image data returned from OpenAI")

    result: Dict[str, Any] = {
        "image_url": None,
        "image_path": None,
        "image_prompt": prompt,
        "source": None,
    }

    if use_upload and getattr(first, "b64_json", None):
        raw = base64.b64decode(first.b64_json)
        os.makedirs(Config.IMAGE_UPLOAD_DIR, exist_ok=True)
        filename = f"generated_{uuid.uuid4().hex[:12]}.png"
        path = os.path.join(Config.IMAGE_UPLOAD_DIR, filename)
        with open(path, "wb") as handle:
            handle.write(raw)
        public_url = _build_public_url(filename)
        result.update({"image_url": public_url, "image_path": path, "source": "uploaded"})
    else:
        url = getattr(first, "url", None)
        if url:
            result.update({"image_url": url, "source": "openai_url"})
        elif getattr(first, "b64_json", None):
            raw = base64.b64decode(first.b64_json)
            fallback_dir = Config.IMAGE_UPLOAD_DIR or "."
            os.makedirs(fallback_dir, exist_ok=True)
            filename = f"generated_{uuid.uuid4().hex[:12]}.png"
            path = os.path.join(fallback_dir, filename)
            with open(path, "wb") as handle:
                handle.write(raw)
            public_url = _build_public_url(filename)
            result.update({"image_url": public_url, "image_path": path, "source": "local_file"})

    revised_prompt = getattr(first, "revised_prompt", None)
    if revised_prompt:
        result["revised_prompt"] = revised_prompt

    return result
