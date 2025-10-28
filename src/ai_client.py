"""AI client abstraction and OpenAI implementation.

This module defines a small, testable interface for text-generation clients
and provides an OpenAI-backed implementation. By depending on the interface
instead of a concrete client we keep code testable and follow Dependency
Inversion (the D in SOLID).
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any

from openai import OpenAI


class AIClient(ABC):
    """Abstract interface for a text-generation client."""

    @abstractmethod
    def generate(self, prompt: str, model: str = "gpt-4o-mini") -> str:
        """Generate text from the given prompt and return plain text.

        Implementations should return a human-readable string and hide
        vendor-specific response objects behind this simple contract.
        """


class OpenAIClient(AIClient):
    """OpenAI-backed AIClient implementation.

    This class is a thin adapter around the official OpenAI client used
    elsewhere in the project. It keeps the AI usage behind a small,
    stable interface so higher-level code (services) doesn't import
    the OpenAI SDK directly.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be provided via env or constructor")

        self._client = OpenAI(api_key=self.api_key)

    def generate(self, prompt: str, model: str = "gpt-4o-mini") -> str:
        # Use the Responses API like other modules in this repo.
        response = self._client.responses.create(model=model, input=prompt)

        # Best-effort extraction of human text from the response object.
        # The shape may vary; we support common patterns used in tests.
        output_parts: list[str] = []

        # Some SDK responses provide `output` with `message`/`content` items
        for item in getattr(response, "output", []) or []:
            # message-style outputs
            if getattr(item, "type", None) == "message":
                for content in getattr(item, "content", []) or []:
                    text = getattr(content, "text", None)
                    if text:
                        output_parts.append(text)

            # simple text fields
            if hasattr(item, "text") and getattr(item, "type", None) != "message":
                output_parts.append(item.text)

        # Fallback to a top-level helper if present (some SDK versions)
        if not output_parts and hasattr(response, "get_output_text"):
            try:
                text = response.get_output_text()
                if text:
                    output_parts.append(text)
            except Exception:
                pass

        # If still empty, stringify the response as last resort
        if not output_parts:
            return str(response)

        return "\n\n".join(output_parts)
