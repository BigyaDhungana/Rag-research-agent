from abc import ABC, abstractmethod

from app.core.config import settings


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Return the model's raw text response for a fully-built prompt."""
        raise NotImplementedError


class GeminiLLMProvider(LLMProvider):
    def __init__(self):
        from google import genai

        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    def generate(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        return response.text


_provider: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    global _provider
    if _provider is None:
        _provider = GeminiLLMProvider()
    return _provider
