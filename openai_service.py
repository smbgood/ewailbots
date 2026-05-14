import time
from typing import Any, Dict, Optional

from openai import OpenAI

from config import Config


class OpenAIServiceError(Exception):
    """Raised when an OpenAI request fails after retries."""


class OpenAIService:
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or Config.OPENAI_API_KEY
        if not key:
            raise ValueError("OPENAI_API_KEY is not configured")

        self.client = OpenAI(api_key=key, timeout=Config.OPENAI_TIMEOUT_SECONDS)
        self.max_retries = max(0, int(Config.OPENAI_MAX_RETRIES))

    def create_conversation(self) -> str:
        conv = self.client.conversations.create()
        conv_id = getattr(conv, "id", None)
        if not conv_id:
            raise OpenAIServiceError("OpenAI conversation id missing")
        return conv_id

    def generate_text(
        self,
        *,
        message: str,
        instructions: str,
        model: str,
        temperature: float,
        max_output_tokens: Optional[int] = None,
        conversation_id: Optional[str] = None,
        previous_response_id: Optional[str] = None,
        store: Optional[bool] = None,
    ) -> Dict[str, Optional[str]]:
        if not message.strip():
            raise OpenAIServiceError("Message cannot be empty")

        kwargs: Dict[str, Any] = {
            "model": model,
            "input": message,
            "instructions": instructions,
            "temperature": temperature,
        }
        if isinstance(max_output_tokens, int):
            kwargs["max_output_tokens"] = max_output_tokens
        if store is not None:
            kwargs["store"] = bool(store)
        if previous_response_id:
            kwargs["previous_response_id"] = previous_response_id
        if conversation_id:
            kwargs["conversation"] = conversation_id

        response = self._call_with_retries("responses.create", kwargs)
        text = self.extract_output_text(response)
        if not text:
            raise OpenAIServiceError("OpenAI response did not include text output")

        return {
            "text": text,
            "response_id": getattr(response, "id", None),
            "conversation_id": conversation_id,
        }

    def generate_image(
        self,
        *,
        prompt: str,
        model: str,
        size: str,
        quality: str,
        output_format: str,
        moderation: str,
        background: str,
        n: int = 1,
    ) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "moderation": moderation,
            "background": background,
            "output_format": output_format,
            "response_format": "b64_json",
            "n": n,
        }
        response = self._call_with_retries("images.generate", kwargs)
        data = getattr(response, "data", None) or []
        if not data:
            raise OpenAIServiceError("No image data returned from OpenAI")
        return data[0]

    def extract_output_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if output_text:
            return str(output_text).strip()

        outputs = getattr(response, "output", None) or []
        for item in outputs:
            contents = getattr(item, "content", None) or []
            for content in contents:
                content_type = getattr(content, "type", None)
                if content_type in ("output_text", "text"):
                    value = getattr(content, "text", None) or getattr(content, "value", None)
                    if value:
                        return str(value).strip()
        return ""

    def _call_with_retries(self, op_name: str, kwargs: Dict[str, Any]) -> Any:
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                if op_name == "responses.create":
                    try:
                        return self.client.responses.create(**kwargs)
                    except TypeError:
                        # SDK compatibility fallback for conversation field naming.
                        if "conversation" in kwargs:
                            compat_kwargs = dict(kwargs)
                            compat_kwargs["conversation_id"] = compat_kwargs.pop("conversation")
                            return self.client.responses.create(**compat_kwargs)
                        raise
                if op_name == "images.generate":
                    return self.client.images.generate(**kwargs)
                raise OpenAIServiceError(f"Unsupported operation: {op_name}")
            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(0.5 * (attempt + 1))

        raise OpenAIServiceError(f"{op_name} failed: {last_error}")
