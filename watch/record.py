"""The full event record: ID, primary category, dates, location, connections, transport mode, outcome,
review status, sources and related events.

Rule: a field is only filled when the report states it. Anything not stated stays empty and is shown as
"Not reported". Nothing is guessed from a headline, and nationality is never recorded.
"""
import datetime as dt
import os
import re

import yaml

from . import extract, journey
from .places import COUNTRIES

NR = "Not reported"

# ---------------------------------------------------------------------------------------------
# primary category: the most specific crime topic first, then enforcement, then policy
# ---------------------------------------------------------------------------------------------
PRIMARY_ORDER = [
    "Human trafficking", "Migrant smuggling", "Passport fraud", "Visa and permit fraud", "Impostors",
    "Digital identity fraud", "Supporting-document fraud", "Identity and document fraud", "Application fraud",
    "Corruption and insider facilitation", "Drug trafficking", "Firearms and ammunition", "Terrorism and sanctions",
    "Cash couriers", "Wildlife smuggling", "Aviation security", "Stowaways", "Cargo operations", "INTERPOL and watch lists",
    "Irregular migration", "Immigration enforcement", "Deportation and returns", "Citizenship and naturalisation",
    "Border security", "Border technology", "Visa and entry policy", "Travel advisories", "Health travel rules",
]


def primary_category(cats):
    for c in PRIMARY_ORDER:
        if c in cats:
            return c
    return cats[0] if cats else ""


# ---------------------------------------------------------------------------------------------
# outcome (most advanced stage stated wins)
# ---------------------------------------------------------------------------------------------
OUTCOMES = [
    ("Sentenced", ["sentenced", "jailed", "imprisoned", "condenad*", "condamne*"]),
    ("Acquitted", ["acquitted", "found not guilty", "cleared of", "charges dropped", "absuelt*", "acquitte*"]),
    ("Convicted", ["convicted", "found guilty", "pleaded guilty", "pleads guilty"]),
    ("Charged", ["charged", "indicted", "prosecuted", "imputad*", "mis en examen"]),
    ("Arrested", ["arrested", "detained", "apprehended", "taken into custody", "detenid*", "arrestad*", "captur*",
                  "aprehend*", "interpelle*", "preso*", "presa*", "detido*", "prende*"]),
    ("Refused entry", ["refused entry", "denied entry", "turned away", "inadmissible", "sent back on the next flight"]),
    ("Seized / intercepted", ["seized", "intercepted", "confiscated", "incaut*", "decomis*", "saisi*", "apreend*"]),
    ("Investigation ongoing", ["under investigation", "investigation is ongoing", "investigations are ongoing",
                               "investigation continues", "investigating", "probe"]),
]
_OUT_RE = [(n, extract.compile_words(w)) for n, w in OUTCOMES]


# "if convicted", "faces up to 10 years if found guilty", "could be sentenced": a possible outcome, not what happened
_HYPOTHETICAL = re.compile(r"\b(?:if|once|unless|until|when|before)\s+(?:he |she |they |the \w+ (?:is|are) |(?:is|are) )?"
                           r"(?:convicted|found guilty|sentenced|charged|jailed)\b"
                           r"|\b(?:could|may|might|would|will|to) be (?:convicted|sentenced|jailed|charged|imprisoned)\b"
                           r"|\b(?:faces?|facing|liable to|risk(?:s|ing)?) (?:up to |a |the )?(?:\w+ ){0,3}(?:years?|jail|prison|death penalty)"
                           r"|\bpreviously (?:convicted|jailed|sentenced)\b|\bwas (?:once|earlier) (?:convicted|jailed)\b")
STAGE = {n: i for i, (n, _) in enumerate(OUTCOMES)}


def outcome(text):
    folded = _HYPOTHETICAL.sub(" ", extract.fold(text))
    return next((n for n, rx in _OUT_RE if rx.search(folded)), "")


