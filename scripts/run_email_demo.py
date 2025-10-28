"""Run a small demo of EmailWriterService without contacting OpenAI.

This script loads `src/email_service.py` directly to avoid importing the
package-level `src` (which requires the openai package). It uses a
simple mock AI client that returns a JSON response, then prints the
parsed subject and body.
"""
from pathlib import Path
import importlib.util
import importlib.machinery
import json
import sys
import types

ROOT = Path(__file__).resolve().parents[1]

def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    # Register module early so that decorators (dataclass) can look up
    # the module during class creation.
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore
    return module


def main():
    # Create a lightweight 'src' package in sys.modules to avoid executing
    # the real package __init__ which imports heavy dependencies.
    if "src" not in sys.modules:
        src_pkg = types.ModuleType("src")
        src_pkg.__path__ = [str(ROOT / "src")]
        sys.modules["src"] = src_pkg

    # Provide a tiny stub of the openai module so importing ai_client.py
    # doesn't fail during the demo. This stub only needs to provide the
    # symbols referenced at import time.
    if "openai" not in sys.modules:
        openai_stub = types.ModuleType("openai")
        # Minimal OpenAI adapter stub
        class OpenAI:
            def __init__(self, api_key=None):
                self.api_key = api_key
                self.responses = types.SimpleNamespace(create=lambda **kw: types.SimpleNamespace(output=[]))

        class AuthenticationError(Exception):
            pass

        class RateLimitError(Exception):
            pass

        class APIError(Exception):
            pass

        openai_stub.OpenAI = OpenAI
        openai_stub.AuthenticationError = AuthenticationError
        openai_stub.RateLimitError = RateLimitError
        openai_stub.APIError = APIError
        sys.modules["openai"] = openai_stub

    # Load ai_client.py into sys.modules as 'src.ai_client'
    ai_client_mod = _load_module(ROOT / "src" / "ai_client.py", "src.ai_client")
    sys.modules["src.ai_client"] = ai_client_mod
    setattr(sys.modules["src"], "ai_client", ai_client_mod)

    # Now load email_service as 'src.email_service' which will import src.ai_client
    email_service = _load_module(ROOT / "src" / "email_service.py", "src.email_service")
    sys.modules["src.email_service"] = email_service
    EmailWriterService = email_service.EmailWriterService

    # Mock AI returns JSON with subject/body
    mock_response = json.dumps({
        "subject": "Interview Reschedule Request",
        "body": (
            "Dear Hiring Manager,\n\n"
            "I hope you are well. I need to reschedule our interview originally "
            "planned for Wednesday. Would it be possible to move it to next Monday "
            "at 10:00 AM? I apologize for any inconvenience and appreciate your "
            "flexibility.\n\n"
            "Best regards,\nSam"
        )
    })

    class MockAIClient:
        def __init__(self, response_text: str):
            self._response_text = response_text
        def generate(self, prompt: str, model: str = "gpt-4o-mini") -> str:
            return self._response_text

    client = MockAIClient(mock_response)
    service = EmailWriterService(client)

    instruction = "Write a professional email to reschedule an interview."
    email = service.write_email(instruction, tone="formal")

    print("SUBJECT:\n", email.subject)
    print("\nBODY:\n", email.body)


if __name__ == '__main__':
    main()
