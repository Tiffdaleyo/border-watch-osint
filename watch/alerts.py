"""Alert email: new high-risk or Jamaica-linked incidents found in this run (one email per run, not one per report)."""
import html

from . import mailer


def pick(events, today, home):
    return [e for e in events
            if e.get("first_seen") == today and not e.get("alerted") and e.get("kind") == "Incident"
            and e.get("review_status") != "Excluded" and (e.get("level") == "High" or e.get("home"))]


def send(events, today, site):
    home = site.get("home_country", "")
    new = pick(events, today, home)
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

    body = (f"<div style='font-family:Arial,sans-serif;max-width:680px'>"
            f"<h2 style='margin:0 0 4px;color:#13294b'>Border Watch OSINT: {len(new)} new alert{'s' if len(new) != 1 else ''}</h2>"
            f"<p style='color:#555;font-size:13px;margin:0 0 14px'>New high-risk or {html.escape(home)}-linked incidents found "
            f"in today's run. Open-source news only: leads to verify, not confirmed intelligence.</p>"
            f"<ol style='padding-left:18px'>{''.join(row(e) for e in new[:25])}</ol>"
            + (f"<p><a href='{html.escape(url)}'>Open the dashboard</a></p>" if url else "")
            + "<p style='color:#888;font-size:12px'>Unofficial project, open-source news only; not a government service.</p></div>")
    text = "\n\n".join(f"{e.get('event_id', '')} | {e.get('level', '')} | {e.get('title', '')}\n{e.get('source_url') or e.get('url', '')}"
                       for e in new[:25])
    subject = f"Border Watch alert: {len(new)} new " + ("high-risk / " if any(e.get('level') == 'High' for e in new) else "") \
              + f"{home} incident{'s' if len(new) != 1 else ''}"
    if mailer.send(subject, body, text, kind="alerts"):
        for e in new:
            e["alerted"] = True
    return len(new)
