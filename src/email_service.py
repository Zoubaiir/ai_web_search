"""Email writing service following SOLID principles.

Single Responsibility: this module only knows how to build and format
emails by delegating generation to an AI client.
Dependency Inversion: the service depends on the AIClient abstraction.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional
import re

from src.ai_client import AIClient


@dataclass
class Email:
    subject: str
    body: str
    tone: str = "formal"


class EmailWriterService:
    """Service that uses an AI client to generate polished emails.

    Responsibilities:
    - Construct a clear, testable prompt
    - Ask the AI client to generate the content
    - Parse the output into an Email value object
    """

    def __init__(self, ai_client: AIClient, model: str = "gpt-4o-mini"):
        self.ai_client = ai_client
        self.model = model

    def write_email(self, instruction: str, tone: str = "formal") -> Email:
        """Generate an email for the given instruction and tone.

        The AI is asked to return a small JSON object with `subject` and
        `body` fields. This makes parsing robust and keeps responsibilities
        separated (generation vs parsing).
        """
        prompt = self._build_prompt(instruction, tone)
        raw = self.ai_client.generate(prompt, model=self.model)

        subject, body = self._parse_ai_output(raw)
        return Email(subject=subject, body=body, tone=tone)

    def _build_prompt(self, instruction: str, tone: str) -> str:
        # Keep the prompt focused and ask for JSON so parsing is simple.
        return (
            "You are an assistant that writes professional emails. "
            "Given a short instruction, produce a JSON object with keys: 'subject' and 'body'. "
            "The 'subject' should be a short email subject line. The 'body' should be a polished email in a formal tone. "
            "Return only valid JSON, with no markdown or code fences. Do not include ``` or any extra text. "
            f"Instruction: {instruction}\nTone: {tone}\n"
        )

    def _parse_ai_output(self, raw: str) -> tuple[str, str]:
        """Try to parse AI output as JSON; fall back to heuristic parsing.

        Returns (subject, body).
        """
        raw = raw.strip()

        # 1) Attempt direct JSON parse
        try:
            data = json.loads(raw)
            subject = data.get("subject", "")
            body = data.get("body", "")
            if subject or body:
                return subject.strip(), body.strip()
        except Exception:
            pass

        # 2) Strip common markdown fences and language labels, then retry JSON
        #    Examples: ```json ... ```  or ``` ... ```
        def _strip_fences(text: str) -> str:
            # Remove triple backtick fences and optional language tag
            text = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", text, flags=re.IGNORECASE | re.MULTILINE)
            text = re.sub(r"\s*```\s*$", "", text, flags=re.MULTILINE)
            return text.strip()

        unfenced = _strip_fences(raw)
        if unfenced != raw:
            try:
                data = json.loads(unfenced)
                subject = data.get("subject", "")
                body = data.get("body", "")
                if subject or body:
                    return subject.strip(), body.strip()
            except Exception:
                pass

        # 3) Extract the first JSON object substring and parse it
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if json_match:
            candidate = json_match.group(0)
            try:
                data = json.loads(candidate)
                subject = data.get("subject", "")
                body = data.get("body", "")
                if subject or body:
                    return subject.strip(), body.strip()
            except Exception:
                pass

        # Heuristic: look for lines starting with "Subject:" then the rest.
        lines = raw.splitlines()
        subject = ""
        body_lines: list[str] = []
        found_subject = False
        for i, line in enumerate(lines):
            if not found_subject and line.lower().startswith("subject:"):
                subject = line.split(":", 1)[1].strip()
                found_subject = True
                continue

            # Skip blank lines after subject
            if found_subject and line.strip() == "":
                continue

            body_lines.append(line)

        if not subject:
            # Fallback: if we can find a key-value style "\"subject\": \"...\"" in text
            subj_match = re.search(r'"subject"\s*:\s*"([\s\S]*?)"', raw, flags=re.IGNORECASE)
            if subj_match:
                subject = subj_match.group(1).strip()
            else:
                # Final fallback subject from first non-empty line
                first_line = next((ln for ln in lines if ln.strip()), "Email")
                subject = first_line.strip().strip("`")

        body = "\n".join(body_lines).strip()
        if not body:
            # Try to pull a body value if present in JSON-like text
            body_match = re.search(r'"body"\s*:\s*"([\s\S]*?)"\s*}', raw, flags=re.IGNORECASE)
            if body_match:
                body = body_match.group(1).encode('utf-8', 'ignore').decode('unicode_escape').strip()

        # Clean stray fences if any
        body = _strip_fences(body)
        return subject, body
