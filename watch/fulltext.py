"""Reads the full article behind each report and pulls out the facts.

Only the facts and a short lead (first sentence or two) are kept. The article text itself is never stored.
Google News links are redirects; they are turned into the publisher's real link first.
"""
import datetime as dt
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from . import extract, journey, record, seizure, specialist

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
    when, quality = record.event_date(text, ev.get("date", ""))
    facts = {
        "event_date": when, "event_date_quality": quality,
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
        "outcome": record.outcome(text[:4000]),
        "transport": record.transport_mode(text[:3000]),
        "location": record.location(text[:3000]),
        "summary_text": lead(text, limit=520),
        "exploitation": record.exploitation(text[:4000]),
        "victim_assistance": record.victim_assistance(text[:4000]),
        "v": 4,
        "sentence": (lambda m: f"{m.group(1)} {m.group(2)}" if m else "")(_SENT_RE.search(text)),
    }
    # specialist details from the full text (the article text itself is never stored)
    tmp = {**ev, "categories": sorted(set(ev.get("categories", [])) | set(facts["categories"])),
           "kind": facts["kind"] or ev.get("kind", "Incident"), "transport_mode": facts["transport"],
           "outcome": facts["outcome"], "exploitation": facts["exploitation"], "agencies": facts["agencies"],
           "location": facts["location"]}
    for key in ("document_types", "countries", "airports", "origin", "destination", "documents_count", "people_count"):
        tmp[key] = facts[key] or ev.get(key)
    facts["specialist"] = specialist.sections(tmp, text[:5000])
    # journey details and stated nationality, from the opening part of the article (the event itself)
    facts["transit"] = journey.transit_points(text[:4000])
    facts["interception"], facts["interception_country"] = journey.interception(text[:3000], tmp)
    facts["nationality"] = journey.nationalities(text[:4000])
    facts["seizure_rows"], facts["seizures"] = seizure.details(text[:3000], tmp)
    return facts


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


def read_articles(events, cfg, risk_words, focus, budget_minutes=8, limit=400, workers=8, only_direct=False):
    """Reads up to `limit` unread reports from the last 30 days, Caribbean and incidents first, within the time budget."""
    cutoff = (dt.date.today() - dt.timedelta(days=30)).isoformat()
    # unread reports, plus reports read before the fuller record existed (version 1), read again once
    todo = [e for e in events if e.get("date", "") >= cutoff and "example.org" not in e.get("url", "") and not e.get("title_only")
            and (not (e.get("article") or {}).get("tried")
                 or ((e.get("article") or {}).get("read") and (e.get("article") or {}).get("v", 1) < 4))]
    if only_direct:      # skip Google News links (used when Google is limiting requests)
        todo = [e for e in todo if "news.google.com" not in e.get("url", "")]
    todo.sort(key=lambda e: (bool((e.get("article") or {}).get("tried")), not e.get("home"), not e.get("region"), e.get("kind") == "Update", e.get("date", "")), reverse=False)
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
            old = ev.get("article") or {}
            if res and status == "ok":
                url, text = res
                a = {"tried": True, "read_on": dt.date.today().isoformat()}
                a.update(article_facts(ev, text, risk_words, focus))
                ev["source_url"] = url
                ev["article"] = a
                ok += 1
            elif old.get("read"):
                # could not re-read: keep the facts we already have; give up re-reading after 3 tries
                old["refails"] = old.get("refails", 0) + 1
                if old["refails"] >= 3:
                    old["v"] = 4
            else:
                # failed (blocked, busy or no link): try again on later runs, up to 3 times
                fails = old.get("fails", 0) + 1
                ev["article"] = {"fails": fails, "tried": fails >= 3}
    log(f"  read {ok} of {done} articles attempted ({len(todo) - done} left for the next run)")
    if done >= 20 and ok == 0:
        log("  note: no article could be read; the news sites are probably limiting requests. They will be retried next run.")
    return ok
