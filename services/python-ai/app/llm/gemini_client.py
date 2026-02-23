from __future__ import annotations

import logging

from google import genai


class GeminiClient:
    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout_seconds: float) -> None:
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required")
        self.model = model
        # google-genai HttpOptions expects milliseconds; convert seconds -> ms
        timeout_ms = int(timeout_seconds * 1000)
        self._client = genai.Client(api_key=api_key, http_options={"timeout": timeout_ms})

    def generate(self, prompt: str, timeout_seconds: int) -> str:
        logger = logging.getLogger(__name__)
        response = self._client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        text = getattr(response, "text", None)
        if text:
            logger.info("gemini_response model=%s chars=%s", self.model, len(text))
            return text
        if getattr(response, "candidates", None):
            text = response.candidates[0].content.parts[0].text
            logger.info("gemini_response model=%s chars=%s", self.model, len(text))
            return text
        raise RuntimeError("Gemini response missing output text")
