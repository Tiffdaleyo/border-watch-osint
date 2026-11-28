"""Structured journeys and stated nationality.

Four things are kept apart on purpose, because they mean different things:
  - incident location: where it happened (countries, airports, ports in the record)
  - journey: origin -> transit points (in order) -> intended destination, plus where it was intercepted
  - document issuing country: the country a document claims to be from (specialist fields)
  - nationality: only when the report says it in words ("a Jamaican national", "citizens of Haiti").
    It is never worked out from a name, a route or a document, and it is never used in the risk score.
"""
import re

from . import extract
from .places import AIRPORTS, COUNTRIES

fold = extract.fold

# nationality words -> country. Used only for nationality stated next to a word for a person.
DEMONYMS = {
    "jamaican": "Jamaica", "haitian": "Haiti", "dominican": "Dominican Republic", "cuban": "Cuba", "bahamian": "Bahamas",
    "trinidadian": "Trinidad and Tobago", "barbadian": "Barbados", "bajan": "Barbados", "guyanese": "Guyana",
    "surinamese": "Suriname", "belizean": "Belize", "grenadian": "Grenada", "vincentian": "Saint Vincent and the Grenadines",
    "kittitian": "Saint Kitts and Nevis", "antiguan": "Antigua and Barbuda", "st lucian": "Saint Lucia",
    "saint lucian": "Saint Lucia", "puerto rican": "Puerto Rico", "caymanian": "Cayman Islands",
    "american": "United States", "us": "United States", "u.s.": "United States", "canadian": "Canada", "mexican": "Mexico",
    "british": "United Kingdom", "uk": "United Kingdom",
    "irish": "Ireland", "french": "France", "spanish": "Spain", "german": "Germany", "italian": "Italy", "dutch": "Netherlands",
    "belgian": "Belgium", "portuguese": "Portugal", "swiss": "Switzerland", "greek": "Greece", "polish": "Poland",
    "romanian": "Romania", "albanian": "Albania", "ukrainian": "Ukraine", "russian": "Russia", "turkish": "Turkey",
    "colombian": "Colombia", "venezuelan": "Venezuela", "ecuadorian": "Ecuador", "peruvian": "Peru", "bolivian": "Bolivia",
    "brazilian": "Brazil", "argentine": "Argentina", "argentinian": "Argentina", "chilean": "Chile", "paraguayan": "Paraguay",
    "panamanian": "Panama", "costa rican": "Costa Rica", "nicaraguan": "Nicaragua", "honduran": "Honduras",
    "guatemalan": "Guatemala", "salvadoran": "El Salvador", "salvadorean": "El Salvador",
    "nigerian": "Nigeria", "ghanaian": "Ghana", "kenyan": "Kenya", "south african": "South Africa", "senegalese": "Senegal",
    "malian": "Mali", "guinean": "Guinea", "cameroonian": "Cameroon", "ivorian": "Ivory Coast", "congolese": "Democratic Republic of the Congo",
    "ethiopian": "Ethiopia", "eritrean": "Eritrea", "somali": "Somalia", "sudanese": "Sudan", "egyptian": "Egypt",
    "moroccan": "Morocco", "algerian": "Algeria", "tunisian": "Tunisia", "libyan": "Libya",
    "indian": "India", "pakistani": "Pakistan", "bangladeshi": "Bangladesh", "sri lankan": "Sri Lanka", "nepali": "Nepal",
    "nepalese": "Nepal", "afghan": "Afghanistan", "iranian": "Iran", "iraqi": "Iraq", "syrian": "Syria", "lebanese": "Lebanon",
    "chinese": "China", "vietnamese": "Vietnam", "filipino": "Philippines", "indonesian": "Indonesia", "thai": "Thailand",
    "malaysian": "Malaysia", "korean": "South Korea", "japanese": "Japan", "australian": "Australia",
    # Spanish / French / Portuguese (masculine and feminine forms after folding)
    "jamaiquino": "Jamaica", "jamaiquina": "Jamaica", "haitiano": "Haiti", "haitiana": "Haiti", "cubano": "Cuba", "cubana": "Cuba",
    "dominicano": "Dominican Republic", "dominicana": "Dominican Republic", "venezolano": "Venezuela", "venezolana": "Venezuela",
    "colombiano": "Colombia", "colombiana": "Colombia", "ecuatoriano": "Ecuador", "ecuatoriana": "Ecuador",
    "mexicano": "Mexico", "mexicana": "Mexico", "peruano": "Peru", "peruana": "Peru", "hondureno": "Honduras",
    "hondurena": "Honduras", "guatemalteco": "Guatemala", "guatemalteca": "Guatemala", "nigeriano": "Nigeria",
    "brasileno": "Brazil", "brasilena": "Brazil", "brasileiro": "Brazil", "brasileira": "Brazil", "espanol": "Spain",
    "estadounidense": "United States", "jamaicain": "Jamaica", "jamaicaine": "Jamaica", "haitien": "Haiti", "haitienne": "Haiti",
}
PERSON = (r"(?:nationals?|citizens?|man|men|woman|women|migrants?|passengers?|suspects?|travell?ers?|deportees?|refugees?|"
          r"asylum[- ]seekers?|teen(?:ager)?s?|boys?|girls?|couple|family|families|businessman|businesswoman|students?|"
          r"workers?|fugitives?|mules?|couriers?|drug mules?|smugglers?|traffickers?|victims?|crew(?: members)?|captain|"
          r"pilot|sailors?|fishermen|fisherman|individuals?|persons?|people|accused|defendants?|convicts?|inmates?|applicants?|"
          r"ciudadanos?|ciudadanas?|migrantes?|hombres?|mujer(?:es)?|pasajeros?|pasajeras?|nacionales?|"
          r"ressortissants?|ressortissantes?|cidadaos?|cidadas?)")
