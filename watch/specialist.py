"""Specialist fields: extra details captured only for the categories they belong to.

Same rule as the rest of the record: a value is filled only when the report states it; otherwise the website
shows "Not reported". Facilitators are recorded by role ("travel agent", "boat captain"), never by name.
"""
import re

from . import extract
from .places import COUNTRIES

W = extract.compile_words
fold = extract.fold

# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------
def _labels(table, text):
    """table = [(label, [words])]; returns the labels whose words appear."""
    t = fold(text)
    return [lab for lab, rx in table if rx.search(t)]


def _table(pairs):
    return [(lab, W(words)) for lab, words in pairs]


def _first(rx, text, group=1, limit=110):
    m = rx.search(text)
    if not m:
        return ""
    s = re.sub(r"\s+", " ", m.group(group)).strip(" ,;:.")
    return s[:limit].rsplit(" ", 1)[0] + "…" if len(s) > limit else s


# Adjectives used ONLY for the country that issued a document ("fake Canadian visas" = a document claiming to be
# Canadian). They are never used to describe a person, and nationality is never recorded.
ISSUER_ADJ = {
    "jamaican": "Jamaica", "american": "United States", "us": "United States", "u.s.": "United States",
    "canadian": "Canada", "british": "United Kingdom", "uk": "United Kingdom", "schengen": "Schengen area",
    "french": "France", "spanish": "Spain", "german": "Germany", "italian": "Italy", "dutch": "Netherlands",
    "belgian": "Belgium", "portuguese": "Portugal", "irish": "Ireland", "greek": "Greece", "swiss": "Switzerland",
    "nigerian": "Nigeria", "ghanaian": "Ghana", "kenyan": "Kenya", "south african": "South Africa",
    "indian": "India", "pakistani": "Pakistan", "bangladeshi": "Bangladesh", "chinese": "China",
    "mexican": "Mexico", "colombian": "Colombia", "venezuelan": "Venezuela", "brazilian": "Brazil",
    "haitian": "Haiti", "dominican": "Dominican Republic", "cuban": "Cuba", "guyanese": "Guyana",
    "trinidadian": "Trinidad and Tobago", "barbadian": "Barbados", "bahamian": "Bahamas", "panamanian": "Panama",
    "honduran": "Honduras", "guatemalan": "Guatemala", "salvadoran": "El Salvador", "ecuadorian": "Ecuador",
    "peruvian": "Peru", "turkish": "Turkey", "israeli": "Israel", "australian": "Australia",
    "japanese": "Japan", "korean": "South Korea", "emirati": "United Arab Emirates", "saudi": "Saudi Arabia",
    "vincentian": "St Vincent and the Grenadines", "kittitian": "St Kitts and Nevis", "lucian": "Saint Lucia",
    "grenadian": "Grenada", "antiguan": "Antigua and Barbuda", "dominica": "Dominica",
}
_DOCWORD = r"(?:passports?|visas?|residence permits?|work permits?|id cards?|identity cards?|green cards?|birth certificates?|travel documents?)"
_ISSUER_RE = re.compile(r"(?<![\w.])(" + "|".join(sorted(map(re.escape, ISSUER_ADJ), key=len, reverse=True))
                        + r")\s+(?:[a-z-]+\s+)?" + _DOCWORD + r"(?!\w)")
_COUNTRY_ALT = "|".join(sorted({re.escape(fold(n)) for n in COUNTRIES}, key=len, reverse=True))
_ISSUER_RE2 = re.compile(r"(?<!\w)(" + _COUNTRY_ALT + r")(?:'s)?\s+" + _DOCWORD + r"(?!\w)")


def issuing_countries(text):
    t = fold(text)
    out = [ISSUER_ADJ[m.group(1)] for m in _ISSUER_RE.finditer(t)]
    for m in _ISSUER_RE2.finditer(t):
        name = next((n for n in COUNTRIES if fold(n) == m.group(1)), "")
        if name:
            out.append(name)
    return list(dict.fromkeys(out))[:4]


