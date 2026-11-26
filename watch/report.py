"""Writes the website (docs/index.html), a CSV download and the weekly bulletin."""
import csv
import datetime as dt
import html
import json
import os

from .extract import GROUPS
from .places import CENTROIDS, COUNTRIES
from .record import NR

HERE = os.path.dirname(os.path.abspath(__file__))
# CSV columns, in the order of the event record. Empty values are written as "Not reported".
FIELDS = ["event_id", "title", "summary_text", "primary_category", "tags", "groups", "kind", "level", "score",
          "event_date", "event_date_quality", "published", "first_seen", "last_updated",
          "countries", "cities", "airports", "ports", "crossings", "origin", "transit", "destination", "interception",
          "route_completeness", "route_basis", "route_text", "nationality",
          "caribbean_connection", "jamaica_connection", "transport_mode", "document_types", "documents_count",
          "people_count", "weight_kg", "agencies", "outcome", "exploitation", "victim_assistance",
          "specialist", "review_status", "review_note", "source", "source_url", "url", "sources", "related", "reasons"]
# fields the website needs (the stored file keeps more, e.g. the raw article facts)
DROP = {"article", "matched_words", "other_sources", "action", "lang", "via", "id", "published"}
KEEP = {"categories", "countries", "airports", "reasons", "title", "date", "level", "score", "kind", "source", "url", "event_id"}


def slim(e):
    # empty values are left out to keep the page small; the page shows them as "Not reported"
    out = {k: v for k, v in e.items() if k not in DROP and (k in KEEP or v not in ("", None, 0, False, [], {}))}
    if isinstance(out.get("journey"), dict):
        out["journey"] = {k: v for k, v in out["journey"].items() if v}
        if out["journey"].get("completeness") == "Not reported" and len(out["journey"]) <= 1:
            out.pop("journey")
    if isinstance(out.get("location"), dict):
        out["location"] = {k: v for k, v in out["location"].items() if v} or None
        if not out["location"]:
            out.pop("location")
    if len(out.get("sources", [])) == 1 and out["sources"][0].get("url") in (e.get("url"), e.get("source_url")):
        out.pop("sources")   # the page builds the single source from source/url/date
    a = e.get("article") or {}
    if a.get("read"):
        out["read"] = True
        out["terms"] = a.get("terms", [])
        if a.get("sentence") and e.get("outcome"):
            out["sentence"] = a["sentence"]
    if out.get("summary_text") and out.get("summary_text") == out.get("summary"):
        out.pop("summary")
    return out


def csv_row(e):
    loc = e.get("location") or {}
    j = e.get("journey") or {}
    flat = {**e, "transit": j.get("transit", []), "interception": j.get("interception", ""),
            "route_completeness": j.get("completeness", ""), "route_basis": j.get("basis", ""), "route_text": j.get("text", ""),
            "cities": loc.get("cities", []), "ports": loc.get("ports", []), "crossings": loc.get("crossings", []),
            "specialist": [f"{sec}: " + ", ".join(f"{k} = {v or NR}" for k, v in rows) for sec, rows in e.get("specialist", [])],
            "sources": [f"{s.get('publisher', '')} {s.get('date', '')} {s.get('url', '')}".strip() for s in e.get("sources", [])]}
    if e.get("kind") == "Update":
        flat["outcome"] = flat.get("outcome") or "Not applicable (update)"
    row = {}
    for k in FIELDS:
        v = flat.get(k, "")
        v = "; ".join(map(str, v)) if isinstance(v, list) else v
        row[k] = NR if v in ("", None, 0) and k not in ("score",) else v
    return row


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
    wt = risk.get("weight") or {}
    if wt:
        out.append({"label": f"{wt['threshold_kg']}+ kg ({wt['big_threshold_kg']}+ kg)",
                    "points": f"{wt['points']} ({wt['big_points']})", "words": "weight found in the report"})
    if mp:
        out.append({"label": f"{mp['threshold']}+ people", "points": mp["points"], "words": "number found in the report"})
    return out


