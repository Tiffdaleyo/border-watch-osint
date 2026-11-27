"""Writes the website (docs/index.html), a CSV download and the weekly bulletin."""
import csv
import datetime as dt
import html
import json
import os

from .extract import GROUPS
from .places import CENTROIDS, COUNTRIES
from .record import NR, port_label
from . import languages
from . import bulletin_charts as bc
from .ports import PORTS as PORT_LIST

HERE = os.path.dirname(os.path.abspath(__file__))
# CSV columns, in the order of the event record. Empty values are written as "Not reported".
FIELDS = ["event_id", "title", "summary_text", "primary_category", "tags", "groups", "kind", "level", "score",
          "event_date", "event_date_quality", "published", "first_seen", "last_updated",
          "countries", "cities", "airports", "ports", "crossings", "origin", "transit", "destination", "interception",
          "route_completeness", "route_basis", "route_text", "nationality",
          "caribbean_connection", "jamaica_connection", "transport_mode", "document_types", "documents_count",
          "people_count", "weight_kg", "agencies", "outcome", "exploitation", "victim_assistance",
          "seizure_quantities", "concealment_types", "cover_goods", "insider_roles", "substances", "specialist", "review_status", "review_note", "uncertainty", "corrections", "source_type", "source_language",
          "independent_sources", "republications", "source_relationship", "source", "source_url", "url", "sources", "related", "reasons"]
# fields the website needs (the stored file keeps more, e.g. the raw article facts)
DROP = {"article", "matched_words", "other_sources", "action", "lang", "via", "id", "published"}
KEEP = {"categories", "countries", "airports", "reasons", "title", "date", "level", "score", "kind", "source", "url", "event_id"}


