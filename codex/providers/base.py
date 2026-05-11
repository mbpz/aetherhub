from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate code from prompt"""
        pass
