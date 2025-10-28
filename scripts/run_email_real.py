"""Run EmailWriterService using the real OpenAIClient and your `.env` key.

WARNING: This will make a real API request to OpenAI and may consume quota.
Only run if your `OPENAI_API_KEY` is set in `.env`.
"""
from dotenv import load_dotenv
from src.ai_client import OpenAIClient
from src.email_service import EmailWriterService


def main():
    load_dotenv()

    client = OpenAIClient()  # reads OPENAI_API_KEY from environment
    service = EmailWriterService(client, model="gpt-4o-mini")

    instruction = "Write a professional email to reschedule an interview."
    print("Sending request to OpenAI...\n")
    email = service.write_email(instruction, tone="formal")

    print("SUBJECT:\n", email.subject)
    print("\nBODY:\n", email.body)


if __name__ == '__main__':
    main()