DETECTION = _table([
    ("At check-in", ["check-in", "check in counter", "checking in"]),
    ("At the boarding gate", ["boarding gate", "at the gate", "while boarding", "before boarding"]),
    ("Departure immigration / exit control", ["departure immigration", "exit control", "departure hall", "outbound passengers",
                                             "trying to leave", "attempting to leave", "while leaving"]),
    ("Arrival immigration", ["on arrival", "upon arrival", "arriving passenger*", "arrival hall", "immigration counter",
                             "immigration desk", "primary inspection", "secondary inspection", "after landing", "al llegar"]),
    ("In transit", ["in transit", "transit passenger*", "transit area", "connecting flight"]),
    ("Baggage / customs examination", ["baggage", "luggage", "suitcase", "customs examination", "x-ray", "scanner",
                                       "sniffer dog*", "canine"]),
    ("Visa or document application", ["visa application", "application centre", "application center", "embassy",
                                      "consulate", "applied for", "passport office", "registry"]),
    ("Mail / parcel inspection", ["parcel*", "mail centre", "mail center", "postal", "courier"]),
    ("Cargo examination", ["container*", "cargo shed", "cargo terminal", "shipment", "consignment"]),
    ("At sea / interdiction", ["intercepted at sea", "interdicted", "coast guard", "at sea", "off the coast"]),
    ("Land border / checkpoint", ["checkpoint", "land border", "border crossing"]),
    ("Inland / after entry", ["raid*", "search warrant", "at a house", "at a residence", "workplace", "traffic stop"]),
])

DOC_METHOD = _table([
    ("Counterfeit (fully false document)", ["counterfeit", "fake passport*", "fake visa*", "fake document*", "fake id*",
                                            "bogus", "phony", "falso*", "faux"]),
    ("Forged / altered genuine document", ["forged", "altered", "doctored", "tampered", "falsified", "photo substitut*",
                                           "page substitut*", "data page", "manipulated", "falsificad*", "falsifie*"]),
    ("Stolen blank documents", ["stolen blank*", "blank passport*", "blank booklet*", "blank visa*", "blank document*"]),
    ("Stolen or lost genuine document", ["stolen passport*", "lost passport*", "reported stolen", "reported lost",
                                         "pasaporte* robado*"]),
    ("Fraudulently obtained genuine document", ["fraudulently obtained", "illegally obtained", "obtained using false",
                                                "obtained with fake", "obtained fraudulently", "genuine passport* obtained"]),
    ("Impostor (someone else's genuine document)", ["impostor*", "imposter*", "look-alike*", "lookalike*",
                                                    "someone else's passport", "another person's passport",
                                                    "belonging to another", "belonging to someone else"]),
    ("Document production / factory", ["document factory", "forgery workshop", "printing equipment", "printers",
                                       "laminat*", "holograms", "forgery lab", "taller de falsificacion"]),
])
BLANK = W(["blank passport*", "blank booklet*", "blank visa*", "blank document*", "blank id card*", "blank stickers",
           "unissued passport*", "pasaportes en blanco"])

