"""Reads a headline (and summary, when there is one) and pulls out the facts.

Everything here is simple word matching: no AI model and no paid service. That keeps it free and
easy to check, but it means the results are leads to verify, not confirmed intelligence.
"""
import re
import unicodedata

from .places import AIRPORTS, COUNTRIES

# ---------------------------------------------------------------------------------------------
# Topics. An article is kept only if it matches at least one topic.
# A word ending in * also matches longer forms (falsif* = falsified, falsification, ...).
# ---------------------------------------------------------------------------------------------
CATEGORIES = {
    "Passport fraud": [
        "fake passport*", "forged passport*", "fraudulent passport*", "counterfeit passport*", "false passport*",
        "falsified passport*", "stolen passport*", "passport fraud", "passport scam", "passport forger*",
        "doctored passport*", "altered passport*", "illegally obtained passport*",
        "pasaporte* falso*", "pasaporte* falsificado*", "pasaporte* robado*",
        "faux passeport*", "passeport* falsifié*", "passaporte* falso*", "passaporte* falsificado*",
    ],
    "Visa and permit fraud": [
        "visa fraud", "fake visa*", "forged visa*", "fraudulent visa*", "counterfeit visa*", "visa scam*",
        "fake work permit*", "fake residence permit*", "forged residence permit*", "fake green card*",
        "sham marriage*", "marriage fraud", "fake visa stamp*", "visa racket", "visa* falsa*",
        "faux visa*", "fraude de visa*", "permiso* de residencia falso*",
    ],
    "Identity and document fraud": [
        "identity fraud", "fake document*", "forged document*", "fraudulent document*", "counterfeit document*",
        "false document*", "fake ID*", "fake identity", "fake identities", "stolen identit*", "fake birth certificate*",
        "forged birth certificate*", "travel document fraud", "fraudulent travel document*", "document fraud",
        "document forger*", "documentos falsos", "documento* falsificado*", "fraude documental", "faux papiers",
        "fraude documentaire", "faux documents", "documentos falsificados", "identidade falsa",
    ],
    "Impostors": [
        "impostor*", "imposter*", "look-alike*", "lookalike*", "someone else's passport",
        "another person's passport", "suplantación de identidad", "usurpation d'identité",
    ],
    "Migrant smuggling": [
        "migrant smuggl*", "human smuggl*", "people smuggl*", "smuggling of migrants", "smuggling migrants",
        "smuggled migrants", "alien smuggling", "tráfico de migrantes", "tráfico ilícito de migrantes",
        "trafic de migrants", "passeur*", "filière d'immigration", "immigration clandestine", "contrabando de migrantes",
        "illegal immigrants arrested", "irregular migrants intercepted", "undocumented migrants",
    ],
    "Human trafficking": [
        "human trafficking", "people trafficking", "trafficking in persons", "trafficking victims", "sex trafficking",
        "trata de personas", "trata de seres humanos", "traite des êtres humains", "tráfico de pessoas",
    ],
    "Immigration enforcement": [
        "immigration fraud", "overstay*", "refused entry", "denied entry", "inadmissible",
        "immigration offence*", "immigration offense*", "immigration violation*", "illegal entry",
        "entered illegally", "border fraud",
    ],
    "Irregular migration": [
        "irregular migra*", "illegal migra*", "migrant boat*", "migrant vessel*", "migrant caravan*", "caravan of migrants",
        "Darien Gap", "Darién", "border crossings", "migrant arrivals", "migrants intercepted", "migrants rescued",
        "migrants detained", "migrants interdicted", "interdicted", "interdiction", "repatriated migrants",
        "migrant surge", "migrant flows", "migration flows", "migration trends", "unauthorized migrants",
        "illegal immigrants", "irregular migrants", "undocumented migrants", "sloop", "asylum seekers",
        "migracion irregular", "migrantes irregulares", "cruces irregulares", "flujo migratorio", "flujos migratorios",
        "migration irreguliere", "migrants intercepte*", "migracao irregular", "migrantes interceptados",
    ],
    "Visa and entry policy": [
        "visa requirement*", "new visa rule*", "visa rule*", "visa policy", "visa policies", "visa-free", "visa free",
        "visa waiver*", "visa exemption*", "visa on arrival", "visa ban*", "visa restriction*", "visa suspension",
        "suspends visa*", "suspended visa*", "visa fee*", "visa regime", "entry requirement*", "entry rule*",
        "entry ban*", "travel ban*", "border closure", "closes border*", "reopens border*", "ETIAS", "Entry/Exit System",
        "entry-exit system", "electronic travel authori*ation", "ETA scheme", "ESTA application*", "ESTA program*", "e-visa", "evisa",
        "immigration policy", "immigration rules", "immigration law", "asylum policy", "work visa*", "student visa*",
        "requisito* de visa", "requisitos de entrada", "exencion de visa", "exigencia de visa", "visado* obligatorio*",
        "nuevas reglas migratorias", "regimen de visas", "obligation de visa", "exemption de visa", "regles d'entree",
        "exigencia de visto", "isencao de visto", "regras de entrada",
    ],
    "Citizenship and naturalisation": [
        "citizenship fraud", "fraudulently obtained citizenship", "citizenship revoked", "revoke* citizenship",
        "revoking citizenship", "stripped of citizenship", "denaturali*ation", "naturali*ation fraud", "fake citizenship",
        "false citizenship", "citizenship certificate*", "citizenship law", "citizenship act", "citizenship rules",
        "citizenship by investment", "citizenship-by-investment", "golden passport*", "golden visa*",
        "economic citizenship", "CBI programme", "CBI program", "passport sales", "selling passports",
        "sale of passports", "birthright citizenship", "dual citizenship", "nacionalidad fraudulenta",
        "ciudadania falsa", "nationalite frauduleuse", "cidadania falsa",
    ],
    "INTERPOL and watch lists": [
        "Interpol", "red notice*", "yellow notice*", "blue notice*", "SLTD", "stolen and lost travel document*",
        "watch list*", "watchlist*", "no-fly list*", "terror list", "terrorist list", "sanctions list",
        "wanted fugitive*", "fugitive arrested", "fugitive captured", "most wanted", "extradit*", "Europol",
        "Ameripol", "Frontex", "IMPACS", "advance passenger information", "passenger name record*",
        "notificacion roja", "difusion roja", "notice rouge", "difusao vermelha", "extradicion", "extradition",
    ],
    "Deportation and returns": [
        "deportation*", "deported", "deportee*", "deporting", "deports", "removal flight*", "repatriation flight*", "forced return*", "returned migrants", "deportacion*",
        "deportad*", "expulse*", "deportacao", "expulsion*",
    ],
    "Border security": [
        "border security", "border control*", "border guard*", "border patrol", "border agency", "border force",
        "border officer*", "coast guard", "e-gate*", "egate*", "biometric border*", "facial recognition",
        "immigration officer*", "immigration officials", "PICA", "seguridad fronteriza", "control fronterizo",
        "controle aux frontieres", "police aux frontieres", "seguranca de fronteira",
    ],
}