_DEM = "|".join(sorted(map(re.escape, DEMONYMS), key=len, reverse=True))
_NUMW = r"(?:\d[\d,]*\s+|(?:a|an|one|two|three|four|five|six|seven|eight|nine|ten|several|dozens of|hundreds of)\s+)?"
_MID = (r"(?:(?:young|elderly|female|male|undocumented|irregular|illegal|suspected|alleged|former|wanted|deported|stranded|"
        r"missing|dual|other|more|fellow)\s+)?")
_NOT_PERSON = r"(?!\w)(?!\s+(?:visas?|permits?|loans?|fees?|accommodation|housing|routes?|numbers?|cap|levy|programme|program|scheme))"
_NAT_RE = re.compile(r"(?<![\w.])(" + _DEM + r")\s+" + _MID + PERSON + _NOT_PERSON)
_NAT_RE2 = re.compile(PERSON + r"\s+(" + _DEM + r")s?(?!\w)")          # Spanish/French order: "ciudadano venezolano"
_COUNTRY_ALT = None
_NAT_OF_RE = None
_NACIONALIDAD_RE = re.compile(r"de nacionalidad (" + _DEM + r")")


def _alt():
    global _COUNTRY_ALT, _NAT_OF_RE
    if _COUNTRY_ALT is None:
        _COUNTRY_ALT = extract._country_alternation()
        _NAT_OF_RE = re.compile(r"(?:nationals?|citizens?|passport holders?|ressortissants?|ciudadanos?)\s+(?:of|from|de|du|d')\s+"
                                r"(?:the\s+)?(" + _COUNTRY_ALT + r")(?!\w)")
    return _COUNTRY_ALT


def nationalities(text):
    """Nationalities stated in words next to a person. Returns country names in order of appearance."""
    _alt()
    t = fold(text)
    hits = []
    for m in _NAT_RE.finditer(t):
        hits.append((m.start(), DEMONYMS[m.group(1)]))
    for m in _NAT_RE2.finditer(t):
        if m.group(1) in DEMONYMS:
            hits.append((m.start(), DEMONYMS[m.group(1)]))
    for m in _NACIONALIDAD_RE.finditer(t):
        hits.append((m.start(), DEMONYMS[m.group(1)]))
    for m in _NAT_OF_RE.finditer(t):
        c = extract._canonical(m.group(1))
        if c:
            hits.append((m.start(), c))
    out = []
    for _, c in sorted(hits):
        if c not in out:
            out.append(c)
    return out[:5]


# ---------------------------------------------------------------------------------------------
# journeys
# ---------------------------------------------------------------------------------------------
def _canon(s):
    return extract._canonical(s) or ""


def transit_points(text):
    alt = _alt()
    rx = re.compile(r"(?<!\w)(?:via|through|transiting|transited|in transit (?:in|through|at)|passing through|by way of|"
                    r"stopover in|layover in|connecting (?:flight )?(?:in|through)|a traves de|pasando por|en transito por|"
                    r"via|en escale a|transitando por|com escala em|con escala en)\s+(?:the\s+)?(" + alt + r")"
                    r"((?:\s*(?:,|and|y|et|e)\s+(?:the\s+)?(?:" + alt + r"))*)(?!\w)")
    out = []
    for m in rx.finditer(fold(text)):
        names = [m.group(1)] + re.findall(r"(" + alt + r")", m.group(2) or "")
        for n in names:
            c = _canon(n)
            if c and c not in out:
                out.append(c)
    return out[:4]


