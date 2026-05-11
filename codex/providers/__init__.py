"""LLM Provider interface and adapters"""
from codex.providers.base import LLMClient
from codex.providers.deepseek import DeepSeekAdapter
from codex.providers.openai import OpenAIAdapter


def get_llm_client() -> LLMClient:
    """Factory function to get LLM client based on LLM_PROVIDER env var"""
    import os
    provider = os.getenv("LLM_PROVIDER", "deepseek")
    if provider == "openai":
        return OpenAIAdapter()
    return DeepSeekAdapter()


__all__ = ["LLMClient", "DeepSeekAdapter", "OpenAIAdapter", "get_llm_client"]