PERMIT_TYPE = _table([
    ("Tourist / visitor visa", ["tourist visa*", "visitor visa*", "visit visa*", "b1/b2", "b-1/b-2", "travel visa*"]),
    ("Student visa", ["student visa*", "study permit*", "f-1 visa*"]),
    ("Work visa / permit", ["work visa*", "work permit*", "employment visa*", "h-1b", "h-2a", "h-2b", "skilled worker visa*",
                            "seasonal worker*", "farm work programme", "farm work program"]),
    ("Residence permit / green card", ["residence permit*", "residency permit*", "green card*", "permanent residen*",
                                       "residence card*"]),
    ("Schengen visa", ["schengen visa*"]),
    ("Transit visa", ["transit visa*"]),
    ("Electronic travel authorisation / e-visa", ["eta", "esta", "etias", "e-visa*", "evisa*", "electronic travel authori*ation"]),
    ("Family / spouse visa", ["spouse visa*", "family visa*", "fiance visa*", "k-1 visa*"]),
    ("Asylum / refugee status", ["asylum", "refugee status"]),
])
VISA_METHOD = _table([
    ("Forged visa or stamp", ["fake visa*", "forged visa*", "counterfeit visa*", "fake visa stamp*", "fake visa sticker*",
                              "forged stamp*", "visa* falsa*", "faux visa*"]),
    ("Forged approval or letter", ["fake approval*", "forged approval*", "fake approval letter*", "fake offer letter*",
                                   "fake job offer*", "fake invitation letter*", "forged letter*", "fake lmia", "fake sponsorship"]),
    ("Fraudulent supporting documents", ["fake bank statement*", "forged bank statement*", "fraudulent supporting",
                                         "fake supporting", "false supporting", "fake employment letter*", "fake degree*",
                                         "fake diploma*", "fake certificate*"]),
    ("Fake agent, consultant or website", ["fake agent*", "bogus agent*", "fake consultant*", "unlicensed consultant*",
                                           "ghost consultant*", "fake website*", "scam website*", "visa scam*",
                                           "travel agen* arrested", "recruit* scam*"]),
    ("Bribery or insider issue", ["bribe*", "bribery", "corrupt*", "insider*", "embassy employee*", "consular employee*"]),
    ("Sham marriage or false relationship", ["sham marriage*", "marriage fraud", "marriage of convenience", "fake marriage*"]),
])

FACILITATORS = _table([
    ("Smuggling network / ring", ["smuggling network*", "smuggling ring*", "smuggling syndicate*", "criminal network*",
                                  "criminal organi*ation*", "gang", "cartel", "red de trafico", "filiere"]),
    ("Smugglers / guides", ["smuggler*", "coyote*", "people smuggler*", "passeur*", "guide*", "pollero*"]),
    ("Boat captain / crew", ["captain", "skipper", "boat operator*", "crew", "capitan"]),
    ("Driver / transporter", ["driver*", "transporter*", "chofer*"]),
    ("Travel agent / recruiter", ["travel agent*", "travel agency", "recruiter*", "recruitment agen*", "agencia de viajes"]),
    ("Document supplier / forger", ["forger*", "document supplier*", "document vendor*", "falsificador*"]),
    ("Corrupt official / insider", ["corrupt official*", "corrupt officer*", "airport worker*", "airline employee*",
                                    "immigration officer*", "customs officer*", "insider*"]),
    ("Accommodation / safe house", ["safe house*", "stash house*", "casa de seguridad"]),
])
_FEE_RE = re.compile(
    r"(?<!\w)((?:us\$|usd|\$|€|£|eur|gbp|j\$|jmd|cad|c\$|mxn|n)\s?\d[\d,.]*(?:\s?(?:million|thousand|k))?"
    r"|\d[\d,.]*\s?(?:dollars|euros|pounds|usd|eur|gbp|jmd|pesos|naira))(?:\s+(?:each|per person|a head|per head|per migrant))?",
    re.I)
_FEE_CONTEXT = W(["paid", "selling", "sold", "sells", "sale", "pay", "paying", "charged", "charging", "fee*", "cost", "costs", "price", "each", "per person",
                  "per head", "pagaron", "cobraban", "payaient"])


def fees(text):
    """Amounts paid to smugglers or agents, only when a payment word is right next to the amount."""
    out = []
    for m in _FEE_RE.finditer(text):
        window = fold(text[max(0, m.start() - 60): m.end() + 25])
        if _FEE_CONTEXT.search(window):
            out.append(m.group(0).strip())
    return list(dict.fromkeys(out))[:3]


_TRANSIT_RE = None


