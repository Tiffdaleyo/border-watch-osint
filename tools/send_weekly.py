"""Turns the weekly bulletin into a PDF and emails it.

  python tools/send_weekly.py --draft   Monday: the DRAFT bulletin (draft/bulletin.html) goes to the reviewer only
  python tools/send_weekly.py --team    after the reviewer pressed Send bulletin: the same week, rebuilt in draft/ with
                                        any corrections from reviews.yaml, goes to the team; its PDF is saved in docs/
"""
import datetime as dt
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from watch import mailer  # noqa: E402

DRAFT = "--draft" in sys.argv
TEAM = "--team" in sys.argv
folder = os.path.join(HERE, "draft" if (DRAFT or TEAM) else "docs")
src = os.path.join(folder, "bulletin.html")
pdf = os.path.join(folder, "bulletin.pdf")


def make_pdf(src, pdf):
    chrome = next((c for c in ("google-chrome", "chromium", "chromium-browser") if shutil.which(c)), None)
    if not chrome:
        sys.exit("No Chrome found to make the PDF.")
    subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", "file://" + src], check=True, timeout=120)
    print(f"PDF made: {os.path.getsize(pdf)} bytes")


make_pdf(src, pdf)
with open(src, encoding="utf-8") as f:
    page = f.read()
page = re.sub(r"<!--nav-->.*?<!--/nav-->", "", page, flags=re.S)     # the website's menus mean nothing in an email
week = os.environ.get("BULLETIN_DATE") or dt.date.today().isoformat()
repo = os.environ.get("GITHUB_REPOSITORY", "")
send_link = f"https://github.com/{repo}/actions/workflows/send-bulletin.yml" if repo else ""
if DRAFT:
    intro = ("<div style='font-family:Arial,sans-serif;background:#fff4e5;border:1px solid #f5c27a;padding:10px 12px;border-radius:8px'>"
             "<b>DRAFT for your review: not sent to the team yet.</b><br>Read it, then reply in the Border Watch project "
             "with anything to correct or remove (for example \"remove BWO-2026-1234\"). When it is right, "
             "send it to the team" + (f" with the green <b>Run workflow</b> button here: <a href='{send_link}'>Send bulletin</a>" if send_link else "")
             + ", or just reply \"send the bulletin\".</div>")
    subject, kind = f"DRAFT for review: Border Watch weekly bulletin, week to {week}", "review"
else:
    intro = ("<p style='font-family:Arial,sans-serif'>This week's Border Watch OSINT bulletin, checked by our reviewer, is attached "
             "as a PDF (also below). Open-source news only: leads to verify, not confirmed intelligence.</p>")
    subject, kind = f"Border Watch OSINT weekly bulletin, week to {week}", "bulletin"
text = re.sub(r"<[^>]+>", "", intro)
with open(pdf, "rb") as f:
    data = f.read()
ok = mailer.send(subject, intro + page, text, kind=kind,
                 attachments=[(f"border-watch-bulletin-{week}{'-DRAFT' if DRAFT else ''}.pdf", data, "application/pdf")])
if TEAM and ok:
    shutil.copy(pdf, os.path.join(HERE, "docs", "bulletin.pdf"))     # the sent PDF is kept on the website
sys.exit(0 if ok or not mailer.configured(kind) else 1)