def coverage_from(events):
    """The first day from which collection is steady: every later week has at least a third of the typical weekly
    number of reports. Comparisons with earlier periods would compare against weeks we hardly collected."""
    import collections
    import datetime as _d
    days = collections.Counter(e.get("date", "")[:10] for e in events if e.get("date"))
    if not days:
        return ""
    end = _d.date.fromisoformat(max(days))
    weeks = []
    while True:
        start = end - _d.timedelta(days=6)
        n = sum(c for d, c in days.items() if start.isoformat() <= d <= end.isoformat())
        if start.isoformat() < min(days):
            break
        weeks.append((start.isoformat(), n))
        end = start - _d.timedelta(days=1)
    if not weeks:
        return min(days)
    typical = sorted(n for _, n in weeks)[len(weeks) // 2]
    first = weeks[0][0]
    for start, n in weeks:
        if n < typical / 3:
            break
        first = start
    return first


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
    out.pop("sources", None)          # the source panel carries them
    sp = out.get("source_panel")
    if sp and not sp.get("supporting"):
        # single source: the page rebuilds the panel from source/url/date; keep only what differs from the default
        small = {"language": sp.get("language")}
        if sp.get("type") != "News report":
            small["type"] = sp["type"]
        if sp.get("relationship") != "Single source":
            small["relationship"] = sp["relationship"]
        out["source_panel"] = small
    # specialist sections: only the filled values are sent; the page knows every label and shows "Not reported"
    if out.get("specialist"):
        out["specialist"] = [[name, {k: v for k, v in rows if v}] for name, rows in out["specialist"]]
    if out.get("review_status") == "Automatically collected":
        out.pop("review_status")
    out.pop("groups", None)           # the page works these out from the topics
    a = e.get("article") or {}
    if a.get("read"):
        out["read"] = True
        out["terms"] = a.get("terms", [])
        if a.get("sentence") and e.get("outcome"):
            out["sentence"] = a["sentence"]
    if out.get("summary_text") and out.get("summary_text") == out.get("summary"):
        out.pop("summary")
    return out


def spec_labels(events):
    out = {}
    for e in events:
        for name, rows in e.get("specialist") or []:
            out.setdefault(name, [k for k, _ in rows])
    return out


def csv_row(e):
    loc = e.get("location") or {}
    j = e.get("journey") or {}
    flat = {**e, "transit": j.get("transit", []), "interception": j.get("interception", ""),
            "route_completeness": j.get("completeness", ""), "route_basis": j.get("basis", ""), "route_text": j.get("text", ""),
            "cities": loc.get("cities", []), "ports": loc.get("ports", []), "crossings": loc.get("crossings", []),
            "seizure_quantities": [f"{q['original']} ({q['substance']}" + (", suspected" if q.get("suspected") else "")
                                   + f"; standardised {q['std_qty']:g} {q['std_unit']}; {q['qualifier']})" for q in e.get("seizures", [])],
            "specialist": [f"{sec}: " + ", ".join(f"{k} = {v or NR}" for k, v in rows) for sec, rows in e.get("specialist", [])],
            "sources": [f"{s.get('publisher', '')} {s.get('date', '')} {s.get('url', '')}".strip() for s in e.get("sources", [])]}
    sp = e.get("source_panel") or {}
    flat.update({"source_type": sp.get("type", ""), "source_language": sp.get("language", ""),
                 "independent_sources": sp.get("independent", 1), "republications": sp.get("supporting", 0),
                 "source_relationship": sp.get("relationship", ""),
                 "corrections": [f"{c.get('date', '')} {c['field']}: {c['from']} -> {c['to']} ({c.get('by', '')})"
                                 for c in e.get("corrections", [])]})
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
        "demo": demo, "events": [slim(e) for e in events], "summary": summary, "groups": GROUPS,
        "ports": [[port_label(p), p["country"], p["code"]] for p in PORT_LIST],
        "coverage_from": coverage_from(events),
        "langs": {"searched": sorted({e["lang"] for e in ((cfg.get("sources") or {}).get("google_news") or {}).get("editions", [])}),
                  "table": languages.table(), "names": languages.NAMES, "alias": languages.MAP_TO_REPORT},
        "spec_labels": spec_labels(events), "new_today": new_today,
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
                .replace("__PORTS__", str(len(PORT_LIST)))
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


def seizure_totals(incidents):
    """Same rules as the website: one main figure per report, the same large figure within 30 days counted once."""
    totals, seen = {}, {}
    for e in sorted(incidents, key=lambda x: x.get("date", "")):
        for q in e.get("seizures") or []:
            if not q.get("std_qty") or q.get("substance") == "Not reported" or not q.get("main"):
                continue
            k = (q["substance"], q["std_unit"])
            if q["std_qty"] >= 50:
                key = k + (round(q["std_qty"]),)
                last = seen.get(key)
                if last and (dt.date.fromisoformat(e["date"][:10]) - dt.date.fromisoformat(last[:10])).days <= 30:
                    continue
                seen[key] = e["date"]
            totals[k] = totals.get(k, 0) + q["std_qty"]
    return totals


def _top(items, n=3):
    c = {}
    for x in items:
        c[x] = c.get(x, 0) + 1
    return sorted(c.items(), key=lambda kv: -kv[1])[:n]


def bulletin_html(week, start, end, site, trends, root="", archive=(), latest=True):
    """One weekly bulletin page with charts and a written analysis: reads well on screen and prints cleanly (the links
    and menus are hidden in print)."""
    esc = html.escape
    home, region = site.get("home_country", ""), site.get("region_name", "Region")
    order = {"High": 0, "Medium": 1, "Low": 2, "Update": 3}
    incidents = [e for e in week if e.get("kind") != "Update"]
    top = sorted(incidents, key=lambda e: (order[e["level"]], -e["score"]))[:7]
    pol = [e for e in week if e.get("kind") == "Update" and "Policy & Systems" in (e.get("groups") or [])]
    # entry-rule changes first (Caribbean and home country first); State Department advisories only fill the gaps
    policy = sorted(pol, key=lambda e: (e.get("primary_category") == "Travel advisories", not e.get("home"), not e.get("region")))[:5]
    watch = [e for e in week if e.get("watch")][:4]
    regional = sorted([e for e in week if e.get("region")], key=lambda e: (not e.get("home"), order[e["level"]]))[:7]
    seiz = [e for e in incidents if "Seizures & Contraband" in (e.get("groups") or [])]
    official = sum(1 for e in week if e.get("official"))
    groups = _top([g for e in week for g in e.get("groups") or []], 8)

    def li(e):
        lvl = "Update" if e["level"] == "Update" else f"{e['level']} {e['score']}"
        j = (e.get("journey") or {}).get("text", "")
        extra = " · ".join(x for x in [e.get("event_id", ""), e.get("date", ""), e.get("source", ""), j, e.get("outcome", "")] if x)
        off = " <b class='o'>OFFICIAL</b>" if e.get("official") else ""
        return (f"<li><b class='l{esc(e['level'])}'>{esc(lvl)}</b>{off} <a href='{esc(e.get('source_url') or e['url'])}'>"
                f"{esc(e['title'][:140])}</a><br><span class='s'>{esc(extra)}</span></li>")

    totals = seizure_totals(seiz)
    tot_txt = "; ".join(f"{s} {v / 1000:,.1f} t" if u == "kg" and v >= 1000 else f"{s} {v:,.0f} {u}"
                        for (s, u), v in sorted(totals.items(), key=lambda x: -x[1])[:6]) or "no quantities stated"
    # highlights: plain-language points from the week's counts
    hl = []
    if groups:
        hl.append(f"Most reports were about <b>{esc(groups[0][0])}</b> ({groups[0][1]})" +
                  (f", then {esc(groups[1][0])} ({groups[1][1]})." if len(groups) > 1 else "."))
    conc = _top([c for e in seiz for c in e.get("concealment_types") or []], 2)
    if conc:
        hl.append("Seizures were most often hidden as " + " and ".join(f"<b>{esc(k.lower())}</b> ({n})" for k, n in conc) + ".")
    routes = _top([f"{(e.get('journey') or {}).get('origin')} → {(e.get('journey') or {}).get('destination')}" for e in incidents
                   if (e.get("journey") or {}).get("origin") and (e.get("journey") or {}).get("destination")], 2)
    if routes:
        hl.append("Routes reported most: " + ", ".join(f"<b>{esc(k)}</b> ({n})" for k, n in routes) + ".")
    ins = [e for e in seiz if e.get("insider_roles")]
    if ins:
        hl.append(f"<b>{len(ins)}</b> seizure report{'s' if len(ins) > 1 else ''} named staff as involved (allegations, not findings).")
    home_n = sum(1 for e in week if e.get("home"))
    hl.append(f"<b>{home_n}</b> report{'' if home_n == 1 else 's'} named {esc(home)}." if home_n else f"No report named {esc(home)} this week.")
    rising = [t["category"] for t in trends if t.get("note") == "Rising"] if latest else []
    if rising:
        hl.append("Rising compared with a usual week: <b>" + esc(", ".join(rising)) + "</b>.")
    nav_arch = "".join(f"<a href='{root}bulletins/{d}.html'>{esc(label)}</a>" for d, label in archive[:8])
    title = site.get("title", "Border Watch OSINT")
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Weekly bulletin {start} to {end} · {esc(title)}</title>
<style>@page{{size:A4;margin:11mm 12mm}}
body{{font-family:Inter,Arial,Helvetica,sans-serif;font-size:13px;line-height:1.45;color:#1d2430;background:#f3f5f9;margin:0}}
.top{{background:#13294b;color:#fff}} .top .in{{max-width:900px;margin:0 auto;padding:14px 18px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}}
.top a{{color:#cfe0ff;text-decoration:none;font-size:13px}} .top .sp{{flex:1}} .top button{{background:#fff;color:#13294b;border:0;border-radius:8px;padding:7px 12px;font-weight:600;cursor:pointer}}
.page{{max-width:900px;margin:18px auto;background:#fff;border:1px solid #dde2ea;border-radius:14px;padding:22px 26px}}
h1{{color:#13294b;margin:0;font-size:22px}} h2{{color:#13294b;font-size:12.5px;border-bottom:1.5px solid #dde2ea;padding-bottom:3px;margin:16px 0 6px;text-transform:uppercase;letter-spacing:.05em}}
.s{{color:#5b6575;font-size:11.5px}} ul,ol{{margin:0;padding-left:18px}} li{{margin:0 0 6px}} a{{color:#13294b}}
.kp{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-top:12px}} .kp div{{background:#f4f6f9;border-radius:10px;padding:8px 10px}} .kp b{{display:block;font-size:20px;color:#13294b}}
.box{{background:#f4f6f9;padding:8px 12px;border-radius:10px;margin-top:8px}} .cols{{display:grid;grid-template-columns:1fr 1fr;gap:0 20px}}
.lHigh{{color:#b42318}} .lMedium{{color:#b54708}} .lLow{{color:#067647}} .lUpdate{{color:#475467}} .o{{color:#067647;font-size:10px}}
.charts{{display:grid;grid-template-columns:1fr 1fr;gap:12px}} .ch{{border:1px solid #e6e9ef;border-radius:10px;padding:8px 10px;break-inside:avoid}}
.ch h3,.an h3{{font-size:12px;color:#13294b;margin:0 0 6px}} .lg{{font-size:10px;color:#5b6575;margin-top:4px}} .lg span{{display:inline-block;margin-right:8px}}
.lg i{{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:3px}} .an{{break-inside:avoid;margin-bottom:8px}}
.arch{{max-width:900px;margin:0 auto 24px;padding:0 18px;font-size:12.5px}} .arch a{{display:inline-block;margin:0 10px 6px 0;color:#13294b}}
@media (max-width:700px){{.cols,.charts{{grid-template-columns:1fr}} .page{{padding:16px}}}}
@media print{{body{{background:#fff;font-size:10.4px;line-height:1.3}} .top,.arch,.noprint{{display:none}} .page{{border:0;margin:0;padding:0;max-width:none}}
 h1{{font-size:17px}} h2{{font-size:11.5px;margin:8px 0 4px}} .kp b{{font-size:14px}} .kp div{{padding:4px 7px}} .s{{font-size:9.4px}} li{{margin-bottom:3px}}}}</style>
</head><body>
<!--nav--><div class="top"><div class="in"><a href="{root}index.html">← Back to the dashboard</a><span class="sp"></span>
<a href="{root}bulletins/index.html">All bulletins</a><a href="{root}bulletin.pdf">PDF</a><button onclick="print()">Print / save as PDF</button></div></div><!--/nav-->
<div class="page">
<h1>{esc(title)}: weekly bulletin</h1>
<div class="s">{"Last 7 days, " if latest else "Week of "}{start} to {end} · open-source news only · leads to verify, not confirmed intelligence</div>
<div class="kp"><div><b>{len(week)}</b>reports</div><div><b>{sum(1 for e in week if e['level'] == 'High')}</b>high review priority</div>
<div><b>{sum(1 for e in week if e.get('region'))}</b>{esc(region)}</div><div><b>{home_n}</b>{esc(home)}</div>
<div><b>{len(seiz)}</b>seizures</div><div><b>{len([e for e in week if e.get('kind') == 'Update'])}</b>policy &amp; updates</div><div><b>{official}</b>official releases</div></div>
<h2>Highlights</h2><ul>{''.join(f'<li>{x}</li>' for x in hl)}</ul>
<h2>Charts</h2>{bc.charts_block(week, start, end, region)}
<h2>Analysis: what the week suggests</h2><div class="s" style="margin-bottom:6px">Written automatically from this week's reports · patterns to look into, not findings · check each point against the sources</div>
{''.join(f"<div class='an'><h3>{esc(t)} <span class='s'>· {n} report{'' if n == 1 else 's'}</span></h3><ul>{''.join(f'<li>{p}</li>' for p in pts)}</ul></div>" for t, n, pts in bc.analysis(week, home, region)) or "<p class='s'>Not enough reports this week for an analysis.</p>"}
<div class="box"><b>Seizure totals (unverified, one figure per report):</b> {esc(tot_txt)}<br>
<b>By main group:</b> {esc(' · '.join(f'{k} {v}' for k, v in groups) or 'none')}</div>
<h2>Top incidents to review</h2><ol>{''.join(li(e) for e in top) or '<li>None this week.</li>'}</ol>
<div class="cols"><div><h2>{esc(region)} and {esc(home)}</h2><ul>{''.join(li(e) for e in regional) or '<li>None this week.</li>'}</ul></div>
<div><h2>Policy &amp; entry rules</h2><ul>{''.join(li(e) for e in policy) or '<li>None this week.</li>'}</ul>
<h2>Watch list hits</h2><ul>{''.join(li(e) for e in watch) or '<li>None this week.</li>'}</ul></div></div>
<p class="s" style="margin-top:12px">Unofficial project, open-source news only; not a government service. Generated automatically. Check every item against the original article and official sources before acting. Review priority never uses nationality.</p>
</div>
<!--nav--><div class="arch noprint">{('<b>Past weeks:</b> ' + nav_arch) if nav_arch else ''}</div><!--/nav-->
</body></html>"""


def write_bulletin(out_dir, events, summary, cfg, today=None):
    """The latest bulletin (last 7 days) at docs/bulletin.html, which is emailed as a PDF every Monday, plus one page
    for each finished week (Monday to Sunday) in docs/bulletins/, and a list of them all."""
    today = today or dt.date.today()
    site = cfg.get("site") or {}
    arch_dir = os.path.join(out_dir, "bulletins")
    os.makedirs(arch_dir, exist_ok=True)
    first = min((e.get("date", "")[:10] for e in events if e.get("date")), default=today.isoformat())
    monday = today - dt.timedelta(days=today.weekday())          # this week's Monday; earlier weeks are finished
    weeks = []
    m = monday - dt.timedelta(days=7)
    while m.isoformat() >= (dt.date.fromisoformat(first) - dt.timedelta(days=6)).isoformat() and len(weeks) < 26:
        weeks.append(m)
        m -= dt.timedelta(days=7)
    archive = [(w.isoformat(), f"{w.strftime('%d %b')} to {(w + dt.timedelta(days=6)).strftime('%d %b %Y')}") for w in weeks]
    for w in weeks:
        s, e = w.isoformat(), (w + dt.timedelta(days=6)).isoformat()
        wk = [x for x in events if s <= x.get("date", "")[:10] <= e]
        with open(os.path.join(arch_dir, f"{s}.html"), "w", encoding="utf-8") as f:
            f.write(bulletin_html(wk, s, e, site, [], root="../", archive=archive, latest=False))
    start = (today - dt.timedelta(days=6)).isoformat()
    week = [e for e in events if e.get("date", "")[:10] >= start]
    with open(os.path.join(out_dir, "bulletin.html"), "w", encoding="utf-8") as f:
        f.write(bulletin_html(week, start, today.isoformat(), site, summary.get("trends", []), archive=archive))
    rows = "".join(f"<li><a href='{d}.html'>Week of {esc_label}</a> · {n} reports</li>" for (d, esc_label), n in
                   ((a, sum(1 for x in events if a[0] <= x.get("date", "")[:10] <= (dt.date.fromisoformat(a[0]) + dt.timedelta(days=6)).isoformat()))
                    for a in archive))
    with open(os.path.join(arch_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>All weekly bulletins</title><style>body{{font-family:Inter,Arial,sans-serif;background:#f3f5f9;color:#1d2430;margin:0}}
.top{{background:#13294b}} .top a{{color:#cfe0ff;text-decoration:none;display:inline-block;padding:14px 18px;font-size:13px}}
.page{{max-width:700px;margin:18px auto;background:#fff;border:1px solid #dde2ea;border-radius:14px;padding:22px 26px}}
h1{{color:#13294b;font-size:22px;margin:0 0 12px}} li{{margin:8px 0}} a{{color:#13294b}}</style></head><body>
<div class="top"><a href="../index.html">← Back to the dashboard</a><a href="../bulletin.html">Latest bulletin</a></div>
<div class="page"><h1>All weekly bulletins</h1><p><a href="../bulletin.html"><b>Latest: the last 7 days</b></a></p>
<ul>{rows or '<li>No finished weeks yet.</li>'}</ul>
<p style="color:#5b6575;font-size:12px">Each week runs Monday to Sunday. Bulletins are rebuilt from the collected news every day, so a late report or a correction updates past weeks too.</p></div></body></html>""")
