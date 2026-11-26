"""Source panel: who published a report, what kind of source it is, whether it is original or a repeat, its
language, how many sources are really independent, and the review, uncertainty and correction notes.

Five websites repeating one police release are ONE source, not five confirmations: every copy of the same
headline is counted as a republication of the first one found.
"""
import re
from urllib.parse import urlparse

from . import extract

STOP = {
    "English": "the of and to in for with on at from by is was were has have after police said".split(),
    "Spanish": "el la los las de del y en con por para que fue son tras policia segun una".split(),
    "French": "le la les des du et en avec pour par est sont apres une selon dans au aux".split(),
    "Portuguese": "o os as do da dos das e em com por para foi sao apos uma segundo no na".split(),
}
LANG_CODES = {"en": "English", "es": "Spanish", "fr": "French", "pt": "Portuguese"}


def guess_lang(text, hint=""):
    words = re.findall(r"[a-z]+", extract.fold(text))
    if len(words) >= 4:
        scores = {lang: sum(w in set(sw) for w in words) for lang, sw in STOP.items()}
        best = max(scores, key=scores.get)
        if scores[best] >= 2:
            return best
    return LANG_CODES.get((hint or "")[:2].lower(), "Not reported")


OTHER_DOMAINS = ("facebook.", "youtube.", "x.com", "twitter.", "instagram.", "tiktok.", "medium.com", "substack.",
                 "reddit.", "linkedin.", "blogspot.", "wordpress.com")


def domain(url):
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def source_type(publisher, url, official):
    d = domain(url)
    p = (publisher or "").lower()
    if re.search(r"court|judiciary|tribunal|judgment|judgement", d + " " + p):
        return "Court publication"
    if official:
        return "Official release"
    if any(x in d for x in OTHER_DOMAINS) or any(x.rstrip(".") in p for x in OTHER_DOMAINS):
        return "Other (social media or blog)"
    return "News report"


_RELEASE_RE = extract.compile_words(["press release", "news release", "said in a statement", "in a statement",
                                     "statement from", "statement issued", "according to a release", "comunicado",
                                     "communique", "nota de prensa", "boletin"])


def panel(ev):
    """Builds ev['source_panel'] from ev['sources'] (added by the store when the same story is seen again)."""
    srcs = sorted(ev.get("sources") or [], key=lambda s: (s.get("date") or "9999", not s.get("official")))
    if not srcs:
        return
    lead = f"{ev.get('summary_text', '')} {ev.get('lead', '')}"
    official_first = next((s for s in srcs if s.get("official")), None)
    original = official_first or srcs[0]
    rows = []
    for s in srcs:
        stype = source_type(s.get("publisher"), s.get("url", ""), s.get("official"))
        if s is original:
            role = "Original release" if s.get("official") else "Original (earliest found)"
        else:
            role = "Republished (same headline)" + (" of the official release" if official_first else "")
        rows.append({"publisher": s.get("publisher", ""), "url": s.get("url", ""), "date": s.get("date", ""),
                     "type": stype, "role": role, "lang": s.get("lang") or guess_lang(ev.get("title", ""), ev.get("lang", ""))})
    repeats = len(rows) - 1
    rel = "Single source" if not repeats else \
        f"1 independent source; {repeats} republication{'s' if repeats != 1 else ''} of the same report (not counted as separate confirmations)"
    if not original.get("official") and _RELEASE_RE.search(extract.fold(lead)):
        rel += ". The report itself says it is based on an official statement or release"
    ev["source_panel"] = {
        "sources": rows,
        "type": rows[0]["type"] if original is srcs[0] else source_type(original.get("publisher"), original.get("url", ""), True),
        "language": rows[0]["lang"],
        "supporting": repeats,
        "independent": 1,
        "relationship": rel,
    }


def uncertainty(ev):
    """Automatic notes on missing or contradictory details (a reviewer can add their own in reviews.yaml)."""
    notes = []
    by_sub = {}
    for q in ev.get("seizures") or []:
        if q.get("substance") != "Not reported":
            by_sub.setdefault((q["substance"], q["std_unit"]), set()).add(q["original"])
    for (sub, unit), vals in by_sub.items():
        if len(vals) > 1:
            notes.append(f"Different quantities stated for {sub.lower()}: {', '.join(sorted(vals))} (may be separate seizures or totals)")
    if ev.get("kind") == "Incident":
        missing = [name for name, ok in (("when it happened", ev.get("event_date")),
                                          ("where it happened", ev.get("countries") or ev.get("airports")),
                                          ("outcome", ev.get("outcome"))) if not ok]
        if missing:
            notes.append("Not stated in the report: " + ", ".join(missing))
    if (ev.get("journey") or {}).get("completeness") == "Partial":
        notes.append("Journey only partly stated")
    if ev.get("date_basis"):
        notes.append("Publication date not shown by the source; date found is used")
    return notes
