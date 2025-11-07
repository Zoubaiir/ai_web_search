from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash

from src.ai_client import OpenAIClient
from src.email_service import EmailWriterService


def create_app() -> Flask:
    # Load env from project root .env
    load_dotenv()

    app = Flask(
        __name__,
        template_folder=str(Path(__file__).with_name("templates")),
        static_folder=str(Path(__file__).with_name("static")),
    )
    # Minimal secret key for flash messages (can be overridden via env)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-me")

    default_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            result=None,
            instruction="",
            tone="formal",
            model=default_model,
            error=None,
        )

    @app.post("/generate")
    def generate():
        instruction = (request.form.get("instruction") or "").strip()
        tone = (request.form.get("tone") or "formal").strip()
        model = (request.form.get("model") or default_model).strip()

        if not instruction:
            flash("Please enter an instruction to generate an email.", "warning")
            return redirect(url_for("index"))

        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("Missing OPENAI_API_KEY in environment")

            ai_client = OpenAIClient(api_key=api_key)
            service = EmailWriterService(ai_client, model=model)
            email = service.write_email(instruction, tone=tone)

            return render_template(
                "index.html",
                result={"subject": email.subject, "body": email.body, "tone": email.tone},
                instruction=instruction,
                tone=tone,
                model=model,
                error=None,
            )
        except Exception as e:  # pragma: no cover - UI layer
            return render_template(
                "index.html",
                result=None,
                instruction=instruction,
                tone=tone,
                model=model,
                error=str(e),
            ), 500

    return app


# Allow `python -m flask --app src.webapp.app run` and `python -m src.webapp.app`
app = create_app()

if __name__ == "__main__":  # pragma: no cover
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=True)