def check_outcome(title, found):
    """A court stage in the article that the headline contradicts (headline: charged; article: convicted) is not
    trusted: the headline's stage is used and the event is flagged for a reviewer. Returns (outcome, note)."""
    head = outcome(title)
    court = ("Sentenced", "Convicted", "Acquitted")
    if found in court and head in ("Charged", "Arrested", "Investigation ongoing", "Seized / intercepted"):
        return head, f"Outcome needs checking: headline says {head.lower()}, article text says {found.lower()}"
    return found, ""


# ---------------------------------------------------------------------------------------------
# human trafficking: type of exploitation and victim assistance, only when the report says so
# ---------------------------------------------------------------------------------------------
EXPLOITATION = [
    ("Sexual exploitation", ["sexual exploitation", "sex trafficking", "forced prostitution", "forced into prostitution",
                             "explotacion sexual", "exploitation sexuelle", "exploracao sexual"]),
    ("Forced labour", ["forced labour", "forced labor", "labour exploitation", "labor exploitation", "labour trafficking",
                       "labor trafficking", "debt bondage", "trabajo forzoso", "explotacion laboral", "travail force",
                       "trabalho escravo", "trabalho forcado"]),
    ("Domestic servitude", ["domestic servitude", "domestic slavery", "servidumbre domestica"]),
    ("Forced criminality", ["forced criminality", "forced to sell drugs", "forced to commit", "scam compound*",
                            "forced to work in scam*", "cyber scam centre*", "scam centre*", "scam center*"]),
    ("Child exploitation", ["child trafficking", "child exploitation", "trafficked children", "minors trafficked",
                            "trafficking of children", "trafficking of minors", "trata de menores"]),
    ("Forced marriage", ["forced marriage*", "matrimonio forzado", "mariage force"]),
    ("Organ removal", ["organ trafficking", "organ removal", "organ harvesting", "trafico de organos"]),
]
_EXP_RE = [(n, extract.compile_words(w)) for n, w in EXPLOITATION]
_VICTIM_RE = extract.compile_words(["victims rescued", "victims were rescued", "rescued victims", "victim support",
                                    "victim assistance", "shelter", "safe house", "repatriated victims", "victims identified",
                                    "rescued", "rescatad*", "victimas rescatadas", "victimes secourues"])


def exploitation(text):
    folded = extract.fold(text)
    return [n for n, rx in _EXP_RE if rx.search(folded)]


def victim_assistance(text):
    return bool(_VICTIM_RE.search(extract.fold(text)))


# ---------------------------------------------------------------------------------------------
# transport mode
# ---------------------------------------------------------------------------------------------
MODES = [
    ("Air cargo", ["air cargo", "cargo flight*", "air freight", "airfreight", "cargo terminal", "cargo shed", "carga aerea", "fret aerien"]),
    ("Postal / courier", ["parcel*", "courier package*", "courier service*", "postal", "mail centre", "mail center",
                          "express mail", "package addressed", "encomienda*", "colis", "encomenda*"]),
    ("Maritime cargo", ["container*", "shipping container*", "cargo ship", "container ship", "bulk carrier", "wharf",
                        "wharves", "seaport", "port of", "contenedor*", "conteneur*", "conteiner*", "navio", "barrel*"]),
    ("Small vessel", ["boat", "boats", "go-fast", "speedboat", "sloop", "canoe", "fishing vessel", "yacht", "dinghy",
                      "semi-submersible", "narco-sub", "lancha*", "embarcacion*", "pirogue", "cayuco*", "patera*"]),
    ("Air passenger", ["passenger*", "luggage", "suitcase*", "baggage", "carry-on", "boarded", "flight from",
                       "flight to", "on a flight", "arriving on", "departing on", "swallow*", "pellets",
                       "pasajer*", "equipaje", "maleta*", "passager*", "bagage*", "passageir*", "bagagem"]),
    ("Land", ["border crossing", "land border", "truck", "lorry", "lorries", "bus", "trailer", "checkpoint",
              "crossing point", "camion*", "frontera terrestre"]),
]
_MODE_RE = [(n, extract.compile_words(w)) for n, w in MODES]


