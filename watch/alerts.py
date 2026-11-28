"""Alert email: new high-priority or Jamaica-linked incidents (one email per run, not one per report).

Every morning a DRAFT goes to the reviewer only (draft=True). The team receives the alerts after the reviewer runs the
send-alerts workflow, which first applies the corrections in reviews.yaml (excluded reports are left out). Alerts that
are never sent roll into the next day's draft, as long as the story is still within the last 7 days."""
import os
import datetime as dt
import html

from . import mailer


RECENT_DAYS = 7  # older stories found for the first time are on the site, but not emailed


def _recent(e, today):
    try:
        return (dt.date.fromisoformat(today) - dt.date.fromisoformat((e.get("date") or "")[:10])).days <= RECENT_DAYS
    except ValueError:
        return True


def pick(events, today, home, since=None):
    """Every incident not yet alerted, first found and dated within the last 7 days (so unsent alerts roll over)."""
    if since is None:
        since = (dt.date.fromisoformat(today) - dt.timedelta(days=RECENT_DAYS)).isoformat()
    return [e for e in events
            if (e.get("first_seen") or "") >= since and _recent(e, today) and not e.get("alerted") and e.get("kind") == "Incident"
            and e.get("review_status") != "Excluded" and (e.get("level") == "High" or e.get("home"))]


def send(events, today, site, subject_prefix="", since=None, draft=False):
    home = site.get("home_country", "")
    new = pick(events, today, home, since if since is not None else None)
    if not new:
        print("  alerts: no new high-risk or home-country incidents")
        return 0
    url = site.get("url", "")
    new.sort(key=lambda e: (e.get("level") != "High", not e.get("home"), -(e.get("score") or 0)))

    def row(e):
        j = (e.get("journey") or {}).get("text", "")
        bits = [x for x in [e.get("event_id", ""), e.get("date", ""), e.get("source", ""), j, e.get("outcome", "")] if x]
        lvl = "High" if e.get("level") == "High" else e.get("level", "")
        tag = f"{lvl} {e.get('score', '')}".strip() + (f" · {home.upper()}" if e.get("home") else "")
        link = f"{url}#{e.get('event_id', '')}" if url else ""
        return (f"<li style='margin:0 0 12px'><b style='color:#b42318'>{html.escape(tag)}</b><br>"
                f"<a href='{html.escape(e.get('source_url') or e.get('url', ''))}'>{html.escape(e.get('title', ''))}</a><br>"
                f"<span style='color:#555;font-size:13px'>{html.escape(' · '.join(bits))}"
                + (f" · <a href='{html.escape(link)}'>full record</a>" if link else "") + "</span></li>")

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    send_link = f"https://github.com/{repo}/actions/workflows/send-alerts.yml" if repo else ""
    banner = ("<div style='background:#fff4e5;border:1px solid #f5c27a;padding:10px 12px;border-radius:8px;margin:0 0 14px'>"
              "<b>DRAFT for your review: not sent to the team yet.</b><br>Check these alerts. To fix or remove one, record it in "
              "reviews.yaml (for example <i>excluded</i>), or reply in the Border Watch project. When they are right, send them "
              + (f"with the green <b>Run workflow</b> button here: <a href='{send_link}'>Send alerts</a>" if send_link else "with the send-alerts workflow")
              + ". Alerts not sent today come back in tomorrow's draft (for up to 7 days).</div>") if draft else ""
    body = (f"<div style='font-family:Arial,sans-serif;max-width:680px'>" + banner +
            f"<h2 style='margin:0 0 4px;color:#13294b'>Border Watch OSINT: {len(new)} new alert{'s' if len(new) != 1 else ''}</h2>"
            f"<p style='color:#555;font-size:13px;margin:0 0 14px'>New high review-priority or {html.escape(home)}-linked incidents found "
            f"since the last published update, now checked and published. Open-source news only: leads to verify, not confirmed intelligence.</p>"
            f"<ol style='padding-left:18px'>{''.join(row(e) for e in new[:25])}</ol>"
            + (f"<p><a href='{html.escape(url)}'>Open the dashboard</a></p>" if url else "")
            + "<p style='color:#888;font-size:12px'>Unofficial project, open-source news only; not a government service.</p></div>")
    text = "\n\n".join(f"{e.get('event_id', '')} | {e.get('level', '')} | {e.get('title', '')}\n{e.get('source_url') or e.get('url', '')}"
                       for e in new[:25])
    subject = f"Border Watch alert: {len(new)} new " + ("high-priority / " if any(e.get('level') == 'High' for e in new) else "") \
              + f"{home} incident{'s' if len(new) != 1 else ''}"
    if draft:
        ok = mailer.send("DRAFT for review: " + subject, body, text, kind="review")
        print(f"  alerts: draft with {len(new)} alert(s) {'sent to the reviewer' if ok else 'not sent'}")
        return len(new) if ok else 0
    if mailer.send(subject_prefix + subject, body, text, kind="alerts"):
        for e in new:
            e["alerted"] = True
        return len(new)
    return 0
