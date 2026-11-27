"""Charts (inline SVG, so they show on screen, in print and in the PDF without any script) and the written
analysis for the weekly bulletin. Every number comes from the week's collected reports."""
import datetime as dt
import html

esc = html.escape
GROUP_COLOURS = {"Document & Identity Fraud": "#2a7de1", "Migration & Facilitation": "#e0621f",
                 "Human Trafficking": "#00977a", "Citizenship & Residence": "#c08000", "Border Integrity": "#d63f7e",
                 "Policy & Systems": "#7b68e0", "Seizures & Contraband": "#7a9220"}
LEVEL_COLOURS = {"High": "#b42318", "Medium": "#b54708", "Low": "#067647", "Update": "#667085"}
INK, MUTED, GRID = "#1d2430", "#5b6575", "#e6e9ef"


def count(items):
    c = {}
    for x in items:
        if x:
            c[x] = c.get(x, 0) + 1
    return sorted(c.items(), key=lambda kv: -kv[1])


def hbar(pairs, colour="#2a7de1", width=400, label_w=150, colour_of=None, empty="Nothing reported this week."):
    """Horizontal bars with the value at the end. pairs = [(label, n)]."""
    if not pairs:
        return f"<p class='s'>{esc(empty)}</p>"
    row, top = 20, 4
    h = top + row * len(pairs)
    mx = max(n for _, n in pairs) or 1
    bw = width - label_w - 34
    out = [f"<svg viewBox='0 0 {width} {h}' width='100%' role='img' style='max-width:{width}px'>"]
    for i, (lab, n) in enumerate(pairs):
        y = top + i * row
        w = max(2, bw * n / mx)
        c = colour_of(lab) if colour_of else colour
        short = lab if len(lab) <= 26 else lab[:25] + "…"
        out.append(f"<text x='{label_w - 6}' y='{y + 13}' text-anchor='end' font-size='11' fill='{MUTED}'>{esc(short)}<title>{esc(lab)}</title></text>"
                   f"<rect x='{label_w}' y='{y + 3}' width='{w:.1f}' height='12' rx='3' fill='{c}'/>"
                   f"<text x='{label_w + w + 5:.1f}' y='{y + 13}' font-size='11' fill='{INK}'>{n}</text>")
    out.append("</svg>")
    return "".join(out)


def daily_stack(week, start, end, width=400, height=170):
    """Reports per day, stacked by main group (the report's primary group)."""
    d0, d1 = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    days = [(d0 + dt.timedelta(days=i)).isoformat() for i in range((d1 - d0).days + 1)]
    per = {d: {} for d in days}
    for e in week:
        d = e.get("date", "")[:10]
        if d in per:
            g = (e.get("groups") or ["Other"])[0]
            per[d][g] = per[d].get(g, 0) + 1
    mx = max([sum(v.values()) for v in per.values()] + [1])
    left, bottom, top = 28, 20, 6
    ph = height - bottom - top
    cw = (width - left - 6) / len(days)
    out = [f"<svg viewBox='0 0 {width} {height}' width='100%' role='img' style='max-width:{width}px'>"]
    for k in range(0, 5):
        v = round(mx * k / 4)
        y = top + ph - ph * v / mx
        out.append(f"<line x1='{left}' x2='{width - 6}' y1='{y:.1f}' y2='{y:.1f}' stroke='{GRID}'/>"
                   f"<text x='{left - 4}' y='{y + 3:.1f}' text-anchor='end' font-size='9.5' fill='{MUTED}'>{v}</text>")
    for i, d in enumerate(days):
        x, y = left + i * cw + cw * 0.18, top + ph
        for g, colour in GROUP_COLOURS.items():
            n = per[d].get(g, 0)
            if n:
                hh = ph * n / mx
                y -= hh
                out.append(f"<rect x='{x:.1f}' y='{y:.1f}' width='{cw * 0.64:.1f}' height='{hh:.1f}' fill='{colour}'><title>{esc(g)}: {n}</title></rect>")
        out.append(f"<text x='{x + cw * 0.32:.1f}' y='{height - 6}' text-anchor='middle' font-size='9.5' fill='{MUTED}'>{d[8:10]}/{d[5:7]}</text>")
    out.append("</svg>")
    return "".join(out)


