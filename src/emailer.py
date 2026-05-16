from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText


def clean_secret_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if lines:
        cleaned = lines[-1]
    for separator in ("：", ":"):
        if separator in cleaned:
            cleaned = cleaned.rsplit(separator, 1)[-1].strip()
    return cleaned


def send_email(subject: str, body: str, config: dict) -> None:
    username = clean_secret_value(os.environ.get("MAIL_USERNAME"))
    password = clean_secret_value(os.environ.get("MAIL_PASSWORD"))
    recipient = clean_secret_value(os.environ.get("MAIL_TO")) or config["profile"].get("target_email")

    missing = [
        name
        for name, value in {
            "MAIL_USERNAME": username,
            "MAIL_PASSWORD": password,
            "MAIL_TO": recipient,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing email environment variables: {', '.join(missing)}")

    email_config = config["email"]
    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = subject
    message["From"] = username
    message["To"] = recipient

    host = email_config.get("smtp_host", "smtp.qq.com")
    port = int(email_config.get("smtp_port", 465))
    security = email_config.get("smtp_security", "ssl").lower()

    if security == "starttls":
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(username, password)
            smtp.sendmail(username, [recipient], message.as_string())
    else:
        with smtplib.SMTP_SSL(host, port, timeout=30) as smtp:
            smtp.login(username, password)
            smtp.sendmail(username, [recipient], message.as_string())
