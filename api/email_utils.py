"""SMTP notification helper for waitlist signups (owner notification only)."""

import os
import smtplib


def send_waitlist_notification(email: str, signed_up_at: str) -> None:
    """Send SMTP owner notification for a new waitlist signup.

    Reads SMTP configuration from environment variables at call time.
    Raises SMTPException (or a subclass) on delivery failure (D-06: fail loudly).
    Raises KeyError if a required env var is missing (surfaces misconfiguration).

    Env vars required: SMTP_HOST, SMTP_USER, SMTP_PASS, SMTP_FROM.
    Env var optional: SMTP_PORT (default 587, STARTTLS per D-03).
    Recipient is hardcoded to info@k-innovative.com (D-04).
    """
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASS"]
    from_addr = os.environ["SMTP_FROM"]
    to_addr = "info@k-innovative.com"

    subject = f"New waitlist signup: {email}"
    body = (
        "New signup on Performance Plus waitlist.\r\n\r\n"
        f"Email: {email}\r\n"
        f"Timestamp: {signed_up_at}\r\n"
        "Source: landing_page"
    )
    message = "\r\n".join([
        f"From: {from_addr}",
        f"To: {to_addr}",
        f"Subject: {subject}",
        "",
        body,
    ])
    with smtplib.SMTP(host, port) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.sendmail(from_addr, [to_addr], message)
