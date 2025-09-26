from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Optional, Dict, Any
import hashlib
import time


class LLMError(Exception):
    pass


class LLMTimeout(LLMError):
    pass


class LLMClient(Protocol):
    def generate(self, prompt: str, *, timeout: float | None = None, max_output: int | None = None) -> str:
        ...


@dataclass
class OllamaClient:
    model: str
    timeout_seconds: int = 8
    max_output_chars: int = 2000

    def generate(self, prompt: str, *, timeout: float | None = None, max_output: int | None = None) -> str:
        # Lazy import to keep dependency surface minimal
        from src.llm.providers import ollama_generate
        to = timeout or self.timeout_seconds
        start = time.time()
        raw = ollama_generate(self.model, prompt)
        elapsed = time.time() - start
        if elapsed > to:
            raise LLMTimeout(
                f"generation exceeded timeout: {elapsed:.2f}s > {to}s")
        cap = max_output or self.max_output_chars
        if len(raw) > cap:
            return raw[:cap]
        return raw


def hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def build_client(cfg: Dict[str, Any]):
    if not cfg.get("enabled"):
        return None
    provider = cfg.get("provider", "ollama")
    if provider == "ollama":
        return OllamaClient(model=cfg.get("model", "mistral:latest"),
                            timeout_seconds=cfg.get("timeout_seconds", 8),
                            max_output_chars=cfg.get("max_output_chars", 2000))
    raise ValueError(f"unsupported LLM provider: {provider}")
