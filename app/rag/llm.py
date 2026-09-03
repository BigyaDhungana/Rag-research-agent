import time

from abc import ABC, abstractmethod

from app.core.config import settings

from langfuse import observe, get_client


class LLMProviderError(Exception):
    """Raised when the underlying LLM call fails after all retries."""


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Return the model's raw text response for a fully-built prompt."""
        raise NotImplementedError


class GeminiLLMProvider(LLMProvider):
    _RETRYABLE_STATUS_CODES = {503, 429}

    def __init__(self):
        from google import genai

        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    @observe(name="llm_generate", as_type="generation")
    def generate(
        self, prompt: str, max_retries: int = 3, base_delay: float = 2.0
    ) -> str:
        from google.genai import errors as genai_errors

        langfuse = get_client()
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                )
                usage = getattr(response, "usage_metadata", None)
                if usage is not None:
                    langfuse.update_current_generation(
                        model=self._model,
                        output=response.text,
                        usage_details={
                            "input": getattr(usage, "prompt_token_count", None),
                            "output": getattr(usage, "candidates_token_count", None),
                            "total": getattr(usage, "total_token_count", None),
                        },
                    )

                return response.text

            except genai_errors.ServerError as e:
                last_error = e
                status_code = getattr(e, "status_code", None)
                if (
                    status_code not in self._RETRYABLE_STATUS_CODES
                    or attempt == max_retries
                ):
                    raise LLMProviderError(f"Gemini call failed: {e}") from e
                time.sleep(base_delay * (2**attempt))

        raise LLMProviderError(
            f"Gemini call failed after {max_retries + 1} attempts: {last_error}"
        )


_provider: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    global _provider
    if _provider is None:
        _provider = GeminiLLMProvider()
    return _provider