def transit(text):
    global _TRANSIT_RE
    if _TRANSIT_RE is None:
        _TRANSIT_RE = re.compile(r"(?<!\w)(?:via|through|transiting|in transit (?:in|through)|passing through|by way of|a traves de|"
                                 r"pasando por|en transito por|en escale a|transitando por)\s+(?:the\s+)?(" + _COUNTRY_ALT + r")(?!\w)")
    out = []
    for m in _TRANSIT_RE.finditer(fold(text)):
        name = next((n for n in COUNTRIES if fold(n) == m.group(1)), "")
        if name:
            out.append(name)
    return list(dict.fromkeys(out))[:3]


# victims: keep "potential/suspected" separate from "identified/confirmed/rescued", as the source says it
_NUM = r"(\d[\d,]*|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|dozens of|hundreds of)"
_POT_RE = re.compile(_NUM + r"\s+(?:potential|suspected|possible|presumed|alleged)\s+(?:human\s+)?(?:trafficking\s+)?victims")
_IDF_RE = re.compile(_NUM + r"\s+(?:identified\s+|confirmed\s+|rescued\s+)?(?:human\s+)?(?:trafficking\s+)?victims"
                     r"(?:\s+(?:were\s+)?(?:identified|rescued|freed|confirmed))?")
_IDF2_RE = re.compile(r"(?:identified|rescued|freed)\s+" + _NUM + r"\s+(?:\w+\s+)?(?:victims|people|women|children|minors|girls|boys)")


def victims(text):
    t = fold(text)
    m = _POT_RE.search(t)
    pot = m.group(0) if m else ""
    idf = ""
    for rx in (_IDF2_RE, _IDF_RE):
        for m in rx.finditer(t):
            if not re.search(r"potential|suspected|possible|presumed|alleged", m.group(0)):
                idf = m.group(0)
                break
        if idf:
            break
    return pot, idf


REFERRAL = W(["referred to", "victim support", "victim assistance", "shelter*", "safe house", "social services",
              "counselling", "counseling", "repatriated", "protection services", "ngo", "iom", "albergue*", "refugio*"])

PROGRAMME = _table([
    ("Citizenship by investment", ["citizenship by investment", "citizenship-by-investment", "cbi programme", "cbi program",
                                   "economic citizenship", "golden passport*", "passport sales", "selling passports"]),
    ("Residence by investment / golden visa", ["golden visa*", "residence by investment", "investor visa*", "eb-5"]),
    ("Naturalisation", ["naturali*ation", "naturali*ed", "citizenship test", "citizenship ceremony"]),
    ("Citizenship by descent / birth", ["by descent", "birthright", "birth certificate*", "late registration"]),
    ("Marriage or family route", ["marriage", "spouse", "family reunification"]),
    ("Asylum / refugee route", ["asylum", "refugee"]),
    ("Permanent residence", ["permanent residen*", "green card*", "indefinite leave"]),
])
STAGE = _table([
    ("At application", ["applied", "application", "applicant*", "submitted"]),
    ("At interview", ["interview"]),
    ("After grant (revocation)", ["revoked", "revoke*", "stripped of", "denaturali*", "cancelled citizenship",
                                  "rescinded", "annulled"]),
    ("At renewal", ["renewal", "renewing"]),
    ("At the border (use of the document)", ["at the airport", "at the border", "on arrival", "at immigration"]),
])
MISREP = _table([
    ("False identity", ["false identity", "fake identity", "assumed identity", "another person's identity", "stolen identity"]),
    ("Concealed criminal record", ["criminal record", "criminal history", "concealed", "failed to disclose", "war crimes"]),
    ("Sham marriage", ["sham marriage*", "marriage fraud", "marriage of convenience", "fake marriage*"]),
    ("False residence or presence", ["false address*", "did not live", "residence requirement", "physical presence"]),
    ("False or forged supporting documents", ["fake document*", "forged document*", "false document*", "fraudulent document*",
                                              "fake certificate*", "forged certificate*"]),
    ("Source of funds", ["source of funds", "money laundering", "due diligence"]),
])
ADMIN_OUTCOME = _table([
    ("Citizenship or status revoked", ["revoked", "stripped of", "denaturali*", "cancelled", "rescinded", "annulled"]),
    ("Application refused", ["refused", "rejected", "denied"]),
    ("Deported / removed", ["deported", "removed from", "deportation"]),
    ("Programme suspended or changed", ["suspended", "paused", "overhaul*", "reform*", "tightened"]),
])

