"""Reads the full article behind each report and pulls out the facts.

Only the facts and a short lead (first sentence or two) are kept. The article text itself is never stored.
Google News links are redirects; they are turned into the publisher's real link first.
"""
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from . import extract

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/124.0 Safari/537.36"}


def log(*a):
    print(*a, flush=True)


def real_url(url):
    """Google News link -> the publisher's link (needs the optional 'googlenewsdecoder' package)."""
    if "news.google.com" not in url:
        return url
    try:
        from googlenewsdecoder import gnewsdecoder
        res = gnewsdecoder(url, timeout=10)
        if res.get("success") or res.get("status"):
            return res.get("decoded_url") or url
    except Exception:
        pass
    return None


def article_text(url, timeout=15, max_chars=12000):
    try:
        import trafilatura
    except ImportError:
        return ""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code != 200 or "html" not in r.headers.get("content-type", "html"):
            return ""
        text = trafilatura.extract(r.text, include_comments=False, include_tables=False, favor_precision=True) or ""
        return text[:max_chars]
    except Exception:
        return ""


JUNK = ("cookie", "navegacion", "navegación", "javascript", "loading", "subscribe", "suscrib", "newsletter", "sign up",
        "advertisement", "all rights reserved", "click here", "read more", "accept")


def lead(text, limit=260):
    """The first sentence or two, as a short summary (skipping cookie notices and page clutter)."""
    text = " ".join(text.split())
    out = ""
    parts = [p for p in text.replace("? ", "?|").replace("! ", "!|").replace(". ", ".|").split("|")
             if len(p) > 25 and not any(j in p.lower() for j in JUNK)]
    text = " ".join(parts)
    for part in parts:
        if len(out) + len(part) > limit:
            break
        out = (out + " " + part).strip()
    return out or (text[:limit].rsplit(" ", 1)[0] + "…" if text else "")


AGENCIES = ["INTERPOL", "Europol", "Frontex", "UNODC", "AIRCOP", "WCO", "IOM", "UNHCR", "PICA", "JCF", "Jamaica Customs",
            "Jamaica Constabulary Force", "JDF", "Jamaica Defence Force", "MOCA", "CBP", "ICE", "HSI", "DEA", "FBI",
            "US Coast Guard", "Coast Guard", "Border Force", "NCA", "National Crime Agency", "CBSA", "RCMP", "Guardia Civil",
            "Policia Nacional", "Gendarmerie", "Douane", "NDLEA", "NACOC", "FIA", "CARICOM IMPACS", "IMPACS", "RSS",
            "Policia Federal", "Receita Federal", "Customs", "Immigration"]
OUTCOMES = [("Sentenced", ["sentenced", "jailed", "imprisoned", "condenad*", "condamne*"]),
            ("Convicted", ["convicted", "found guilty", "pleaded guilty", "pleads guilty"]),
            ("Charged", ["charged", "indicted", "prosecuted", "imputad*", "mis en examen"]),
            ("Arrested", ["arrested", "detained", "apprehended", "taken into custody", "detenid*", "arrestad*", "captur*", "aprehend*",
                          "interpelle*", "preso*", "presa*", "detido*", "prende*"]),
            ("Seized / intercepted", ["seized", "intercepted", "confiscated", "incaut*", "decomis*", "saisi*", "apreend*"])]
_OUT_RE = [(name, extract.compile_words(words)) for name, words in OUTCOMES]
_AG_RE = [(a, re.compile(r"(?<!\w)" + re.escape(a) + r"(?!\w)")) for a in AGENCIES]
_SENT_RE = re.compile(r"(?<!\w)(\d{1,3})\s*(?:-|\s)?(years?|months?)\b[^.]{0,40}?(?:prison|jail|imprisonment|sentence)", re.I)


def first_weight(text):
    for m in extract._KG_RE.finditer(extract.fold(text[:4000])):
        w = extract.find_weight_kg(m.group(0))
        if w:
            return w
    return 0