# Topics that describe crime. Anything else (policy, security, deportation news) is an "Update", not an incident.
CRIME_TOPICS = {"Passport fraud", "Visa and permit fraud", "Identity and document fraud", "Impostors",
                "Migrant smuggling", "Human trafficking"}
# Broad topics: kept on their own only when something happened (arrest, interception...) or a place we watch is named.
BROAD_TOPICS = {"Immigration enforcement", "Deportation and returns", "Border security"}

# "fake Canadian visas", "forged Nigerian passport": a warning word up to 2 words before a document word.
FAKE_WORDS = ["fake", "forged", "fraudulent", "counterfeit", "false", "falsified", "doctored", "altered", "bogus",
              "phony", "phoney", "stolen", "illegally obtained", "falso", "falsos", "falsa", "falsas", "falsificado",
              "falsificados", "faux", "falsifie", "falsifies"]
PROXIMITY = {
    "Passport fraud": ["passport", "passports"],
    "Visa and permit fraud": ["visa", "visas", "work permit", "work permits", "residence permit", "residence permits",
                              "green card", "green cards", "visa stamp", "visa stamps"],
    "Identity and document fraud": ["id", "ids", "id card", "id cards", "identity card", "identity cards",
                                    "birth certificate", "birth certificates", "documents", "travel documents"],
}

# Words that show something happened (an arrest, a seizure, a conviction).
ACTION_WORDS = [
    "arrest*", "detain*", "intercept*", "seiz*", "charged", "convicted", "sentenced", "jailed", "busted",
    "dismantl*", "nabbed", "caught", "held", "raid*", "indicted", "pleaded guilty", "pleads guilty", "remanded",
    "uncovered", "foiled", "cracked down", "crackdown", "rescued", "stopped",
    "detenid*", "arrestad*", "capturad*", "incautad*", "decomisad*", "desarticulad*", "desmantelad*",
    "aprehendid*", "interpellé*", "arrêté*", "démantelé*", "saisi*", "condamné*", "preso*", "presa*", "detido*",
    "apreendid*", "condenad*",
]

