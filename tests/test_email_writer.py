"""Unit tests for the EmailWriterService.

We use a simple mock AI client to keep tests fast and hermetic.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

# Load modules by file path to avoid importing the package-level `src` which
# pulls in heavy dependencies at import time (OpenAI). This keeps tests
# hermetic and fast.
ROOT = Path(__file__).resolve().parents[1]

def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    # Register module early so decorators like @dataclass can resolve
    # the module during class creation.
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore
    return module


email_service = _load_module(ROOT / "src" / "email_service.py", "email_service")
EmailWriterService = email_service.EmailWriterService
Email = email_service.Email


class MockAIClient:
    def __init__(self, response_text: str):
        self._response_text = response_text

    def generate(self, prompt: str, model: str = "gpt-4o-mini") -> str:
        return self._response_text


def test_write_email_json_response():
    # AI returns a JSON object (the preferred structured response)
    ai_text = '{"subject": "Interview reschedule", "body": "Dear Ms. Lee,\n\nI need to reschedule our interview to next Tuesday at 10am.\n\nRegards,\nSam"}'
    client = MockAIClient(ai_text)
    service = EmailWriterService(client)

    email = service.write_email("Write a professional email to reschedule an interview.")

    assert isinstance(email, Email)
    assert "Interview reschedule" in email.subject
    assert "Dear Ms. Lee" in email.body


def test_write_email_plain_text_response():
    # AI returns plain text with a Subject: line - service should parse it
    ai_text = "Subject: Reschedule Interview\n\nDear Hiring Team,\n\nI would like to reschedule...\n"
    client = MockAIClient(ai_text)
    service = EmailWriterService(client)

    email = service.write_email("Reschedule interview")

    assert email.subject.startswith("Reschedule Interview")
    assert "Dear Hiring Team" in email.body