def legend():
    return "<div class='lg'>" + "".join(f"<span><i style='background:{c}'></i>{esc(g)}</span>" for g, c in GROUP_COLOURS.items()) + "</div>"


def _route(e):
    j = e.get("journey") or {}
    return f"{j['origin']} → {j['destination']}" if j.get("origin") and j.get("destination") and j["origin"] != j["destination"] else ""


def _spec(e, sec, label):
    for name, rows in e.get("specialist") or []:
        if name == sec:
            rows = dict(rows) if not isinstance(rows, dict) else rows
            return rows.get(label) or ""
    return ""


def _names(pairs):
    return ", ".join(f"<b>{esc(k)}</b> ({n})" for k, n in pairs)


def _pct(a, b):
    return f"{round(100 * a / b)}%" if b else "0%"


def analysis(week, home, region):
    """Short written analysis per area. Each point states the counts it rests on."""
    inc = [e for e in week if e.get("kind") != "Update"]
    out = []

    def grp(g):
        return [e for e in inc if g in (e.get("groups") or [])]

    sz = grp("Seizures & Contraband")
    if sz:
        pts = []
        subs = count(s for e in sz for s in e.get("substances") or [])[:3]
        if subs:
            pts.append(f"The substances or items reported most were {_names(subs)}.")
        hid = [e for e in sz if e.get("concealment_types")]
        conc = count(c for e in hid for c in e["concealment_types"])[:3]
        if conc:
            pts.append(f"{_pct(len(hid), len(sz))} of seizure reports said how the goods were hidden, most often {_names(conc)}.")
        cover = count(c for e in sz for c in e.get("cover_goods") or [])[:2]
        if cover:
            pts.append(f"Cover loads named: {_names(cover)}. Shipments of these goods on the same routes deserve a closer look.")
        routes = count(_route(e) for e in sz)[:3]
        if routes:
            pts.append(f"Routes: {_names(routes)}.")
        ins = [e for e in sz if e.get("insider_roles")]
        pts.append(f"{len(ins)} of {len(sz)} seizure reports ({_pct(len(ins), len(sz))}) named staff as involved. These are allegations in the news, not findings.")
        out.append(("Seizures and contraband", len(sz), pts))
    docs = grp("Document & Identity Fraud")
    if docs:
        pts = []
        dt_ = count(d for e in docs for d in e.get("document_types") or [])[:3]
        if dt_:
            pts.append(f"Documents named most: {_names(dt_)}.")
        m = count(x for e in docs for x in _spec(e, "Document fraud", "Reported fraud method").split("; "))[:3]
        if m:
            pts.append(f"Fraud methods: {_names(m)}.")
        ic = count(x for e in docs for x in _spec(e, "Document fraud", "Issuing country of the document").split("; "))[:3]
        if ic:
            pts.append(f"Documents claimed to be from {_names(ic)}.")
        st = count(x for e in docs for x in _spec(e, "Document fraud", "Detection stage").split("; "))[:2]
        if st:
            pts.append(f"Where it was caught: {_names(st)}.")
        out.append(("Documents and identity", len(docs), pts))
    mig = grp("Migration & Facilitation")
    if mig:
        pts = []
        r = count(_route(e) for e in mig)[:3]
        if r:
            pts.append(f"Journeys reported most: {_names(r)}.")
        tm = count(e.get("transport_mode") for e in mig if e.get("transport_mode") not in ("", "Not reported", None))[:3]
        if tm:
            pts.append(f"Transport: {_names(tm)}.")
        fac = count(x for e in mig for x in _spec(e, "Migrant smuggling", "Alleged facilitators (role)").split("; "))[:3]
        if fac:
            pts.append(f"Facilitators named: {_names(fac)}.")
        out.append(("Irregular movement and smuggling", len(mig), pts))
    tr = grp("Human Trafficking")
    if tr:
        pts = []
        x = count(t for e in tr for t in e.get("exploitation") or [])[:3]
        if x:
            pts.append(f"Exploitation types: {_names(x)}.")
        va = sum(1 for e in tr if e.get("victim_assistance"))
        pts.append(f"{va} of {len(tr)} reports mention support or referral for victims.")
        out.append(("Human trafficking", len(tr), pts))
    up = [e for e in week if e.get("kind") == "Update" and "Policy & Systems" in (e.get("groups") or [])
          and e.get("primary_category") != "Travel advisories"]
    if up:
        def t(e):
            return (e.get("title", "") + " " + (e.get("summary") or "")).lower()
        tight = sum(1 for e in up if any(w in t(e) for w in ("suspend", "ban", "restrict", "end visa-free", "ends visa-free", "tighten", "revok", "stricter", "new requirement")))
        ease = sum(1 for e in up if any(w in t(e) for w in ("visa-free", "visa free", "waiver", "exempt", "eases", "easing", "lifts", "extend")) and "suspend" not in t(e))
        pts = [f"{tight} change{'' if tight == 1 else 's'} tightened entry rules and {ease} eased them (judged from the wording, so check each source)."]
        c = count(x for e in up for x in e.get("countries") or [])[:4]
        if c:
            pts.append(f"Countries in the news: {_names(c)}.")
        hm = [e for e in up if e.get("home") or e.get("region")]
        if hm:
            pts.append(f"{len(hm)} change{'' if len(hm) == 1 else 's'} concern {esc(region)} or {esc(home)}. Check whether they affect {esc(home)} travellers or arrivals.")
        out.append(("Visa and entry rules", len(up), pts))
    bi = grp("Border Integrity")
    if bi:
        cor = [e for e in bi if "Corruption and insider facilitation" in (e.get("categories") or []) or e.get("insider_roles")]
        pts = [f"{len(cor)} of {len(bi)} border-integrity incidents involve staff or corruption."]
        ap = count(a for e in bi for a in e.get("airports") or [])[:3]
        if ap:
            pts.append(f"Airports named: {_names(ap)}.")
        out.append(("Border integrity", len(bi), pts))
    return out


