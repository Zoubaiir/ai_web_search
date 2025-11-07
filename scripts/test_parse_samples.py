from src.email_service import EmailWriterService

samples = [
    """```json
{
  "subject": "Let's Play Valorant!",
  "body": "Hey Yazen,\n\nI hope this message finds you well! I was wondering if you’d like to hop on Valorant for a few games. It’s always a blast playing together, and I’d love to team up and have some fun.\n\nLet me know when you’re available!\n\nBest,\n[Your Name]"
}
```""",
    """Subject: Thank You!

Body: Appreciate the help""",
    """Request: ```json

```json
{
  "subject": "Thank You for Your Support",
  "body": "Dear [Colleague]..."
}
```""",
]

svc = EmailWriterService.__new__(EmailWriterService)  # bypass __init__
for i, raw in enumerate(samples, 1):
    s, b = EmailWriterService._parse_ai_output(svc, raw)
    print(f"\n--- Sample {i} ---\nSubject: {s}\nBody: {b[:120]}...")
