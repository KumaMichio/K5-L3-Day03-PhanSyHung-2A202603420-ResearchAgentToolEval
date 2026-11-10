from __future__ import annotations

import os

from providers.openai_provider import OpenAIProvider


class OllamaProvider(OpenAIProvider):
    """Local small models via Ollama's OpenAI-compatible endpoint (no API key needed).

    Also works with any other local OpenAI-compatible server (LM Studio, llama.cpp
    server, vLLM) by overriding OLLAMA_BASE_URL.
    """

    def __init__(self) -> None:
        super().__init__(
            api_key_env="OLLAMA_API_KEY",
            api_key_default="ollama",  # local server ignores the key, but the SDK requires one
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            default_model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
            # Small local models sometimes loop and never stop; Ollama has no default
            # cap, so one runaway answer can block an eval run for many minutes on CPU.
            max_tokens=int(os.getenv("OLLAMA_MAX_TOKENS", "512")),
        )
