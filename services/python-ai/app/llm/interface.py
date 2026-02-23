from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Iterable, Protocol

from pydantic import BaseModel, Field, ValidationError, field_validator


class AnalysisResult(BaseModel):
    tickers: list[str] = Field(default_factory=list)
    sentiment: str
    confidence: float
    reasoning_summary: str

    model_config = {
        "extra": "forbid",
        "strict": True,
    }

    @field_validator("tickers")
    @classmethod
    def _validate_tickers(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError("tickers must be strings")
            item = item.strip().upper()
            if not item:
                raise ValueError("tickers must be non-empty")
            cleaned.append(item)
        return list(dict.fromkeys(cleaned))

    @field_validator("sentiment")
    @classmethod
    def _validate_sentiment(cls, value: str) -> str:
        allowed = {"positive", "neutral", "negative"}
        if value not in allowed:
            raise ValueError("sentiment must be positive|neutral|negative")
        return value

    @field_validator("confidence")
    @classmethod
    def _validate_confidence(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("confidence must be between 0 and 1")
        return value

    @field_validator("reasoning_summary")
    @classmethod
    def _validate_summary(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("reasoning_summary must be a string")
        summary = value.strip()
        if not summary:
            raise ValueError("reasoning_summary must be non-empty")
        if len(summary) > 280:
            raise ValueError("reasoning_summary must be <= 280 chars")
        return summary


@dataclass(frozen=True)
class LLMRunAttempt:
    prompt: str
    output: str | None
    error: str | None


class LLMProvider(Protocol):
    name: str
    model: str

    def generate(self, prompt: str, timeout_seconds: int) -> str:
        ...


class LLMAnalysisError(RuntimeError):
    def __init__(self, message: str, attempts: list[LLMRunAttempt]):
        super().__init__(message)
        self.attempts = attempts


class ProviderError(RuntimeError):
    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.code = code


def build_prompt(input_text: str) -> str:
    return (
        "You are a financial news analyst. "
        "Analyze the news below and output ONLY valid JSON with keys: "
        "tickers (list of strings), sentiment (positive|neutral|negative), "
        "confidence (0..1), reasoning_summary (<=280 chars). "
        "No markdown, no extra text.\n\n"
        f"NEWS:\n{input_text}\n"
    )


def build_retry_prompt(input_text: str) -> str:
    template = (
        '{"tickers":["AAPL"],"sentiment":"neutral","confidence":0.5,'
        '"reasoning_summary":"Short reason."}'
    )
    return (
        "STRICT MODE: Output ONLY JSON matching this exact schema. "
        "Do not include any extra keys, markdown, or commentary.\n"
        f"TEMPLATE:\n{template}\n\n"
        f"NEWS:\n{input_text}\n"
    )


def parse_analysis_json(text: str) -> AnalysisResult:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object")
    return AnalysisResult.model_validate(payload)


class LLMClient:
    def __init__(self, provider: LLMProvider, timeout_seconds: int, max_retries: int):
        self._provider = provider
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self.last_attempts: list[LLMRunAttempt] = []

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def model(self) -> str:
        return self._provider.model

    def analyze_news(self, input_text: str) -> AnalysisResult:
        self.last_attempts = []
        prompts: Iterable[str] = [build_prompt(input_text)]
        retry_prompt = build_retry_prompt(input_text)
        logger = logging.getLogger(__name__)

        for attempt in range(self._max_retries + 1):
            if attempt > 0:
                time.sleep(2)
            prompt = prompts[0] if attempt == 0 else retry_prompt
            output: str | None = None
            error: str | None = None
            try:
                logger.info(
                    "llm_attempt provider=%s model=%s attempt=%s",
                    self.provider_name,
                    self.model,
                    attempt + 1,
                )
                output = self._provider.generate(prompt, self._timeout_seconds)
                result = parse_analysis_json(output)
                self.last_attempts.append(LLMRunAttempt(prompt=prompt, output=output, error=None))
                logger.info(
                    "llm_attempt_success provider=%s model=%s attempt=%s",
                    self.provider_name,
                    self.model,
                    attempt + 1,
                )
                return result
            except ProviderError as exc:
                error = f"provider_error:{exc.code}:{exc}" if exc.code else f"provider_error:{exc}"
                self.last_attempts.append(LLMRunAttempt(prompt=prompt, output=output, error=error))
                logger.warning(
                    "llm_attempt_failed provider=%s model=%s attempt=%s error=%s output_snippet=%s",
                    self.provider_name,
                    self.model,
                    attempt + 1,
                    error,
                    (output or "")[:200],
                )
                if exc.code == "insufficient_quota":
                    raise LLMAnalysisError("LLM analysis failed", self.last_attempts)
                continue
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                error = str(exc)
            except Exception as exc:  # noqa: BLE001
                error = f"provider_error: {exc}"

            self.last_attempts.append(LLMRunAttempt(prompt=prompt, output=output, error=error))
            logger.warning(
                "llm_attempt_failed provider=%s model=%s attempt=%s error=%s output_snippet=%s",
                self.provider_name,
                self.model,
                attempt + 1,
                error,
                (output or "")[:200],
            )

        raise LLMAnalysisError("LLM analysis failed", self.last_attempts)