_INTERCEPT_WORDS = (r"(?:intercept\w*|interdict\w*|arrest\w*|detain\w*|(?<!meeting )(?<!meeting was )(?<!conference )(?<!summit )(?<!workshop )(?<!forum )(?<!event )(?<!talks )held|seiz\w*|caught|stopped|apprehend\w*|nabbed|"
                    r"captur\w*|refused entry|denied entry|turned back|rescu\w*|busted|deten\w*|detien\w*|interceptad[oa]s?|"
                    r"intercepta[n]?|aprehend\w*|arrestad[oa]s?|incaut\w*|decomis\w*|rescat\w*|interpell\w*|apreend\w*|"
                    r"aangehouden|houdt\s+\w+\s+\w*\s*aan|festgenommen)")
_STOP_RE = re.compile(r"(?<!\w)" + _INTERCEPT_WORDS)
NEAR = 120      # characters either side of the place name


def _stopped_near(t, words):
    """True when a word for stopping someone or something (arrested, seized, intercepted...) is close to one of the place's names."""
    for w in words:
        for m in re.finditer(r"(?<!\w)" + re.escape(fold(w)).replace(r"\ ", r"\s+") + r"(?!\w)", t):
            if re.search(r"(?<!\w)(?:from|departing|left|desde|saindo de|partindo de|depuis)\s+(?:\S+\s+){0,4}$", t[max(0, m.start() - 40):m.start()]):
                continue       # "flew in from Guarulhos": where the journey started, not where it was stopped
            if _STOP_RE.search(t[max(0, m.start() - NEAR):m.end() + NEAR]):
                return True
    return False


def interception(text, ev):
    """Where it was stopped. Only when the report says someone or something was stopped there: 'intercepted in/at/off X',
    or an airport, seaport or crossing named close to a word such as arrested, seized or intercepted.
    A place that is only mentioned (a meeting, a network, a new system at an airport) is not an interception."""
    alt = _alt()
    t = fold(text)
    m = re.search(r"(?<!\w)" + _INTERCEPT_WORDS + r"\s+(?:\w+\s+){0,3}?(?:at|in|off|near|on arrival in|upon arrival in|en|a|no|na|op)\s+"
                  r"(?:the\s+)?(?:coast of\s+)?(" + alt + r")(?!\w)", t)
    country = _canon(m.group(1)) if m else ""
    if ev.get("kind") == "Incident":
        from .record import PORTS, CROSSINGS, port_label
        from .ports import PORTS as _PL
        port_country = {port_label(x): x["country"] for x in _PL}
        loc = ev.get("location") or {}
        named = [(a, AIRPORTS[a][1] + [a.split(" (")[0]]) for a in ev.get("airports") or [] if a in AIRPORTS]
        named += [(p, PORTS.get(p, [])) for p in loc.get("ports", [])]
        named += [(c, CROSSINGS.get(c, [])) for c in loc.get("crossings", [])]
        for where, words in named:
            if not _stopped_near(t, words):
                continue
            ap_country = AIRPORTS[where][0] if where in AIRPORTS else port_country.get(where, "")
            if not ap_country:     # a seaport or crossing: use the country named with it, if any
                ap_country = next((c for c in ev.get("countries", []) if fold(c) in fold(where)), "") or country
            return f"{where}" + (f" ({ap_country})" if ap_country and ap_country not in where else ""), ap_country
    return country, country


def build(ev, text, from_article):
    origin, dest = ev.get("origin", ""), ev.get("destination", "")
    if origin and origin == dest:
        dest = ""
    tr = [c for c in transit_points(text) if c not in (origin, dest)]
    inter, inter_country = interception(text, ev)
    n = sum(bool(x) for x in (origin, dest))
    if origin and dest:
        comp = "Complete"
    elif origin or dest or tr:
        comp = "Partial"
    else:
        comp = "Not reported"
    basis = ("Explicitly stated in article" if from_article else "Stated in headline or summary") if (n or tr) else \
            ("Place of interception stated in report" if inter else "")
    return {"origin": origin, "transit": tr, "destination": dest, "interception": inter,
            "interception_country": inter_country, "completeness": comp, "basis": basis}


def describe(j):
    """'Jamaica → Panama → Spain', or 'Origin: Jamaica; destination not reported'."""
    if not j:
        return ""
    o, d, tr = j.get("origin"), j.get("destination"), j.get("transit") or []
    if o and d:
        return " → ".join([o] + tr + [d])
    parts = []
    if o:
        parts.append(f"Origin: {o}")
    if tr:
        parts.append("transit: " + ", ".join(tr))
    if d:
        parts.append(f"Destination: {d}")
    if not parts:
        return ""
    if not o:
        parts.append("origin not reported")
    if not d:
        parts.append("destination not reported")
    s = "; ".join(parts)
    return s[0].upper() + s[1:]