DOC_TYPES = {
    "Passport": ["passport*", "pasaporte*", "passeport*", "passaporte*"],
    "Visa": ["visa", "visas", "vistos"],
    "Residence/work permit": ["residence permit*", "work permit*", "green card*", "permiso de residencia",
                              "titre de séjour", "autorização de residência"],
    "ID card": ["ID card*", "identity card*", "national ID*", "cédula*", "carte d'identité", "carteira de identidade"],
    "Birth certificate": ["birth certificate*", "acta de nacimiento", "acte de naissance", "certidão de nascimento"],
    "Boarding pass/ticket": ["boarding pass*", "air ticket*", "fake ticket*"],
    "Citizenship certificate": ["citizenship certificate*", "naturali*ation certificate*"],
}

NUMBER_WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
                "ten": 10, "eleven": 11, "twelve": 12, "dozen": 12, "dozens": 24, "fifteen": 15, "twenty": 20,
                "thirty": 30, "forty": 40, "fifty": 50, "hundred": 100, "hundreds": 200,
                "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "diez": 10, "veinte": 20, "cien": 100,
                "deux": 2, "trois": 3, "dix": 10, "vingt": 20, "cent": 100}


# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------
def fold(s):
    """Lower-case and remove accents, so 'Pasaporte' and 'pasaporte' match the same way."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.replace("’", "'").lower()


def word_pattern(word):
    """Turn a word from the lists into a regular expression that matches whole words.
    '*' at the end = any ending. '*' in the middle = any single letter (naturali*ation)."""
    w = fold(word).strip()
    prefix = w.endswith("*")
    w = w.rstrip("*")
    parts = [re.escape(p) for p in w.split("*")]
    body = r"\w?".join(parts).replace(r"\ ", r"\s+")
    return r"(?<!\w)" + body + (r"\w*" if prefix else r"(?:e?s)?(?!\w)")


def compile_words(words):
    if not words:
        return None
    return re.compile("|".join(word_pattern(w) for w in words))


def find_words(compiled, text):
    if compiled is None:
        return []
    return sorted({m.group(0) for m in compiled.finditer(text)})


_CAT_RE = {name: compile_words(words) for name, words in CATEGORIES.items()}
_FAKE = "|".join(re.escape(fold(w)).replace(r"\ ", r"\s+") for w in FAKE_WORDS)
_PROX_RE = {name: re.compile(r"(?<!\w)(?:" + _FAKE + r")(?:\s+[\w'-]+){0,2}?\s+(?:"
                             + "|".join(re.escape(n).replace(r"\ ", r"\s+") for n in nouns) + r")(?!\w)")
            for name, nouns in PROXIMITY.items()}
_ACTION_RE = compile_words(ACTION_WORDS)
_DOC_RE = {name: compile_words(words) for name, words in DOC_TYPES.items()}


def _alias_re(alias):
    # all-capital short forms (USA, UK, UAE, DRC) must match in capitals, everything else ignores case
    body = re.escape(alias).replace(r"\ ", r"\s+")
    pat = r"(?<!\w)" + body + r"(?!\w)"
    if alias.replace(".", "").isupper() and len(alias.replace(".", "")) <= 4:
        return re.compile(pat)
    body = re.escape(fold(alias)).replace(r"\ ", r"\s+")
    return re.compile(r"(?<!\w)" + body + r"(?!\w)")


_COUNTRY_RE = [(name, _alias_re(a), a.replace(".", "").isupper() and len(a.replace(".", "")) <= 4)
               for name, aliases in COUNTRIES.items() for a in aliases]
_AIRPORT_RE = [(name, country, _alias_re(a)) for name, (country, aliases) in AIRPORTS.items() for a in aliases]


def find_countries(text):
    """Countries named in the text, in the order they first appear."""
    folded = fold(text)
    hits = []
    for name, rx, exact_case in _COUNTRY_RE:
        m = rx.search(text if exact_case else folded)
        if m:
            hits.append((m.start(), name))
    for _, country, rx in _AIRPORT_RE:          # an airport also tells us the country
        m = rx.search(folded)
        if m:
            hits.append((m.start(), country))
    seen, out = set(), []
    for _, name in sorted(hits):
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def find_airports(text):
    folded = fold(text)
    return sorted({name for name, _, rx in _AIRPORT_RE if rx.search(folded)})


_COUNTRY_ALT = None


def _country_alternation():
    global _COUNTRY_ALT
    if _COUNTRY_ALT is None:
        aliases = sorted({fold(a) for al in COUNTRIES.values() for a in al}, key=len, reverse=True)
        _COUNTRY_ALT = "|".join(re.escape(a).replace(r"\ ", r"\s+") for a in aliases)
    return _COUNTRY_ALT


def _canonical(alias_text):
    a = fold(alias_text)
    for name, aliases in COUNTRIES.items():
        if any(fold(x) == a for x in aliases):
            return name
    return None


def find_route(text):
    """Looks for 'from X to Y', 'X-bound', 'bound for Y', 'en route to Y' and their Spanish/French/Portuguese forms.
    Returns (origin, destination); either can be empty."""
    t = fold(text)
    alt = _country_alternation()
    origin = dest = ""
    m = re.search(r"(?<!\w)(?:from|desde|depuis|vindo de|procedente de|proveniente de|en provenance d[eu']?)\s+(?:the\s+)?(" + alt
                  + r")(?!\w)", t)
    if m:
        origin = _canonical(m.group(1)) or ""
    m = re.search(r"(?<!\w)(?:bound for|en route to|headed to|heading to|destined for|to|hacia|con destino a|rumbo a|"
                  r"vers|a destination de|com destino a)\s+(?:the\s+)?(" + alt + r")(?!\w)", t)
    if m:
        dest = _canonical(m.group(1)) or ""
    if not dest:
        m = re.search(r"(?<!\w)(" + alt + r")-bound(?!\w)", t)
        if m:
            dest = _canonical(m.group(1)) or ""
    if origin == dest:
        dest = "" if origin else dest
    return origin, dest


_NUM = r"(?<!\w)(\d[\d,\.]*|" + "|".join(NUMBER_WORDS) + r")(?!\w)"


def _to_int(s):
    s = fold(s)
    if s in NUMBER_WORDS:
        return NUMBER_WORDS[s]
    s = s.replace(",", "").replace(".", "")
    return int(s) if s.isdigit() else 0


_DOC_COUNT_RE = re.compile(_NUM + r"\s+(?:\w+\s+){0,3}?(?:passports?|visas?|documents?|ids?|identity cards?|"
                           r"pasaportes?|documentos?|passeports?|passaportes?|papiers?)(?!\w)")
_PEOPLE_COUNT_RE = re.compile(_NUM + r"\s+(?:\w+\s+){0,2}?(?:migrants?|people|persons?|victims?|passengers?|"
                              r"suspects?|nationals?|foreigners?|men|women|children|minors?|migrantes?|personas?|"
                              r"victimas?|pasajeros?|hombres|mujeres|extranjeros|personnes?|victimes?|hommes|femmes|"
                              r"etrangers|pessoas?|homens|mulheres|estrangeiros)(?!\w)")


def find_count(rx, text):
    best = 0
    for m in rx.finditer(fold(text)):
        n = _to_int(m.group(1))
        if 1 < n < 1_000_000 and not (1900 <= n <= 2100):   # skip years like "2026"
            best = max(best, n)
    return best


# ---------------------------------------------------------------------------------------------
# main entry point
# ---------------------------------------------------------------------------------------------
def extract(item):
    """item = dict with at least 'title' (and optionally 'summary'). Returns the facts, or None if off-topic."""
    text = f"{item.get('title', '')}. {item.get('summary', '')}"
    folded = fold(text)
    cats = {name: find_words(rx, folded) for name, rx in _CAT_RE.items()}
    for name, rx in _PROX_RE.items():
        cats[name] = sorted(set(cats.get(name, [])) | {m.group(0) for m in rx.finditer(folded)})
    cats = {k: v for k, v in cats.items() if v}
    actions = find_words(_ACTION_RE, folded)
    if actions and re.search(r"(?<!\w)(?:migrant|migrante|immigrant|refugee|asylum seeker)s?(?!\w)", folded):
        cats.setdefault("Irregular migration", ["migrants + " + actions[0]])
    if not cats:
        return None
    countries = find_countries(text)
    if set(cats) <= BROAD_TOPICS and not actions and not countries:
        return None
    crime = bool(set(cats) & CRIME_TOPICS) or (
        bool(actions) and bool(set(cats) & {"Citizenship and naturalisation", "INTERPOL and watch lists",
                                            "Irregular migration", "Immigration enforcement"}))
    origin, dest = find_route(text)
    return {
        "kind": "Incident" if crime else "Update",
        "categories": sorted(cats),
        "matched_words": sorted({w for ws in cats.values() for w in ws}),
        "action": bool(actions),
        "document_types": sorted(n for n, rx in _DOC_RE.items() if rx.search(folded)),
        "countries": countries,
        "airports": find_airports(text),
        "origin": origin,
        "destination": dest,
        "documents_count": find_count(_DOC_COUNT_RE, text),
        "people_count": find_count(_PEOPLE_COUNT_RE, text),
    }
