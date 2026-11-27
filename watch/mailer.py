"""Sends email (weekly bulletin and alerts) through a mail account you set up once.

Nothing personal is stored in this public repository. The account and the recipient list are kept as
GitHub "secrets" (Settings > Secrets and variables > Actions), which nobody else can read:

  MAIL_USERNAME   the sending address, e.g. borderwatch.alerts@gmail.com
  MAIL_PASSWORD   that account's app password (16 letters), NOT its normal password
  MAIL_TO         who receives the weekly bulletin, comma-separated
  MAIL_ALERTS_TO  optional: who receives alerts (if empty, MAIL_TO is used)
  MAIL_SERVER     optional: defaults to smtp.gmail.com (port 465)

Recipients are put in "Bcc", so team members do not see each other's addresses.
If the secrets are not set, nothing is sent and the run carries on normally.
"""
import os
import smtplib
import ssl
from email.message import EmailMessage


def recipients(kind="bulletin"):
    # the reviewer (MAIL_REVIEW_TO) gets the daily draft and the draft bulletin; if not set, the alerts list is used
    raw = os.environ.get("MAIL_ALERTS_TO") if kind == "alerts" else ""
    if kind == "review":
        raw = os.environ.get("MAIL_REVIEW_TO") or os.environ.get("MAIL_ALERTS_TO") or ""
    raw = raw or os.environ.get("MAIL_TO", "")
    return [a.strip() for a in raw.replace(";", ",").split(",") if "@" in a]


def configured(kind="bulletin"):
    return bool(os.environ.get("MAIL_USERNAME") and os.environ.get("MAIL_PASSWORD") and recipients(kind))


def send(subject, html, text, kind="bulletin", attachments=()):
    """attachments: [(filename, bytes, 'application/pdf'), ...]. Returns True when sent."""
    if not configured(kind):
        print(f"  email ({kind}): not set up yet (no MAIL_USERNAME / MAIL_PASSWORD / MAIL_TO secrets), nothing sent")
        return False
    user = os.environ["MAIL_USERNAME"]
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"Border Watch OSINT <{user}>"
    msg["To"] = user
    msg["Bcc"] = ", ".join(recipients(kind))
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    for name, data, mime in attachments:
        main, sub = mime.split("/", 1)
        msg.add_attachment(data, maintype=main, subtype=sub, filename=name)
    server = os.environ.get("MAIL_SERVER") or "smtp.gmail.com"
    port = int(os.environ.get("MAIL_PORT") or 465)
    try:
        with smtplib.SMTP_SSL(server, port, context=ssl.create_default_context(), timeout=60) as s:
            s.login(user, os.environ["MAIL_PASSWORD"])
            s.send_message(msg)
        print(f"  email ({kind}): sent to {len(recipients(kind))} recipient(s)")
        return True
    except Exception as e:      # never stop the daily run because of email
        print(f"  email ({kind}): could not send ({type(e).__name__}: {e})")
        return False
