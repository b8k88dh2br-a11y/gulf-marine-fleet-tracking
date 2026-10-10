from email.message import EmailMessage
import smtplib
from typing import Optional

from app.config import MANAGER_EMAIL, SECONDARY_MANAGER_EMAIL, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USERNAME


def send_manager_email(subject: str, body: str, manager_email: Optional[str] = None, secondary_email: Optional[str] = None) -> bool:
    recipients = []
    if manager_email:
        recipients.append(manager_email)
    if MANAGER_EMAIL:
        recipients.append(MANAGER_EMAIL)
    if secondary_email:
        recipients.append(secondary_email)
    if SECONDARY_MANAGER_EMAIL:
        recipients.append(SECONDARY_MANAGER_EMAIL)

    recipients = list(dict.fromkeys(recipient for recipient in recipients if recipient))
    if not recipients:
        print(f"[EMAIL SIMULATION] Subject: {subject}\nBody:\n{body}\n")
        return False

    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print(f"[EMAIL SIMULATION] To: {recipients}\nSubject: {subject}\nBody:\n{body}\n")
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = SMTP_USERNAME
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(message)
        print(f"Email sent to {recipients}")
        return True
    except Exception as exc:  # pragma: no cover
        print(f"Failed to send email: {exc}")
        return False


__all__ = ["send_manager_email"]
