"""
Sends an HTML newsletter via Gmail SMTP using an App Password.

Usage:
    python tools/send_gmail.py --html-file .tmp/newsletter_slug.html --subject "Subject"

Setup:
    1. Enable 2-Step Verification on your Google account
    2. Go to myaccount.google.com -> Security -> App Passwords
    3. Create an App Password for "Mail"
    4. Add to .env:
         GMAIL_ADDRESS=you@gmail.com
         GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
"""

import argparse
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def send_email(to: str, subject: str, html_body: str) -> None:
    gmail_address = os.getenv("GMAIL_ADDRESS")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_address or not app_password:
        print("ERROR: GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set in .env", file=sys.stderr)
        sys.exit(1)

    recipients = [r.strip() for r in to.split(",") if r.strip()]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_address
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(gmail_address, app_password)
        server.sendmail(gmail_address, recipients, msg.as_string())


def main():
    parser = argparse.ArgumentParser(description="Send newsletter via Gmail SMTP")
    parser.add_argument("--html-file", required=True, help="Path to rendered HTML newsletter file")
    parser.add_argument("--subject", required=True, help="Email subject line")
    parser.add_argument("--to", help="Recipient email (defaults to NEWSLETTER_RECIPIENT in .env)")
    args = parser.parse_args()

    if not Path(args.html_file).exists():
        print(f"ERROR: HTML file not found: {args.html_file}", file=sys.stderr)
        sys.exit(1)

    recipient = args.to or os.getenv("NEWSLETTER_RECIPIENT")
    if not recipient:
        print("ERROR: No recipient. Use --to or set NEWSLETTER_RECIPIENT in .env", file=sys.stderr)
        sys.exit(1)

    with open(args.html_file) as f:
        html_body = f.read()

    send_email(recipient, args.subject, html_body)
    print(f"Email sent to {recipient}")


if __name__ == "__main__":
    main()