ROLE = _table([
    ("Customs officer", ["customs officer*", "customs official*", "customs agent*", "customs employee*", "aduanero*",
                         "funcionario* de aduana*", "douanier*"]),
    ("Immigration officer", ["immigration officer*", "immigration official*", "immigration agent*", "border agent*",
                             "border officer*", "border guard*", "cbp officer*", "agente* de migracion"]),
    ("Police officer", ["police officer*", "policeman", "policemen", "cop", "cops", "constable*", "policia*"]),
    ("Military / coast guard", ["soldier*", "coast guard", "navy", "marine*", "military officer*"]),
    ("Airport worker", ["airport worker*", "airport employee*", "airport staff", "ground staff", "ramp agent*",
                        "baggage handler*", "cleaner*", "security screener*", "screener*", "tsa officer*"]),
    ("Airline employee", ["airline employee*", "airline staff", "flight attendant*", "cabin crew", "pilot*"]),
    ("Port / wharf worker", ["port worker*", "dock worker*", "dockworker*", "stevedore*", "wharf worker*", "port employee*"]),
    ("Embassy / consular staff", ["embassy employee*", "embassy staff", "consular officer*", "consular employee*"]),
    ("Registry / passport office staff", ["registry", "passport office", "civil registry", "registrar"]),
])
CONDUCT = _table([
    ("Bribery", ["bribe*", "bribery", "kickback*", "soborno*", "coima*"]),
    ("Helping drugs through", ["cocaine", "drugs", "narcotic*", "marijuana", "ganja"]),
    ("Helping people through", ["smuggl* migrants", "human smuggling", "let passengers", "waved through", "allowed passengers"]),
    ("Issuing or selling documents", ["issued passports", "sold passports", "issuing documents", "selling visas", "sold visas"]),
    ("Tag switching / baggage interference", ["tag switch*", "baggage tag*", "switched tags"]),
    ("Leaking information", ["leaked", "tipped off", "sharing information"]),
    ("Security breach", ["security breach", "breach", "unauthori*ed access", "stowaway*"]),
])
DISCIPLINE = _table([
    ("Convicted / sentenced", ["convicted", "sentenced", "pleaded guilty", "pleads guilty", "jailed"]),
    ("Charged", ["charged", "indicted"]),
    ("Arrested", ["arrested", "detained"]),
    ("Suspended / interdicted", ["suspended", "interdicted", "placed on leave", "relieved of duty"]),
    ("Dismissed", ["dismissed", "fired", "sacked", "terminated"]),
    ("Under investigation", ["under investigation", "investigating", "probe"]),
])

NOTICE = _table([
    ("INTERPOL Red Notice", ["red notice*", "notificacion roja", "alerta roja", "notice rouge", "difusao vermelha"]),
    ("INTERPOL Yellow Notice (missing person)", ["yellow notice*"]),
    ("INTERPOL Blue Notice", ["blue notice*"]),
    ("INTERPOL Diffusion", ["diffusion"]),
    ("Arrest warrant", ["arrest warrant*", "warrant for his arrest", "warrant for her arrest", "orden de captura",
                        "orden de arresto", "mandat d'arret"]),
    ("Extradition request", ["extradition request", "requested extradition", "seeks extradition", "seeking extradition",
                             "solicitud de extradicion"]),
    ("Watch list / alert", ["watch list", "watchlist", "no-fly list", "border alert", "stop list", "lookout"]),
])
_BASIS_RE = re.compile(r"wanted (?:in [a-z ]{3,30} )?(?:for|on charges of|in connection with|over)\s+([a-z ,'-]{4,90})")
WANTED_OUTCOME = _table([
    ("Extradited", ["extradited", "extraditado*", "extrade*"]),
    ("Deported / handed over", ["deported", "handed over", "expelled", "deportado*", "entregado*"]),
    ("Arrested", ["arrested", "detained", "caught", "captured", "apprehended", "detenido*", "capturado*"]),
    ("Extradition pending", ["extradition proceedings", "awaiting extradition", "extradition hearing", "fighting extradition"]),
    ("Released", ["released", "freed", "granted bail", "bail"]),
])

