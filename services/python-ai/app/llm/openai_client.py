from __future__ import annotations

from openai import OpenAI


class OpenAIClient:
    name = "openai"

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required")
        self.model = model
        self._client = OpenAI(api_key=api_key)

    def generate(self, prompt: str, timeout_seconds: int) -> str:
        response = self._client.responses.create(
            model=self.model,
            input=prompt,
            timeout=timeout_seconds,
        )
        text = getattr(response, "output_text", None)
        if text:
            return text
        if getattr(response, "output", None):
            return response.output[0].content[0].text
        raise RuntimeError("OpenAI response missing output text")