def write_dashboard(out_dir, events, summary, cfg, new_today, demo=False):
    site = cfg.get("site") or {}
    data = {
        "updated": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "demo": demo, "events": [slim(e) for e in events], "summary": summary, "groups": GROUPS, "new_today": new_today,
        "report_days": (cfg.get("run") or {}).get("report_days", 180),
        "home": site.get("home_country", ""), "region": site.get("region_name", "Region"),
        "method": _method(cfg),
        "region_countries": site.get("region_countries", []),
        "all_countries": sorted(COUNTRIES),
        "centroids": {c: CENTROIDS[c] for c in {c for e in events for c in e.get("countries", []) + e.get("nationality", [])
                                                + [(e.get("journey") or {}).get(k, "") for k in ("origin", "destination", "interception_country")]
                                                + (e.get("journey") or {}).get("transit", [])} if c in CENTROIDS},
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
            w.writerow(csv_row(e))


def write_bulletin(out_dir, events, summary, cfg, today=None):
    """A one-page weekly summary (A4) to print, save as PDF or email. Emailed as a PDF every Monday."""
    today = today or dt.date.today()
    start = (today - dt.timedelta(days=7)).isoformat()
    week = [e for e in events if e.get("date", "") >= start]
    site = cfg.get("site") or {}
    home, region = site.get("home_country", ""), site.get("region_name", "Region")
    order = {"High": 0, "Medium": 1, "Low": 2, "Update": 3}
    incidents = [e for e in week if e.get("kind") != "Update"]
    top = sorted(incidents, key=lambda e: (order[e["level"]], -e["score"]))[:7]
    policy = [e for e in week if e.get("kind") == "Update" and "Policy & Systems" in (e.get("groups") or [])][:5]
    watch = [e for e in week if e.get("watch")][:4]
    regional = sorted([e for e in week if e.get("region")], key=lambda e: (not e.get("home"), order[e["level"]]))[:7]
    official = sum(1 for e in week if e.get("official"))
    groups = {}
    for e in week:
        for g in e.get("groups") or []:
            groups[g] = groups.get(g, 0) + 1
    esc = html.escape

    def li(e):
        lvl = "Update" if e["level"] == "Update" else f"{e['level']} {e['score']}"
        j = (e.get("journey") or {}).get("text", "")
        extra = " · ".join(x for x in [e.get("event_id", ""), e.get("date", ""), e.get("source", ""), j, e.get("outcome", "")] if x)
        off = " <b class='o'>OFFICIAL</b>" if e.get("official") else ""
        return (f"<li><b class='l{esc(e['level'])}'>{esc(lvl)}</b>{off} <a href='{esc(e.get('source_url') or e['url'])}'>"
                f"{esc(e['title'][:140])}</a><br><span class='s'>{esc(extra)}</span></li>")

    rising = [t for t in summary.get("trends", []) if t["note"] == "Rising"]
    url = site.get("url", "")
    body = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Weekly bulletin {today.isoformat()}</title>
<style>@page{{size:A4;margin:11mm 12mm}}
body{{font-family:Arial,Helvetica,sans-serif;font-size:10.6px;line-height:1.32;color:#1d2430;max-width:820px;margin:16px auto;padding:0 14px}}
@media print{{body{{margin:0;padding:0;max-width:none}}}}
h1{{color:#13294b;margin:0;font-size:18px}} h2{{color:#13294b;font-size:12px;border-bottom:1.5px solid #dde2ea;padding-bottom:2px;margin:9px 0 4px;text-transform:uppercase;letter-spacing:.04em}}
.s{{color:#5b6575;font-size:9.6px}} ul,ol{{margin:0;padding-left:16px}} li{{margin:0 0 4px}} a{{color:#13294b;text-decoration:none}}
.box{{background:#f4f6f9;padding:6px 9px;border-radius:6px;margin-top:6px}} .cols{{display:grid;grid-template-columns:1fr 1fr;gap:0 16px}}
.lHigh{{color:#b42318}} .lMedium{{color:#b54708}} .lLow{{color:#067647}} .lUpdate{{color:#475467}} .o{{color:#067647;font-size:9px}}
.k{{display:inline-block;margin-right:12px}} .k b{{font-size:14px;color:#13294b}}</style>
</head><body>
<h1>{esc(site.get('title', 'Border Watch OSINT'))}: weekly bulletin</h1>
<div class="s">{start} to {today.isoformat()} · open-source news only · leads to verify, not confirmed intelligence{(' · ' + esc(url)) if url else ''}</div>
<div class="box">
<span class="k"><b>{len(week)}</b> reports</span><span class="k"><b>{sum(1 for e in week if e['level'] == 'High')}</b> high-risk</span>
<span class="k"><b>{sum(1 for e in week if e.get('region'))}</b> {esc(region)}</span><span class="k"><b>{sum(1 for e in week if e.get('home'))}</b> {esc(home)}</span>
<span class="k"><b>{len([e for e in week if e.get('kind') == 'Update'])}</b> policy &amp; updates</span><span class="k"><b>{official}</b> official releases</span><br>
<b>By main group:</b> {esc(' · '.join(f'{k} {v}' for k, v in sorted(groups.items(), key=lambda x: -x[1])) or 'none')}<br>
<b>Rising this week:</b> {esc(', '.join(t['category'] for t in rising) or 'nothing unusual')}</div>
<h2>Top incidents to review</h2><ol>{''.join(li(e) for e in top) or '<li>None this week.</li>'}</ol>
<div class="cols"><div><h2>{esc(region)} and {esc(home)}</h2><ul>{''.join(li(e) for e in regional) or '<li>None this week.</li>'}</ul></div>
<div><h2>Policy &amp; systems</h2><ul>{''.join(li(e) for e in policy) or '<li>None this week.</li>'}</ul>
<h2>Watch list hits</h2><ul>{''.join(li(e) for e in watch) or '<li>None this week.</li>'}</ul></div></div>
<p class="s" style="margin-top:8px">Unofficial project, open-source news only; not a government service. Generated automatically. Check every item against the original article and official sources before acting. Risk scores never use nationality.</p>
</body></html>"""
    with open(os.path.join(out_dir, "bulletin.html"), "w", encoding="utf-8") as f:
        f.write(body)