AUTHORITY = [
    "Home Office", "UK Visas and Immigration", "IRCC", "Immigration, Refugees and Citizenship Canada", "State Department",
    "Department of State", "DHS", "Department of Homeland Security", "USCIS", "CBP", "European Commission",
    "European Union", "European Parliament", "Council of the EU", "Frontex", "PICA", "Ministry of Foreign Affairs",
    "Ministry of Home Affairs", "Ministry of National Security", "Ministry of the Interior", "Interior Ministry",
    "Foreign Ministry", "Department of Home Affairs", "Immigration Department", "Immigration Service",
    "Migracion Colombia", "Instituto Nacional de Migracion", "CARICOM", "IMPACS", "White House", "President",
    "Prime Minister", "Cabinet", "Parliament", "Congress",
]
_AUTH_RE = [(a, re.compile(r"(?<!\w)" + re.escape(fold(a)) + r"(?!\w)")) for a in AUTHORITY]
_AFFECTED_RE = re.compile(r"(?<!\w)(?:for|affects?|affecting|applies to|apply to|requires?|required for)\s+((?:citizens|nationals|"
                          r"travell?ers|visitors|holders|passport holders|students|workers|tourists|passengers|migrants|"
                          r"applicants|residents)[a-z ,'-]{0,70})")
_EFFECTIVE_RE = re.compile(r"(?:from|starting|effective|takes effect|take effect|comes into force|come into force|"
                           r"enter into force|enters into force|begins?|beginning|as of|launch(?:es|ed)? on|"
                           r"a partir del?|desde el|a compter du)\s+(?:on\s+)?((?:\w+\s+){0,1}\w+\s+\d{1,2}(?:,?\s+20\d\d)?|"
                           r"\d{1,2}\s+(?:de\s+)?\w+(?:\s+(?:de\s+)?20\d\d)?|\w+\s+20\d\d)")
_EXCEPT_RE = re.compile(r"(?<!\w)(?:except(?:ion)?s? (?:for|are)|exempt(?:ed|ion)? (?:from|for)?|with the exception of|"
                        r"excluding|will not apply to|does not apply to)\s+([a-z ,'-]{4,90})")
STATUS = _table([
    ("Withdrawn / reversed", ["withdrawn", "withdraws", "scrapped", "scraps", "reversed", "reverses", "revoked the",
                              "cancelled the", "u-turn", "backtrack*", "drops plan*"]),
    ("Delayed / postponed", ["delayed", "delays", "postponed", "postpones", "pushed back", "deferred", "put on hold",
                             "aplazad*"]),
    ("Proposed / planned", ["proposed", "proposes", "proposal", "plans to", "planning to", "considering", "draft",
                            "consultation", "may introduce", "will introduce", "announces plan*"]),
    ("Active / in force", ["takes effect", "took effect", "comes into force", "came into force", "now in force",
                           "now required", "now need", "effective immediately", "has introduced", "introduces",
                           "launched", "begins", "began", "starts", "started", "implemented", "enters into force",
                           "entra en vigor", "entro en vigor"]),
])
# official pages to check a rule (country -> link); a link is shown only for a country named in the report
OFFICIAL = {
    "United States": "https://travel.state.gov/content/travel/en/us-visas.html",
    "United Kingdom": "https://www.gov.uk/check-uk-visa",
    "Canada": "https://www.canada.ca/en/immigration-refugees-citizenship/services/visit-canada.html",
    "Jamaica": "https://www.pica.gov.jm",
    "Schengen area": "https://travel-europe.europa.eu/",
    "Ireland": "https://www.irishimmigration.ie/",
    "Australia": "https://immi.homeaffairs.gov.au/",
    "New Zealand": "https://www.immigration.govt.nz/",
    "Mexico": "https://www.gob.mx/inm",
    "Colombia": "https://www.migracioncolombia.gov.co/",
    "Panama": "https://www.migracion.gob.pa/",
    "Dominican Republic": "https://migracion.gob.do/",
    "Trinidad and Tobago": "https://immigration.gov.tt/",
    "Barbados": "https://immigration.gov.bb/",
    "Bahamas": "https://www.immigration.gov.bs/",
    "Cayman Islands": "https://www.gov.ky/immigration",
}
EU_SCHENGEN = {"France", "Spain", "Germany", "Italy", "Netherlands", "Belgium", "Portugal", "Greece", "Austria", "Sweden",
               "Switzerland", "Poland", "Czech Republic", "Denmark", "Finland", "Norway", "Iceland", "Hungary", "Croatia"}