def transport_mode(text):
    folded = extract.fold(text)
    found = [n for n, rx in _MODE_RE if rx.search(folded)]
    if not found:
        return ""
    return found[0] if len(found) == 1 else "Mixed: " + ", ".join(found[:3])


# ---------------------------------------------------------------------------------------------
# event date (when it happened), as opposed to when it was published
# ---------------------------------------------------------------------------------------------
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}
MONTHS.update({m[:3]: i for m, i in list(MONTHS.items())})
MONTHS.update({"sept": 9, "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
               "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12})
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
_MON = "|".join(sorted(MONTHS, key=len, reverse=True))
_D1 = re.compile(r"(?<!\w)(?:on\s+)?(?:\w+day,?\s+)?(" + _MON + r")\.?\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(20\d\d))?(?!\w)")
_D2 = re.compile(r"(?<!\w)(\d{1,2})(?:st|nd|rd|th)?\s+(?:de\s+)?(" + _MON + r")(?:\s+(?:de\s+)?(20\d\d))?(?!\w)")
_DAY = re.compile(r"(?<!\w)(?:on|last|this)\s+(" + "|".join(DAYS) + r")(?!\w)")
_REL = re.compile(r"(?<!\w)(yesterday|earlier this week|last week|over the weekend|this morning|last night)(?!\w)")


def event_date(text, published):
    """Returns (date, quality): quality is 'exact', 'approximate' or 'unknown'. Only dates written in the
    report are used; a date after publication is ignored."""
    try:
        pub = dt.date.fromisoformat(published[:10])
    except Exception:
        return "", "unknown"
    t = extract.fold(text[:3000])
    for rx, order in ((_D1, "md"), (_D2, "dm")):
        for m in rx.finditer(t):
            mon, day = (m.group(1), m.group(2)) if order == "md" else (m.group(2), m.group(1))
            year = int(m.group(3)) if m.group(3) else pub.year
            try:
                d = dt.date(year, MONTHS[mon], int(day))
            except (ValueError, KeyError):
                continue
            if not m.group(3) and d > pub:
                d = d.replace(year=d.year - 1)
            if pub - dt.timedelta(days=400) <= d <= pub:
                return d.isoformat(), "exact"
    m = _DAY.search(t)
    if m:
        back = (pub.weekday() - DAYS.index(m.group(1))) % 7 or 7
        return (pub - dt.timedelta(days=back)).isoformat(), "approximate"
    m = _REL.search(t)
    if m:
        back = {"yesterday": 1, "last night": 1, "this morning": 0}.get(m.group(1), 3)
        return (pub - dt.timedelta(days=back)).isoformat(), "approximate"
    return "", "unknown"


# ---------------------------------------------------------------------------------------------
# location: city, seaport, border crossing
# ---------------------------------------------------------------------------------------------
from .ports import PORTS as _PORT_LIST
# seaports: "Kingston (JMKIN)" -> the words that name the port in a report (see watch/ports.py)
def port_label(p):
    return p["name"].replace(" (", ", ").rstrip(")") + f" ({p['code']})"


PORTS = {port_label(p): p["words"] for p in _PORT_LIST}
# names used before the world port list (kept in older article facts) -> the current label
_OLD_PORT = {}
for _p in _PORT_LIST:
    for _w in [_p["name"].split(" (")[0].split(" / ")[0]] + _p["words"]:
        _OLD_PORT.setdefault(extract.fold(_w), port_label(_p))


def norm_ports(names):
    out = []
    for n in names or []:
        if n in PORTS:
            out.append(n)
            continue
        base = extract.fold(n.split(" (")[0].split(" / ")[0])
        out.append(_OLD_PORT.get(base, n))
    return list(dict.fromkeys(out))
CROSSINGS = {
    "Darien Gap (Colombia–Panama)": ["Darien Gap", "Darien", "Darién"], "US–Mexico border": ["southern border", "US-Mexico border",
    "U.S.-Mexico border", "Rio Grande", "El Paso", "San Ysidro", "Tijuana"], "Ceuta / Melilla": ["Ceuta", "Melilla"],
    "Lampedusa": ["Lampedusa"], "English Channel": ["English Channel", "Calais", "small boats crossing"],
    "Canary Islands route": ["Canary Islands", "Islas Canarias"], "Evros (Greece–Turkey)": ["Evros"],
    "Mona Passage (DR–Puerto Rico)": ["Mona Passage"], "Haiti–DR border": ["Dajabon", "Dajabón", "Haitian-Dominican border"],
}
COUNTRY_NAMES = {extract.fold(a) for name, al in COUNTRIES.items() for a in al if extract.fold(a) == extract.fold(name)} | \
                {extract.fold(n) for n in COUNTRIES}


_HIT_RE = {}


def _hits(table, text):
    """Names from a place table whose words appear in the text (one compiled pattern per table, for speed)."""
    key = id(table)
    if key not in _HIT_RE:
        index = {}
        for name, words in table.items():
            for w in words:
                index.setdefault(extract.fold(w), name)
        alts = sorted(index, key=len, reverse=True)
        _HIT_RE[key] = (re.compile(r"(?<!\w)(" + "|".join(re.escape(a) for a in alts) + r")(?!\w)"), index)
    rx, index = _HIT_RE[key]
    folded = extract.fold(text)
    return list(dict.fromkeys(index[m.group(1)] for m in rx.finditer(folded)))


def cities(text):
    """City names we know (from the place lists), as written in the report."""
    folded = extract.fold(text)
    out = []
    for country, aliases in COUNTRIES.items():
        for a in aliases:
            fa = extract.fold(a)
            if fa in COUNTRY_NAMES or len(a) <= 4 or a.isupper():
                continue
            if fa != extract.fold(country) and re.search(r"(?<!\w)" + re.escape(fa) + r"(?!\w)", folded):
                if not any(w in fa for w in ("islands", "republic", "united", "kingdom", "states")):
                    out.append(f"{a.split(',')[0]} ({country})")
    return list(dict.fromkeys(out))[:4]


def location(text):
    return {"cities": cities(text), "ports": _hits(PORTS, text), "crossings": _hits(CROSSINGS, text)}


# ---------------------------------------------------------------------------------------------
# Caribbean and Jamaica connection: what kind of link, not just a mention
# ---------------------------------------------------------------------------------------------
TRANSIT_WORDS = extract.compile_words(["transit", "via", "transshipment", "stopover", "connecting flight", "en route",
                                       "en transito", "escala", "en escale"])


def connections(ev, site):
    region = set(site.get("region_countries", []))
    home = site.get("home_country", "")
    home_places = [extract.fold(x) for x in site.get("home_places", [])]
    text = f"{ev.get('title', '')}. {ev.get('summary', '')}. {ev.get('lead', '')}"
    folded = extract.fold(text)
    countries, origin, dest = ev.get("countries", []), ev.get("origin", ""), ev.get("destination", "")
    airports, loc = ev.get("airports", []), ev.get("location") or {}
    places_in_region = [c for c in countries if c in region]

    car = []
    if origin in region:
        car.append(f"Origin ({origin})")
    if dest in region:
        car.append(f"Destination ({dest})")
    if places_in_region and TRANSIT_WORDS.search(folded) and not car:
        car.append(f"Transit ({', '.join(places_in_region[:2])})")
    if places_in_region and not car:
        car.append(f"Occurred in or named: {', '.join(places_in_region[:3])}")
    if not car and any(w in folded for w in ("caribbean", "caricom", "caribe", "caraibes", "west indies")):
        car.append("Other explicit link (Caribbean named)")

    jm = []
    jm_airports = [a for a in airports if any(k in a for k in ("KIN", "MBJ", "OCJ"))]
    jm_ports = [p for p in loc.get("ports", []) if "Kingston" in p or "Montego" in p]
    if jm_airports:
        jm.append("Jamaican airport: " + ", ".join(jm_airports))
    if jm_ports:
        jm.append("Jamaican port: " + ", ".join(jm_ports))
    if origin == home:
        jm.append(f"Journey started in {home}")
    if dest == home:
        jm.append(f"Journey bound for {home}")
    if "pica" in folded.split() or "passport, immigration and citizenship agency" in folded:
        jm.append("PICA named")
    if not jm and (home in countries or any(h and h in folded for h in home_places)):
        jm.append(f"{home} or a {home} place named in the report (role not stated)")
    return car, jm


# ---------------------------------------------------------------------------------------------
# IDs, sources, reviews, related events
# ---------------------------------------------------------------------------------------------
def assign_ids(events, prefix="BWO"):
    """Permanent readable IDs, e.g. BWO-2026-0001, given once in the order reports were captured."""
    top = {}
    for e in events:
        m = re.match(rf"{prefix}-(\d{{4}})-(\d+)$", e.get("event_id", ""))
        if m:
            top[m.group(1)] = max(top.get(m.group(1), 0), int(m.group(2)))
    for e in sorted([e for e in events if not e.get("event_id")], key=lambda e: (e.get("first_seen", ""), e.get("date", ""), e["id"])):
        year = (e.get("date") or e.get("first_seen") or str(dt.date.today()))[:4]
        top[year] = top.get(year, 0) + 1
        e["event_id"] = f"{prefix}-{year}-{top[year]:04d}"


def ensure_sources(ev):
    if not ev.get("sources"):
        ev["sources"] = [{"publisher": ev.get("source", ""), "url": ev.get("source_url") or ev.get("url", ""),
                          "date": ev.get("date", ""), "lang": ev.get("lang", ""),
                          **({"official": True} if ev.get("official") else {})}]
    elif ev.get("source_url"):
        ev["sources"][0]["url"] = ev["source_url"]


def load_approved(path):
    """Event IDs the reviewer approved by publishing (data/published.json), with the date of approval."""
    import json
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return (json.load(f) or {}).get("approved") or {}


def last_publish(path, before=None):
    """The date of the last publish before the given date (alerts held since then go out at the next publish)."""
    import json
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        dates = sorted({d for d in ((json.load(f) or {}).get("approved") or {}).values() if not before or d < before})
    return dates[-1] if dates else ""


def save_approved(path, shown, today):
    """Mark every report now live as approved (keeps the first approval date). Returns how many are new."""
    import json
    data = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f) or {}
    appr = data.get("approved") or {}
    new = 0
    base = set(data.get("baseline") or [])
    for e in shown:
        if e.get("event_id") and e["event_id"] not in appr and e["event_id"] not in base:
            appr[e["event_id"]] = today
            new += 1
    data["approved"], data["last_publish"] = appr, today
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=0, sort_keys=True)
    return new


