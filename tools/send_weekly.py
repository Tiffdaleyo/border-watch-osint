"""Turns docs/bulletin.html into a one-page PDF and emails it (run every Monday by the weekly-bulletin workflow)."""
import datetime as dt
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from watch import mailer  # noqa: E402

src = os.path.join(HERE, "docs", "bulletin.html")
pdf = os.path.join(HERE, "docs", "bulletin.pdf")
chrome = next((c for c in ("google-chrome", "chromium", "chromium-browser") if shutil.which(c)), None)
if not chrome:
    sys.exit("No Chrome found to make the PDF.")
subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}", "file://" + src], check=True, timeout=120)
print(f"PDF made: {os.path.getsize(pdf)} bytes")

with open(src, encoding="utf-8") as f:
    page = f.read()
week = dt.date.today().isoformat()
html = ("<p style='font-family:Arial,sans-serif'>This week's Border Watch OSINT bulletin is attached as a PDF "
        "(also below). Open-source news only: leads to verify, not confirmed intelligence.</p>" + page)
text = "This week's Border Watch OSINT bulletin is attached as a PDF."
with open(pdf, "rb") as f:
    data = f.read()
ok = mailer.send(f"Border Watch OSINT weekly bulletin, week to {week}", html, text, kind="bulletin",
                 attachments=[(f"border-watch-bulletin-{week}.pdf", data, "application/pdf")])
sys.exit(0 if ok or not mailer.configured() else 1)
