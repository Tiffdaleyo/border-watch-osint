"""Daily review email: what the morning run found that is not live yet, so the reviewer can check it before
publishing. Run after `python run.py --draft` by the daily workflow. Nothing here changes the live site."""
import datetime as dt
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from watch import mailer  # noqa: E402

esc = html.escape
with open(os.path.join(HERE, "data", "events.json"), encoding="utf-8") as f:
    events = json.load(f)
pub_path = os.path.join(HERE, "data", "published.json")
pub = json.load(open(pub_path, encoding="utf-8")) if os.path.exists(pub_path) else {}
live = set(pub.get("baseline") or []) | set(pub.get("approved") or {})
keep_from = (dt.date.today() - dt.timedelta(days=180)).isoformat()
new = [e for e in events if e.get("event_id") not in live and e.get("date", "") >= keep_from
       and e.get("review_status") != "Excluded"]
order = {"High": 0, "Medium": 1, "Low": 2, "Update": 3}
new.sort(key=lambda e: (not e.get("home"), not e.get("region"), order.get(e.get("level"), 4), -(e.get("score") or 0)))
repo = os.environ.get("GITHUB_REPOSITORY", "")
publish_link = f"https://github.com/{repo}/actions/workflows/publish.yml" if repo else ""
today = dt.date.today().isoformat()


def row(e):
    flag = []
    if e.get("home"):
        flag.append("JAMAICA")
    elif e.get("region"):
        flag.append("CARIBBEAN")
    if e.get("outcome_note"):
        flag.append("CHECK OUTCOME")
    lvl = "Update" if e.get("level") == "Update" else f"{e.get('level')} {e.get('score')}"
    meta = " · ".join(x for x in [e.get("event_id", ""), e.get("date", ""), e.get("source", ""),
                                  ", ".join((e.get("categories") or [])[:3]), ", ".join((e.get("countries") or [])[:3])] if x)
    return (f"<tr><td style='padding:6px 8px;border-bottom:1px solid #eee;vertical-align:top;white-space:nowrap;color:{'#b42318' if e.get('level') == 'High' else '#b54708' if e.get('level') == 'Medium' else '#475467'}'><b>{esc(lvl)}</b>"
            f"{'<br><span style=color:#c08000>' + esc(' · '.join(flag)) + '</span>' if flag else ''}</td>"
            f"<td style='padding:6px 8px;border-bottom:1px solid #eee'><a href='{esc(e.get('source_url') or e.get('url', ''))}'>{esc(e.get('title', ''))}</a>"
            f"<br><span style='color:#667085;font-size:12px'>{esc(meta)}</span>"
            + (f"<br><span style='color:#b54708;font-size:12px'>{esc(e['outcome_note'])}</span>" if e.get("outcome_note") else "")
            + "</td></tr>")


hi = sum(1 for e in new if e.get("level") == "High")
home = sum(1 for e in new if e.get("home"))
body = (f"<div style='font-family:Arial,sans-serif;max-width:760px'>"
        f"<h2 style='color:#13294b;margin:0 0 6px'>Daily draft for review: {len(new)} new report{'s' if len(new) != 1 else ''}</h2>"
        f"<p style='margin:0 0 10px;color:#344054'><b>{hi}</b> high review priority · <b>{home}</b> naming Jamaica. "
        "None of this is on the live site yet.</p>"
        "<div style='background:#eef4ff;border:1px solid #b2ccff;padding:10px 12px;border-radius:8px;margin-bottom:12px;font-size:14px'>"
        "<b>What to do</b><br>1. Read the list below (Jamaica and Caribbean first, then by priority).<br>"
        "2. To fix or remove anything, tell Claude in the Border Watch project, e.g. \"remove BWO-2026-1234\" or "
        "\"BWO-2026-1234 is Charged, not Convicted\".<br>"
        "3. When it is right, publish: " + (f"<a href='{publish_link}'>open Publish</a> and press the green <b>Run workflow</b> button" if publish_link else "run the Publish workflow")
        + ", or reply \"publish\" to Claude.<br>Publishing marks these reports as reviewed and sends any held alerts.</div>"
        f"<table style='border-collapse:collapse;width:100%;font-size:14px'>{''.join(row(e) for e in new[:150])}</table>"
        + (f"<p style='color:#667085'>…and {len(new) - 150} more, lower priority.</p>" if len(new) > 150 else "")
        + "<p style='color:#98a2b3;font-size:12px'>Unofficial project, open-source news only. Draft generated automatically.</p></div>")
text = "\n".join(f"{e.get('event_id')} | {e.get('level')} | {e.get('title')}" for e in new[:150])
if not new:
    print("No new reports since the last publish: no draft email sent.")
    sys.exit(0)
ok = mailer.send(f"DRAFT for review: {len(new)} new Border Watch reports ({today})", body, text, kind="review")
sys.exit(0 if ok or not mailer.configured("review") else 1)