def article_facts(ev, text, risk_words, focus):
    """Facts from the full text. Topics and countries come from the opening part (the most relevant);
    numbers, airports, routes and warning signs come from the whole article."""
    head = text[:1500]
    top = extract.extract({"title": ev["title"], "summary": head}, focus) or {}
    folded = extract.fold(text)
    terms = sorted({w for rx in risk_words for w in extract.find_words(rx, folded)})[:25]
    origin, dest = extract.find_route(text)
    return {
        "read": True,
        "kind": top.get("kind", ""),
        "lead": lead(text),
        "categories": top.get("categories", []),
        "countries": top.get("countries", []),
        "airports": extract.find_airports(text),
        "document_types": top.get("document_types", []),
        # the first figure mentioned is usually the event itself; later ones are often background or other cases
        "documents_count": extract.find_count(extract._DOC_COUNT_RE, text[:2500]),
        "people_count": extract.find_count(extract._PEOPLE_COUNT_RE, text[:2500]),
        "weight_kg": first_weight(text),
        "origin": origin, "destination": dest,
        "terms": terms,
        "agencies": [a for a, rx in _AG_RE if rx.search(text)][:6],
        "outcome": next((name for name, rx in _OUT_RE if rx.search(folded)), ""),
        "sentence": (lambda m: f"{m.group(1)} {m.group(2)}" if m else "")(_SENT_RE.search(text)),
    }


def apply_article(ev):
    """Merge the stored article facts into the report (used after every extraction, so a rebuild keeps them)."""
    a = ev.get("article") or {}
    if not a.get("read"):
        return ev
    for k in ("categories", "countries", "airports", "document_types"):
        ev[k] = list(dict.fromkeys((ev.get(k) or []) + [x for x in a.get(k, []) if x not in (ev.get(k) or [])]))
    ev["categories"] = sorted(ev["categories"])
    for k in ("documents_count", "people_count", "weight_kg"):
        ev[k] = max(ev.get(k) or 0, a.get(k) or 0)
    if not ev.get("origin") and a.get("origin"):
        ev["origin"] = a["origin"]
    if not ev.get("destination") and a.get("destination"):
        ev["destination"] = a["destination"]
    if a.get("kind") == "Incident":
        ev["kind"] = "Incident"
    if a.get("lead") and not ev.get("summary"):
        ev["lead"] = a["lead"]
    return ev


def read_articles(events, cfg, risk_words, focus, budget_minutes=8, limit=400, workers=8):
    """Reads up to `limit` unread reports from the last 30 days, Caribbean and incidents first, within the time budget."""
    import datetime as dt
    cutoff = (dt.date.today() - dt.timedelta(days=30)).isoformat()
    todo = [e for e in events if not (e.get("article") or {}).get("tried") and e.get("date", "") >= cutoff
            and "example.org" not in e.get("url", "")]
    todo.sort(key=lambda e: (not e.get("home"), not e.get("region"), e.get("kind") == "Update", e.get("date", "")), reverse=False)
    todo = todo[:limit]
    if not todo:
        return 0
    deadline = time.monotonic() + budget_minutes * 60
    log(f"Reading full articles for {len(todo)} reports (up to {budget_minutes} minutes)...")

    def one(ev):
        if time.monotonic() > deadline:
            return ev, None, "skipped"
        url = real_url(ev["url"])
        if not url:
            return ev, None, "no link"
        text = article_text(url)
        return ev, (url, text), "ok" if len(text) > 300 else "no text"

    done = ok = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for fut in as_completed([pool.submit(one, e) for e in todo]):
            ev, res, status = fut.result()
            if status == "skipped":
                continue
            done += 1
            a = {"tried": True}
            if res and status == "ok":
                url, text = res
                a.update(article_facts(ev, text, risk_words, focus))
                ev["source_url"] = url
                ok += 1
            ev["article"] = a
    log(f"  read {ok} of {done} articles attempted ({len(todo) - done} left for the next run)")
    return ok
