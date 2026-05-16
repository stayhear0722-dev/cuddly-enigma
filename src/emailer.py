from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText


def send_email(subject: str, body: str, config: dict) -> None:
    username = os.environ.get("MAIL_USERNAME")
    password = os.environ.get("MAIL_PASSWORD")
    recipient = os.environ.get("MAIL_TO") or config["profile"].get("target_email")

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
