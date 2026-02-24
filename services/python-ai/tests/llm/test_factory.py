from llm.factory import load_llm_client


class StubProvider:
    name = "stub"

    def __init__(self, *args, **kwargs):
        self.model = kwargs.get("model", "stub-model")

    def generate(self, prompt: str, timeout_seconds: int) -> str:
        raise RuntimeError("not used")


def test_load_openai_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    client = load_llm_client(provider_override=None, openai_cls=StubProvider, gemini_cls=StubProvider)
    assert client.provider_name == "stub"


def test_load_gemini_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GOOGLE_API_KEY", "test")
    client = load_llm_client(provider_override=None, openai_cls=StubProvider, gemini_cls=StubProvider)
    assert client.provider_name == "stub"