def charts_block(week, start, end, region):
    inc = [e for e in week if e.get("kind") != "Update"]
    sz = [e for e in inc if "Seizures & Contraband" in (e.get("groups") or [])]
    region_set = {c for e in week if e.get("region") for c in e.get("countries") or []}
    boxes = [
        ("Reports per day, by main group", daily_stack(week, start, end) + legend()),
        ("Main groups", hbar(count(g for e in week for g in e.get("groups") or []), colour_of=lambda g: GROUP_COLOURS.get(g, "#667085"))),
        ("Countries named most", hbar(count(c for e in week for c in e.get("countries") or [])[:8],
                                      colour_of=lambda c: "#00977a" if c in region_set else "#2a7de1")),
        ("Review priority (incidents)", hbar([(k, n) for k, n in count(e.get("level") for e in inc)], colour_of=lambda k: LEVEL_COLOURS.get(k, "#667085"))),
        ("Seizures: substance or item", hbar(count(s for e in sz for s in e.get("substances") or [])[:8], "#7a9220")),
        ("Seizures: how it was hidden", hbar(count(c for e in sz for c in e.get("concealment_types") or [])[:8], "#e0621f",
                                             empty="No seizure report this week said how it was hidden.")),
        ("Transport used", hbar(count(e.get("transport_mode") for e in inc if e.get("transport_mode") not in ("", "Not reported", None))[:7], "#7b68e0")),
        ("Routes reported (origin → destination)", hbar(count(_route(e) for e in inc)[:7], "#00977a", label_w=190,
                                                        empty="No complete routes stated this week.")),
    ]
    return "<div class='charts'>" + "".join(f"<div class='ch'><h3>{esc(t)}</h3>{svg}</div>" for t, svg in boxes) + "</div>"
