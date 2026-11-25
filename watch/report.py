"""Writes the website (docs/index.html), a CSV download and the weekly bulletin."""
import csv
import datetime as dt
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = ["date", "kind", "level", "score", "title", "source", "url", "categories", "document_types", "countries",
          "airports", "origin", "destination", "documents_count", "people_count", "reasons", "via"]


def _method(cfg):
    out = []
    risk = cfg.get("risk") or {}
    for ind in (risk.get("indicators") or {}).values():
        out.append({"label": ind.get("label", ""), "points": ind.get("points", 0),
                    "words": ", ".join(w.rstrip("*") for w in (ind.get("words") or [])[:8])})
    md, mp = risk.get("many_documents") or {}, risk.get("many_people") or {}
    if md:
        out.append({"label": f"{md['threshold']}+ documents ({md['big_threshold']}+ documents)",
                    "points": f"{md['points']} ({md['big_points']})", "words": "number found in the report"})
    if mp:
        out.append({"label": f"{mp['threshold']}+ people", "points": mp["points"], "words": "number found in the report"})
    return out


def write_dashboard(out_dir, events, summary, cfg, new_today, demo=False):
    site = cfg.get("site") or {}
    data = {
        "updated": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "demo": demo, "events": events, "summary": summary, "new_today": new_today,
        "report_days": (cfg.get("run") or {}).get("report_days", 180),
        "home": site.get("home_country", ""), "region": site.get("region_name", "Region"),
        "method": _method(cfg),
    }
    with open(os.path.join(HERE, "dashboard.html"), encoding="utf-8") as f:
        page = f.read()
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = (page.replace("__TITLE__", html.escape(site.get("title", "Border Watch OSINT")))
                .replace("__SUBTITLE__", html.escape(site.get("subtitle", "")))
                .replace("__REGION__", html.escape(site.get("region_name", "Region")))
                .replace("__HOME__", html.escape(site.get("home_country", "")))
                .replace("__BANDS__", "{high} or more points = High, {medium} or more = Medium.".format(
                    **((cfg.get("risk") or {}).get("bands") or {"high": 40, "medium": 20})))
                .replace("__DATA__", blob))
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)


def write_csv(out_dir, events):
    # utf-8-sig so Excel shows accents (é, ñ) correctly
    with open(os.path.join(out_dir, "events.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for e in events:
            row = {k: ("; ".join(e[k]) if isinstance(e.get(k), list) else e.get(k, "")) for k in FIELDS}
            w.writerow(row)


def write_bulletin(out_dir, events, summary, cfg, today=None):
    """A one-page weekly summary you can print, save as PDF or paste into an email."""
    today = today or dt.date.today()
    start = (today - dt.timedelta(days=7)).isoformat()
    week = [e for e in events if e.get("date", "") >= start]
    site = cfg.get("site") or {}
    home, region = site.get("home_country", ""), site.get("region_name", "Region")
    order = {"High": 0, "Medium": 1, "Low": 2, "Update": 3}
    top = sorted([e for e in week if e.get("kind") != "Update"], key=lambda e: (order[e["level"]], -e["score"]))[:10]
    policy = [e for e in week if e.get("kind") == "Update"][:12]
    watch = [e for e in week if e.get("watch")]
    regional = sorted([e for e in week if e.get("region")], key=lambda e: not e.get("home"))[:12]
    cats = {}
    for e in week:
        for c in e["categories"]:
            cats[c] = cats.get(c, 0) + 1

    def li(e):
        lvl = "Update" if e["level"] == "Update" else f"{e['level']} ({e['score']})"
        return (f"<li><b>{html.escape(lvl)}</b> · {html.escape(e['date'])} · "
                f"<a href='{html.escape(e['url'])}'>{html.escape(e['title'])}</a> "
                f"<span class='s'>({html.escape(e.get('source', ''))})</span></li>")

    rising = [t for t in summary.get("trends", []) if t["note"] == "Rising"]
    body = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Weekly bulletin</title>
<style>body{{font-family:system-ui,Arial,sans-serif;max-width:820px;margin:24px auto;padding:0 16px;color:#1d2430}}
h1{{color:#13294b;margin-bottom:0}} h2{{color:#13294b;border-bottom:2px solid #dde2ea;padding-bottom:4px}}
.s{{color:#5b6575;font-size:13px}} li{{margin:6px 0}} .box{{background:#f4f6f9;padding:10px 14px;border-radius:8px}}</style>
</head><body>
<h1>{html.escape(site.get('title', 'Border Watch OSINT'))}: weekly bulletin</h1>
<p class="s">{start} to {today.isoformat()} · open-source news only · leads to verify, not confirmed intelligence</p>
<div class="box"><b>Key numbers.</b> {len(week)} reports this week; {sum(1 for e in week if e['level'] == 'High')} High-risk incidents; {len(policy)} policy and other updates;
{len(regional)} in the {html.escape(region)}; {sum(1 for e in week if e.get('home'))} mention {html.escape(home)}.<br>
<b>Topics:</b> {html.escape(', '.join(f'{k} {v}' for k, v in sorted(cats.items(), key=lambda x: -x[1])) or 'none')}.<br>
<b>Rising this week:</b> {html.escape(', '.join(t['category'] for t in rising) or 'nothing unusual')}.</div>
<h2>Watch list hits</h2><ul>{''.join(li(e) for e in watch) or '<li>None this week.</li>'}</ul>
<h2>Top incidents to review</h2><ol>{''.join(li(e) for e in top) or '<li>None this week.</li>'}</ol>
<h2>{html.escape(region)} and {html.escape(home)}</h2><ul>{''.join(li(e) for e in regional) or '<li>None this week.</li>'}</ul>
<h2>Visa, entry, citizenship and other updates</h2><ul>{''.join(li(e) for e in policy) or '<li>None this week.</li>'}</ul>
<p class="s">Unofficial project, open-source news only; not a government service. Generated automatically. Check every item against the original article and official sources before acting.</p>
</body></html>"""
    with open(os.path.join(out_dir, "bulletin.html"), "w", encoding="utf-8") as f:
        f.write(body)
