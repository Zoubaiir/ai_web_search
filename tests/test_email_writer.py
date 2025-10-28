"""Unit tests for the EmailWriterService.

We use a simple mock AI client to keep tests fast and hermetic.
"""
from __future__ import annotations

from src.email_service import EmailWriterService, Email
from src.ai_client import AIClient


class MockAIClient(AIClient):
    def __init__(self, response_text: str):
        self._response_text = response_text

    def generate(self, prompt: str, model: str = "gpt-4o-mini") -> str:
        # In a real test we could assert the prompt contains expected
        # guidance; keep it simple here.
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
