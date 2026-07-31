from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

import config

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str) -> None:
    if not config.SMTP_HOST:
        logger.info(
            "SMTP not configured; email logged instead of sent. To=%s Subject=%s Body=%s",
            to_email,
            subject,
            body,
        )
        return
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config.SMTP_FROM_EMAIL
    message["To"] = to_email
    message.set_content(body)
    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as server:
            if config.SMTP_USE_TLS:
                server.starttls()
            if config.SMTP_USERNAME:
                server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        logger.warning("Failed to send email to %s: %s", to_email, exc)
