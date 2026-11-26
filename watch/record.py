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
    "Cash couriers", "Wildlife smuggling", "Aviation security", "Cargo operations", "INTERPOL and watch lists",
    "Irregular migration", "Immigration enforcement", "Deportation and returns", "Citizenship and naturalisation",
    "Border security", "Border technology", "Visa and entry policy", "Health travel rules",
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


def outcome(text):
    folded = extract.fold(text)
    return next((n for n, rx in _OUT_RE if rx.search(folded)), "")


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
PORTS = {
    "Kingston Wharves / Port of Kingston": ["Kingston Wharves", "Port of Kingston", "Port Bustamante", "Kingston Freeport"],
    "Montego Bay Freeport": ["Montego Bay Freeport", "Montego Bay port"], "Port of Spain": ["Port of Spain port"],
    "Caucedo (DR)": ["Caucedo"], "Freeport (Bahamas)": ["Freeport Container Port", "Grand Bahama port"],
    "Colon / Manzanillo (Panama)": ["Colon Free Zone", "Manzanillo International Terminal", "port of Colon"],
    "Cartagena (Colombia)": ["port of Cartagena", "Cartagena port"], "Buenaventura (Colombia)": ["Buenaventura"],
    "Santa Marta (Colombia)": ["port of Santa Marta"], "Guayaquil (Ecuador)": ["port of Guayaquil", "Guayaquil port"],
    "Santos (Brazil)": ["port of Santos", "Santos port"], "Manzanillo (Mexico)": ["port of Manzanillo"],
    "Lazaro Cardenas (Mexico)": ["Lazaro Cardenas"], "Port Everglades (US)": ["Port Everglades"],
    "PortMiami (US)": ["PortMiami", "Port of Miami"], "Rotterdam": ["port of Rotterdam", "Rotterdam port"],
    "Antwerp": ["port of Antwerp", "Antwerp port"], "Algeciras": ["Algeciras"], "Valencia": ["port of Valencia"],
    "Le Havre": ["Le Havre"], "Hamburg": ["port of Hamburg"], "Gioia Tauro": ["Gioia Tauro"],
    "Felixstowe": ["Felixstowe"], "Southampton": ["port of Southampton"], "Tema (Ghana)": ["Tema port", "port of Tema"],
    "Apapa / Tin Can (Lagos)": ["Apapa", "Tin Can Island"], "Durban": ["port of Durban", "Durban harbour"],
    "Mombasa": ["port of Mombasa"],
}
CROSSINGS = {
    "Darien Gap (Colombia–Panama)": ["Darien Gap", "Darien", "Darién"], "US–Mexico border": ["southern border", "US-Mexico border",
    "U.S.-Mexico border", "Rio Grande", "El Paso", "San Ysidro", "Tijuana"], "Ceuta / Melilla": ["Ceuta", "Melilla"],
    "Lampedusa": ["Lampedusa"], "English Channel": ["English Channel", "Calais", "small boats crossing"],
    "Canary Islands route": ["Canary Islands", "Islas Canarias"], "Evros (Greece–Turkey)": ["Evros"],
    "Mona Passage (DR–Puerto Rico)": ["Mona Passage"], "Haiti–DR border": ["Dajabon", "Dajabón", "Haitian-Dominican border"],
}
COUNTRY_NAMES = {extract.fold(a) for name, al in COUNTRIES.items() for a in al if extract.fold(a) == extract.fold(name)} | \
                {extract.fold(n) for n in COUNTRIES}


def _hits(table, text):
    folded = extract.fold(text)
    out = []
    for name, words in table.items():
        if any(re.search(r"(?<!\w)" + re.escape(extract.fold(w)) + r"(?!\w)", folded) for w in words):
            out.append(name)
    return out


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
                          "date": ev.get("date", ""), **({"official": True} if ev.get("official") else {})}]
    elif ev.get("source_url"):
        ev["sources"][0]["url"] = ev["source_url"]


def load_reviews(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("reviews") or {}


EDITABLE = {"title", "primary_category", "categories", "event_date", "event_date_quality", "countries", "origin",
            "destination", "transit", "interception", "nationality", "transport_mode", "outcome", "agencies",
            "summary_text", "level", "note"}


def apply_review(ev, reviews):
    r = reviews.get(ev.get("event_id")) or {}
    status = str(r.get("status", "")).lower()
    if status in ("reviewed", "corrected", "excluded"):
        ev["review_status"] = status.capitalize()
        ev["review_note"] = r.get("note", "")
        ev["review_by"] = r.get("by", "")
        for k, v in (r.get("corrections") or {}).items():
            if k in EDITABLE:
                ev[k] = v
        if r.get("corrections"):
            ev["review_status"] = "Corrected"
            c = r["corrections"]
            if "categories" in c and "primary_category" not in c:
                ev["primary_category"] = primary_category(ev["categories"])
            ev["tags"] = [x for x in ev.get("categories", []) if x != ev.get("primary_category")]
            ev["groups"] = extract.groups_of(ev.get("categories", []))
    else:
        ev["review_status"] = "Awaiting review" if (ev.get("level") == "High" or ev.get("home")) else "Automatically collected"


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


def build(ev, site, reviews):
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
    ev["location"] = art.get("location") or location(text)
    ev["transport_mode"] = art.get("transport") or transport_mode(text)
    ev["outcome"] = (art.get("outcome") or outcome(text)) if ev.get("kind") == "Incident" else ""
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
    ev["nationality"] = list(dict.fromkeys(journey.nationalities(text) + (art.get("nationality") or [])))[:5]
    apply_review(ev, reviews)
    # the journey is built after the review, so a corrected origin, destination or transit shows up in it
    j = journey.build(ev, text, bool(art.get("read")))
    if art.get("read"):
        j["transit"] = list(dict.fromkeys(j["transit"] + [c for c in art.get("transit", []) if c not in (ev.get("origin"), ev.get("destination"))]))[:4]
        if not j["interception"] and art.get("interception"):
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
    from . import privacy
    privacy.apply(ev)
    return ev


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