def load_reviews(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("reviews") or {}


EDITABLE = {"title", "primary_category", "categories", "event_date", "event_date_quality", "countries", "origin",
            "destination", "transit", "interception", "nationality", "transport_mode", "outcome", "agencies",
            "summary_text", "level", "note"}


def apply_review(ev, reviews, approved=None):
    r = reviews.get(ev.get("event_id")) or {}
    status = str(r.get("status", "")).lower()
    ev["corrections"] = []
    ev["review_uncertainty"] = ""
    if status in ("reviewed", "corrected", "excluded"):
        ev["review_status"] = status.capitalize()
        ev["review_note"] = r.get("note", "")
        ev["review_by"] = r.get("by", "")
        ev["review_date"] = str(r.get("date", "") or "")
        ev["review_uncertainty"] = r.get("uncertainty", "")
        for k, v in (r.get("corrections") or {}).items():
            if k in EDITABLE:
                before = ev.get(k)
                ev[k] = v
                ev["corrections"].append({"field": k, "from": before if before not in (None, "", []) else "Not reported",
                                          "to": v, "by": r.get("by", ""), "date": ev["review_date"]})
        if r.get("corrections"):
            ev["review_status"] = "Corrected"
            c = r["corrections"]
            if "categories" in c and "primary_category" not in c:
                ev["primary_category"] = primary_category(ev["categories"])
            ev["tags"] = [x for x in ev.get("categories", []) if x != ev.get("primary_category")]
            ev["groups"] = extract.groups_of(ev.get("categories", []))
    elif approved and ev.get("event_id") in approved and not ev.get("outcome_note"):
        # the reviewer read the daily draft and published it
        ev["review_status"] = "Reviewed"
        ev["review_date"] = approved[ev["event_id"]]
        ev["review_note"] = "Approved in the daily review before publishing"
    else:
        ev["review_status"] = "Awaiting review" if (ev.get("level") == "High" or ev.get("home") or ev.get("outcome_note")) else "Automatically collected"


_STOP = set("the a an of in on at to for and or with by from as is are was were be been after over into its their his her new "
            "says said police man woman men women two three four five de la el los las en con por para del y un una".split())


def _words(t):
    return {w for w in re.findall(r"[a-z]{4,}", extract.fold(t)) if w not in _STOP}


def related(events, window_days=90, top=3):
    """Links a report to others about the same thing: same topic, shared places or route, similar wording."""
    by_cat = {}
    for e in events:
        by_cat.setdefault(e.get("primary_category", ""), []).append(e)
    for group in by_cat.values():
        group.sort(key=lambda e: e.get("date", ""))
        words = {e["id"]: _words(e.get("title", "")) for e in group}
        for i, e in enumerate(group):
            d0 = e.get("date", "")
            scored = []
            for o in group:
                if o is e:
                    continue
                try:
                    gap = abs((dt.date.fromisoformat(d0) - dt.date.fromisoformat(o.get("date", d0))).days)
                except Exception:
                    gap = 0
                if gap > window_days:
                    continue
                s = 0
                shared = set(e.get("countries", [])) & set(o.get("countries", []))
                s += min(len(shared), 2)
                s += 2 if set(e.get("airports", [])) & set(o.get("airports", [])) else 0
                s += 2 if e.get("origin") and e.get("origin") == o.get("origin") and e.get("destination") == o.get("destination") else 0
                a, b = words[e["id"]], words[o["id"]]
                if a and b:
                    j = len(a & b) / len(a | b)
                    s += 3 if j >= 0.45 else 2 if j >= 0.3 else 0
                if s >= 3:
                    scored.append((s, o.get("date", ""), o["event_id"]))
            scored.sort(reverse=True)
            e["related"] = [x[2] for x in scored[:top]]


def build(ev, site, reviews, approved=None):
    """Fills every record field for one event (after extraction, article facts and scoring)."""
    art = ev.get("article") or {}
    text = f"{ev.get('title', '')}. {ev.get('summary', '')}. {art.get('lead', '')}"
    ev["primary_category"] = primary_category(ev.get("categories", []))
    ev["tags"] = [c for c in ev.get("categories", []) if c != ev["primary_category"]]
    ev["groups"] = extract.groups_of(ev.get("categories", []))
    ev["published"] = ev.get("date", "")
    if art.get("event_date_quality") in ("exact", "approximate"):
        ev["event_date"], ev["event_date_quality"] = art["event_date"], art["event_date_quality"]
    else:
        ev["event_date"], ev["event_date_quality"] = event_date(text, ev.get("date", ""))
    ev["location"] = dict(art.get("location") or location(text))
    ev["location"]["ports"] = norm_ports(ev["location"].get("ports"))
    ev["transport_mode"] = art.get("transport") or transport_mode(text)
    ev["outcome"], ev["outcome_note"] = "", ""
    if ev.get("kind") == "Incident":
        art_out = outcome(art["lead"]) if art.get("lead") and art.get("outcome") in ("Sentenced", "Convicted", "Acquitted") else art.get("outcome")
        ev["outcome"], ev["outcome_note"] = check_outcome(ev.get("title", ""), art_out or outcome(text))
    ev["agencies"] = art.get("agencies") or []
    ev["summary_text"] = art.get("summary_text") or ev.get("summary", "")
    ev["caribbean_connection"], ev["jamaica_connection"] = connections(ev, site)
    if "Human trafficking" in ev.get("categories", []):
        ev["exploitation"] = art.get("exploitation") or exploitation(text)
        ev["victim_assistance"] = "Reported" if (art.get("victim_assistance") or victim_assistance(text)) else ""
    else:
        ev.pop("exploitation", None)
        ev.pop("victim_assistance", None)
    ev["specialist"] = _specialist(ev, art, text)
    ensure_sources(ev)
    for k in ("transit", "interception"):
        ev.pop(k, None)
    stated = journey.nationalities(text)
    art_nat = art.get("nationality") or []
    if art.get("v", 1) < 7:
        # read before 28 Nov 2026, when "American workers" or "U.S. officers" also counted: keep United States or
        # United Kingdom from those reads only if the stored opening still states it about a person
        opening = " ".join(x for x in (text, art.get("summary_text")) if x)
        again = journey.nationalities(opening)
        art_nat = [c for c in art_nat if c not in ("United States", "United Kingdom") or c in again]
    ev["nationality"] = list(dict.fromkeys(stated + art_nat))[:5]
    apply_review(ev, reviews, approved)
    # the journey is built after the review, so a corrected origin, destination or transit shows up in it
    j = journey.build(ev, text, bool(art.get("read")))
    if art.get("read"):
        j["transit"] = list(dict.fromkeys(j["transit"] + [c for c in art.get("transit", []) if c not in (ev.get("origin"), ev.get("destination"))]))[:4]
        if not j["interception"] and art.get("interception") and art.get("v", 1) >= 7:   # older reads used a looser rule
            j["interception"], j["interception_country"] = art["interception"], art.get("interception_country", "")
        if j["transit"] and j["completeness"] == "Not reported":
            j["completeness"], j["basis"] = "Partial", "Explicitly stated in article"
    if ev.get("transit"):
        j["transit"] = ev["transit"] if isinstance(ev["transit"], list) else [ev["transit"]]
    if ev.get("interception"):
        j["interception"] = ev["interception"]
        j["interception_country"] = extract._canonical(ev["interception"]) or j.get("interception_country", "")
    j["text"] = journey.describe(j)
    ev["journey"] = j
    _seizure(ev, art, text)
    if "insider_roles" not in ev and ev.get("kind") == "Incident":
        from . import seizure as _sz
        roles = _sz.insider_roles(text)
        if roles:
            ev["insider_roles"] = roles      # staff named as involved, for any incident (corruption, smuggling...)
    from . import sources
    sources.panel(ev)
    ev["uncertainty"] = ([ev["review_uncertainty"]] if ev.get("review_uncertainty") else []) + sources.uncertainty(ev)
    if art.get("read") and art.get("read_on"):
        ev["corrections"].insert(0, {"field": "several", "from": "headline only", "to": "facts taken from the full article",
                                     "by": "automatic", "date": art["read_on"]})
    from . import privacy
    privacy.apply(ev)
    return ev


SEIZURE_TOPICS = {"Drug trafficking", "Firearms and ammunition", "Cash couriers", "Wildlife smuggling", "Cargo operations"}


def _seizure(ev, art, text):
    """Seizure fields for seizure incidents; the article's figures are preferred over the headline's."""
    ev.pop("seizures", None)
    ev.pop("concealment_types", None)
    ev.pop("cover_goods", None)
    ev.pop("insider_roles", None)
    ev.pop("substances", None)
    ev["specialist"] = [s for s in ev.get("specialist", []) if s[0] != "Seizure"]
    if ev.get("kind") != "Incident" or not set(ev.get("categories", [])) & SEIZURE_TOPICS:
        return
    from . import seizure
    rows, qs = seizure.details(text, ev)
    full = dict(art.get("seizure_rows") or [])
    for row in rows:
        if row[0] in ("Origin", "Transit", "Destination", "Seizing agency"):
            continue          # these come from the final journey and agency fields
        if full.get(row[0]):
            row[1] = full[row[0]]
    # standard categories for trends: from the full article when it gave them, otherwise from the concealment words
    # (article or headline) plus the headline and summary
    r = {k: i for i, (k, _) in enumerate(rows)}
    if not full.get("Concealment category"):
        rows[r["Concealment category"]][1] = "; ".join(seizure.concealment_types(
            " ".join([rows[r["Concealment method"]][1], rows[r["Declared commodity"]][1], text])))
    if not full.get("Cover load / goods used as cover"):
        goods = seizure.cover_goods(" ".join([rows[r["Declared commodity"]][1], rows[r["Concealment method"]][1],
                                              seizure._cover_zone(seizure.fold(text))]))
        rows[r["Cover load / goods used as cover"]][1] = "; ".join(f"{w} ({n})" for n, w in goods)
    if not full.get("Insider signal (staff named as involved)"):
        rows[r["Insider signal (staff named as involved)"]][1] = "; ".join(seizure.insider_roles(text))
    ev["insider_roles"] = [x for x in rows[r["Insider signal (staff named as involved)"]][1].split("; ") if x]
    ev["substances"] = list(dict.fromkeys(re.sub(r"^Suspected ", "", x).capitalize() if x.startswith("Suspected ") else x
                                          for x in rows[r["Substance / item (as reported)"]][1].split("; ") if x))
    ev["concealment_types"] = [x for x in rows[r["Concealment category"]][1].split("; ") if x]
    ev["cover_goods"] = [x.rsplit(" (", 1)[1].rstrip(")") for x in rows[r["Cover load / goods used as cover"]][1].split("; ") if " (" in x]
    ev["specialist"].insert(0, ["Seizure", rows])
    ev["seizures"] = art.get("seizures") if art.get("seizure_rows") is not None else qs
    pick_main_quantities(ev)


def pick_main_quantities(ev):
    """Only one figure per substance and unit counts in the seizure totals: the one in the headline if the headline
    gives one, otherwise the first figure that is not background (a yearly total, an earlier case). Updates (policy,
    statistics) add nothing to the totals."""
    from . import seizure
    qs = ev.get("seizures") or []
    head = {(q["substance"], q["std_unit"]): q["std_qty"] for q in seizure.quantities(ev.get("title", ""), ev.get("lang") or "en")
            if not q["background"]}
    old = (ev.get("title", "").lower().startswith("archived") or
           bool(re.search(r"\b(?:ja teve|ja foram|ja apreend\w*|has had|have had)\b", extract.fold(ev.get("title", "")))))
    done = set()
    for q in qs:
        k = (q.get("substance"), q.get("std_unit"))
        bg = q.get("background", False)
        if k in head:
            ok = abs(q.get("std_qty", 0) - head[k]) < 0.01
        else:
            ok = not bg
        q["main"] = bool(ok and ev.get("kind") == "Incident" and not old and q.get("substance") != "Not reported" and k not in done)
        if q["main"]:
            done.add(k)


def _specialist(ev, art, text):
    """Category-specific details: from the full article when it was read, filled in from the headline otherwise."""
    from . import specialist
    head = specialist.sections(ev, text)
    full = {name: dict(rows) for name, rows in (art.get("specialist") or [])}
    for name, rows in head:
        for row in rows:
            v = full.get(name, {}).get(row[0])
            if v:
                row[1] = v
    return head
