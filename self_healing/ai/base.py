"""
Khmer Translator AI — Abstract AI Provider Interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseAIProvider(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if required API credentials and dependencies are present."""
        pass

    @abstractmethod
    def generate_analysis(self, prompt: str) -> Optional[dict[str, Any]]:
        """Sends the diagnostic prompt to the AI provider and returns structured JSON."""
        pass