EU_WORDS = W(["schengen", "etias", "entry/exit system", "entry-exit system", "european union", "eu"])


def official_links(countries, text):
    out = []
    if EU_WORDS.search(fold(text)) or set(countries) & EU_SCHENGEN:
        out.append(OFFICIAL["Schengen area"])
    out += [OFFICIAL[c] for c in countries if c in OFFICIAL]
    return list(dict.fromkeys(out))[:3]


# ---------------------------------------------------------------------------------------------
# which sections apply to which topics
# ---------------------------------------------------------------------------------------------
SECTIONS = [
    ("Document fraud", {"Passport fraud", "Document fraud", "Unspecified documents", "Other civil documents", "Supporting-document fraud", "Digital identity fraud"}),
    ("Visa / permit fraud", {"Document fraud"}),
    ("Impostor use", {"Impostors"}),
    ("Migrant smuggling", {"Migrant smuggling"}),
    ("Human trafficking", {"Human trafficking"}),
    ("Citizenship / residence fraud", {"Citizenship and naturalisation", "Application fraud"}),
    ("Border integrity", {"Corruption and insider facilitation", "Border security", "Aviation security", "Stowaways"}),
    ("Wanted-person interception", {"INTERPOL and watch lists"}),
    ("Policy update", {"Visa and entry policy", "Travel advisories", "Border technology", "Health travel rules", "Citizenship and naturalisation"}),
]


def _join(v):
    return "; ".join(v) if isinstance(v, (list, tuple)) else (v or "")


def sections(ev, text):
    """Returns [[section, [[label, value], ...]], ...] for the sections that match the report's topics.
    Values are plain strings; "" means not reported."""
    cats = set(ev.get("categories", []))
    kind = ev.get("kind", "Incident")
    t = fold(text)
    out = []
    for name, topics in SECTIONS:
        if not cats & topics:
            continue
        # policy sections only for updates; crime sections only for incidents (citizenship can be either)
        if name == "Policy update" and kind != "Update":
            continue
        if name == "Citizenship / residence fraud" and kind == "Update" and "Application fraud" not in cats:
            continue
        rows = []
        if name == "Document fraud":
            rows = [["Document type", _join(ev.get("document_types"))],
                    ["Issuing country of the document", _join(issuing_countries(text))],
                    ["Reported fraud method", _join(_labels(DOC_METHOD, t))],
                    ["Number of documents", str(ev.get("documents_count") or "")],
                    ["Blank versus issued documents", "Blank (unissued) documents reported" if BLANK.search(t) else ""],
                    ["Detection stage", _join(_labels(DETECTION, t)[:2])]]
        elif name == "Visa / permit fraud":
            rows = [["Visa or permit type", _join(_labels(PERMIT_TYPE, t))],
                    ["Purported issuing authority", _join(issuing_countries(text))],
                    ["Reported method", _join(_labels(VISA_METHOD, t))]]
        elif name == "Impostor use":
            used = W(["someone else's", "another person's", "belonging to", "brother's", "sister's", "cousin's", "friend's",
                      "relative's", "look-alike*", "lookalike*", "impostor*", "imposter*", "genuine passport*"])
            m = re.search(r"[^.]{0,120}(?:impostor|imposter|look-?alike|someone else's|another person's|belonging to)[^.]{0,120}",
                          text, re.I)
            rows = [["Use of another person's genuine document", "Reported" if used.search(t) else ""],
                    ["Detection point", _join(_labels(DETECTION, t)[:2])],
                    ["Source's description of the method", m.group(0).strip() if m else ""]]
        elif name == "Migrant smuggling":
            rows = [["Reported origin", ev.get("origin", "")], ["Reported transit", _join(transit(text))],
                    ["Reported destination", ev.get("destination", "")], ["Transport mode", ev.get("transport_mode", "")],
                    ["People intercepted", str(ev.get("people_count") or "")],
                    ["Alleged facilitators (role)", _join(_labels(FACILITATORS, t))],
                    ["Reported fees and currency", _join(fees(text))]]
        elif name == "Human trafficking":
            pot, idf = victims(text)
            rows = [["Reported exploitation type", _join(ev.get("exploitation"))],
                    ["Potential / suspected victims (as stated)", pot],
                    ["Identified / rescued victims (as stated)", idf],
                    ["Assistance or referral reported", "Reported" if REFERRAL.search(t) else ""],
                    ["Proceedings", ev.get("outcome", "")]]
        elif name == "Citizenship / residence fraud":
            adm = _labels(ADMIN_OUTCOME, t)
            rows = [["Programme involved", _join(_labels(PROGRAMME, t))],
                    ["Application stage", _join(_labels(STAGE, t)[:2])],
                    ["Alleged misrepresentation", _join(_labels(MISREP, t))],
                    ["Documents involved", _join(ev.get("document_types"))],
                    ["Administrative or court outcome", _join(adm + ([ev["outcome"]] if ev.get("outcome") else []))]]
        elif name == "Border integrity":
            loc = ev.get("location") or {}
            place = (ev.get("airports") or []) + loc.get("ports", []) + loc.get("crossings", [])
            # a role is "implicated" only in a corruption / insider report; elsewhere officers are the ones acting
            insider = "Corruption and insider facilitation" in cats
            conduct = [c for c in _labels(CONDUCT, t) if insider or c in ("Security breach", "Tag switching / baggage interference")]
            rows = [["Organisation or role implicated", _join(_labels(ROLE, t)) if insider else ""],
                    ["Alleged conduct", _join(conduct)],
                    ["Location", _join(place or ev.get("countries", [])[:2])],
                    ["Investigation / disciplinary / criminal outcome", _join(_labels(DISCIPLINE, t)[:2])]]
        elif name == "Wanted-person interception":
            rows = [["Notice or warrant", _join(_labels(NOTICE, t))],
                    ["Agency reporting it", _join(ev.get("agencies"))],
                    ["Stated basis", _first(_BASIS_RE, t)],
                    ["Reported outcome", _join(_labels(WANTED_OUTCOME, t)[:2])]]
        elif name == "Policy update":
            eff = ""
            m = _EFFECTIVE_RE.search(t)
            if m and re.search(r"\d|january|february|march|april|may|june|july|august|september|october|november|december|"
                                r"enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre", m.group(1)):
                eff = m.group(1).strip().title() + " (as stated)"
            stat = _labels(STATUS, t)
            rows = [["Issuing authority", _join([a for a, rx in _AUTH_RE if rx.search(t)][:3])],
                    ["Affected travellers / documents", _first(_AFFECTED_RE, t, limit=90)],
                    ["Announcement date (publication)", ev.get("date", "")],
                    ["Effective date", eff],
                    ["Exceptions", _first(_EXCEPT_RE, t, limit=90)],
                    ["Status", stat[0] if stat else ""],
                    ["Official guidance link", _join(official_links(ev.get("countries", []), text))]]
        out.append([name, rows])
    return out
