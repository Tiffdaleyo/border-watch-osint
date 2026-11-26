"""Seizure details: what was seized, how much (in its own unit), how it was hidden and shipped, its reported value.

Rules:
  - quantities keep their original number and unit; a converted figure is added only within the same kind of unit
    (mass -> kg, volume -> litres, counts stay counts). Kilograms, litres, tablets and plants are never added together.
  - "suspected" is kept when the report says it.
  - a value (money) is kept apart from the quantity, with who gave the estimate when the report says so.
"""
import re

from . import extract

fold = extract.fold

SUBSTANCES = [
    ("Cocaine", ["cocaine", "cocaina", "crack cocaine"]),
    ("Cannabis", ["cannabis", "marijuana", "marihuana", "ganja", "hashish", "skunk", "kush", "maconha", "compressed weed"]),
    ("Heroin", ["heroin", "heroina"]),
    ("Methamphetamine", ["methamphetamine", "crystal meth", "meth", "metanfetamina", "shabu"]),
    ("Fentanyl", ["fentanyl", "fentanilo"]),
    ("MDMA / ecstasy", ["mdma", "ecstasy", "extasis"]),
    ("Ketamine", ["ketamine", "ketamina"]),
    ("Synthetic drugs (other)", ["tramadol", "captagon", "synthetic drugs", "nitazene*"]),
    ("Khat", ["khat"]),
    ("Precursor chemicals", ["precursor*"]),
    ("Firearms", ["firearm*", "gun", "guns", "pistol*", "rifle*", "revolver*", "shotgun*", "armas de fuego"]),
    ("Ammunition", ["ammunition", "rounds", "cartridges", "bullets", "municiones"]),
    ("Cash", ["cash", "currency", "banknotes", "dinero", "efectivo"]),
    ("Wildlife", ["ivory", "pangolin*", "rhino horn*", "shark fin*", "parrots", "birds", "reptiles", "turtles", "wildlife"]),
    ("Tobacco", ["cigarettes", "tobacco", "cigars", "vapes", "e-cigarettes"]),
    ("Counterfeit goods", ["counterfeit goods", "fake goods", "counterfeit items", "counterfeit clothing"]),
    ("Gold / precious metals", ["gold", "gold bars", "silver bars"]),
]
_SUB_RE = [(n, extract.compile_words(w)) for n, w in SUBSTANCES]

# units: (pattern, original unit name, kind, factor to the standard unit)
UNITS = [
    (r"(?:metric\s+)?tonnes?|tons?|toneladas?", "tonnes", "mass", 1000.0),
    (r"kilograms?|kilogrammes?|kgs?|kilos?|kilogramos?", "kg", "mass", 1.0),
    (r"grams?|grammes?|gramos?|g", "g", "mass", 0.001),
    (r"pounds?|lbs?", "lb", "mass", 0.4536),
    (r"ounces?|oz", "oz", "mass", 0.02835),
    (r"litres?|liters?|litros?|l", "litres", "volume", 1.0),
    (r"gallons?", "gallons", "volume", 3.785),
    (r"tablets?|pills?|capsules?|pastillas?|comprimidos?", "tablets", "count", 1.0),
    (r"plants?|plantas?|seedlings?", "plants", "count", 1.0),
    (r"(?:rounds|cartridges|bullets)(?: of ammunition)?", "rounds", "count", 1.0),
    (r"firearms?|guns?|pistols?|rifles?|weapons?", "firearms", "count", 1.0),
    (r"packages?|parcels?|bricks?|blocks?|packets?|bundles?|bales?|paquetes?|ladrillos?", "packages", "count", 1.0),
    (r"pellets?|capsules?|bolsitas?", "pellets", "count", 1.0),
    (r"(?:cigarette\s+)?sticks|cigarettes|cartons", "cigarettes", "count", 1.0),
]
STD = {"mass": "kg", "volume": "litres", "count": None}
_NUMWORD = {"a dozen": 12, "dozens of": 24, "hundreds of": 200, "thousands of": 2000}
_QTY_RE = re.compile(
    r"(?<![\w.])(?P<qual>approximately|approx\.?|about|around|roughly|nearly|almost|some|an estimated|estimated|"
    r"more than|over|at least|in excess of|upwards of|up to|as much as|as many as|less than|under|"
    r"mas de|cerca de|alrededor de|aproximadamente|hasta|plus de|environ|jusqu'a|mais de|cerca de)?\s*"
    r"(?P<num>\d{1,3}(?:[,\s]\d{3})+(?:\.\d+)?|\d+(?:[.,]\d+)?)\s*(?P<mult>million|billion|thousand|millones|mil)?\s*"
    r"(?:-\s*)?(?:(?P<mid>[a-z]{3,})\s+)?(?P<unit>" + "|".join(u[0] for u in UNITS) + r")(?!\w)")
QUAL = {"approximately": "Approximate", "approx": "Approximate", "approx.": "Approximate", "about": "Approximate",
        "around": "Approximate", "roughly": "Approximate", "nearly": "Approximate", "almost": "Approximate",
        "some": "Approximate", "an estimated": "Approximate", "estimated": "Approximate", "cerca de": "Approximate",
        "alrededor de": "Approximate", "aproximadamente": "Approximate", "environ": "Approximate",
        "more than": "More than", "over": "More than", "at least": "More than", "in excess of": "More than",
        "upwards of": "More than", "mas de": "More than", "plus de": "More than", "mais de": "More than",
        "up to": "Up to", "as much as": "Up to", "as many as": "Up to", "hasta": "Up to", "jusqu'a": "Up to",
        "less than": "Less than", "under": "Less than"}


def _num(s, mult):
    s = s.replace(" ", "")
    if re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?", s):
        s = s.replace(",", "")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", s):          # 1.200 (Spanish thousands)
        s = s.replace(".", "")
    else:
        s = s.replace(",", ".")
    try:
        v = float(s)
    except ValueError:
        return None
    return v * {"million": 1e6, "millones": 1e6, "billion": 1e9, "thousand": 1e3, "mil": 1e3}.get(mult or "", 1)


def _unit(u):
    for pat, name, kind, f in UNITS:
        if re.fullmatch(pat, u):
            return name, kind, f
    return u, "count", 1.0


def _substance_near(t, start, end):
    """The substance named closest after (or just before) a quantity: '2 kg of cocaine', 'cocaine weighing 2 kg'."""
    after = t[end: end + 45]
    before = t[max(0, start - 45): start]
    best = None
    for name, rx in _SUB_RE:
        m = rx.search(after)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), name)
    if best:
        return best[1]
    for name, rx in _SUB_RE:
        if rx.search(before):
            return name
    return ""


def quantities(text):
    """All stated quantities (first 3000 characters), each with its substance, unit and qualifier."""
    t = fold(text[:3000])
    out, seen = [], set()
    for m in _QTY_RE.finditer(t):
        val = _num(m.group("num"), m.group("mult"))
        if not val:
            continue
        unit, kind, f = _unit(m.group("unit"))
        if m.group("unit") in ("g", "l") and (m.group("mid") or not re.search(r"\d\s*(g|l)$", m.group(0))):
            continue          # a lone "g" or "l" only counts right after a number ("500g")
        sub = _substance_near(t, m.start(), m.end())
        if m.group("mid"):        # "40 cannabis plants": the word in between names the substance
            sub = next((n for n, rx in _SUB_RE if rx.search(m.group("mid"))), sub)
        if unit == "firearms":
            sub = "Firearms"
        if unit == "rounds":
            sub = "Ammunition"
        if unit == "cigarettes":
            sub = "Tobacco"
        suspected = bool(re.search(r"suspected|presumed|believed to be|presunta|presunto", t[max(0, m.start() - 40): m.end() + 40]))
        std_unit = STD[kind] or unit
        key = (round(val * f, 3), std_unit)
        if key in seen:          # the same figure mentioned twice is one quantity
            continue
        seen.add(key)
        out.append({"substance": sub or "Not reported", "suspected": suspected,
                    "original": re.sub(r"\s+", " ", m.group(0)).strip(), "qty": val, "unit": unit,
                    "std_qty": round(val * f, 3), "std_unit": std_unit,
                    "qualifier": QUAL.get((m.group("qual") or "").strip(), "Exact")})
    return out[:6]


def substances(text):
    t = fold(text[:3000])
    out = []
    for name, rx in _SUB_RE:
        m = rx.search(t)
        if m:
            sus = re.search(r"suspected|presumed|presunta|presunto", t[max(0, m.start() - 30): m.start()])
            out.append(("Suspected " + name.lower()) if sus else name)
    return out[:5]


CONFIRM = [
    ("Laboratory-confirmed", ["laboratory", "lab test*", "lab results", "forensic analysis", "forensic test*",
                              "confirmed to be", "confirmed as"]),
    ("Field-tested", ["field test*", "field-test*", "tested positive", "narcotics test kit", "presumptive test"]),
    ("Suspected", ["suspected", "presumed", "believed to be", "presunta", "presunto", "presumed to be"]),
]
_CONF_RE = [(n, extract.compile_words(w)) for n, w in CONFIRM]

_CONCEAL_RE = re.compile(
    r"(?:hidden|concealed|stashed|stuffed|secreted|packed|tucked|smuggled|ocult\w*|escondid\w*|camuflad\w*|dissimul\w*)"
    r"\s+(?:\w+\s+){0,2}?(?:in|inside|within|among|beneath|under|behind|between|en|dentro de|entre|dans)\s+"
    r"((?:[\w'-]+\s+){0,5}[\w'-]+)")
_CONCEAL_WORDS = extract.compile_words(["false bottom*", "false compartment*", "body cavity", "swallowed", "ingested",
                                        "strapped to", "taped to", "body pack*", "pellets", "disguised as", "doble fondo",
                                        "compartimento oculto"])
SHIPMENT = [
    ("Shipping container", ["container*", "contenedor*", "conteneur*", "conteiner*", "reefer"]),
    ("Passenger baggage", ["suitcase*", "luggage", "baggage", "carry-on", "maleta*", "equipaje", "bagage*", "bagagem"]),
    ("On the body / swallowed", ["swallow*", "pellets", "body cavity", "strapped to", "taped to", "ingest*"]),
    ("Courier parcel / mail", ["parcel*", "courier", "package addressed", "mail", "postal", "encomienda*", "colis"]),
    ("Air cargo", ["air cargo", "cargo flight", "air freight", "carga aerea", "fret aerien"]),
    ("Vessel", ["vessel", "boat", "go-fast", "speedboat", "yacht", "semi-submersible", "fishing boat", "ship", "lancha*",
                "embarcacion*"]),
    ("Vehicle", ["vehicle", "truck", "lorry", "car", "van", "trailer", "bus", "camion*", "vehiculo*"]),
    ("Barrel", ["barrel*", "drum*"]),
    ("Sea cargo (port)", ["wharf", "wharves", "seaport", "port of", "shipment of", "consignment of", "cargo ship"]),
]
_SHIP_RE = [(n, extract.compile_words(w)) for n, w in SHIPMENT]
_DECLARED_RE = re.compile(r"(?:declared as|manifested as|labell?ed as|described as|disguised as|listed as|"
                          r"shipment of|consignment of|cargo of|load of|cargamento de|declarad[oa]s? como)\s+"
                          r"((?:(?!at |in |from |to |on |for |bound |which |that |and |with )[a-z'-]+\s+){0,2}"
                          r"(?!at\b|in\b|from\b|to\b|on\b|for\b|and\b)[a-z'-]+)")
_NOT_COMMODITY = re.compile(r"cocaine|cannabis|marijuana|drugs|narcotics|heroin|weapons|firearms|guns|ammunition|cash|meth")
_MONEY = (r"(?:us\$|usd\s?|\$|€|£|eur\s?|gbp\s?|j\$|jmd\s?|jm\$|cad\s?|c\$|tt\$|r\$|mxn\s?|ksh\s?|n|rs\.?\s?)"
          r"\s?\d[\d,.]*(?:\s?(?:million|billion|bn|m|thousand|k|millones))?"
          r"|\d[\d,.]*\s?(?:million|billion)?\s?(?:dollars|euros|pounds|pesos|naira|rupees|reais|jmd|usd|eur|gbp)")
_VALUE_RE = re.compile(r"(?:worth|valued at|value of|street value of|estimated value of|estimated at|with a value of|"
                       r"street value|valorad[oa]s? en|avaliad[oa]s? em|d'une valeur de)\s+(?:(?:an estimated|approximately|about|around|some|"
                       r"more than|over|nearly)\s+)?(" + _MONEY + ")")
_VALUE_RE2 = re.compile(r"(" + _MONEY + r")\s+(?:worth of|in (?:cocaine|cannabis|marijuana|drugs|narcotics|ganja))")
_ATTRIB_RE = re.compile(r"(?:according to|said|estimated|say|says)\s+(?:the\s+)?((?:[a-z]+\s+){0,3}"
                        r"(?:police|customs|authorities|officials|agency|cbp|ice|hsi|dea|nca|jcf|border force|coast guard|"
                        r"prosecutors|ministry|navy|army|office))")
_CASH_RE = re.compile(r"(" + _MONEY + r")\s+(?:in\s+)?(?:undeclared\s+)?(?:cash|currency|banknotes|in cash)|"
                      r"(?:cash|currency) (?:totall?ing|amounting to|of)\s+(" + _MONEY + ")")
_GUN_RE = re.compile(r"(\d[\d,]*|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(?:\w+\s+){0,2}?"
                     r"(firearms?|guns?|pistols?|rifles?|revolvers?|shotguns?|handguns?)")
_AMMO_RE = re.compile(r"(\d[\d,]*)\s+(?:\w+\s+){0,2}?(?:rounds|cartridges|bullets)")
CASE = [
    ("Correction reported", ["correction", "corrected", "clarified", "earlier reported", "previously reported"]),
    ("Court outcome", ["sentenced", "convicted", "pleaded guilty", "acquitted", "jailed", "found guilty"]),
    ("Charged", ["charged", "indicted", "prosecuted", "remanded"]),
    ("Arrest", ["arrested", "detained", "apprehended", "taken into custody", "detenido*", "arrestado*"]),
    ("Investigation", ["investigation", "investigating", "probe", "inquiry", "investigacion"]),
]
_CASE_RE = [(n, extract.compile_words(w)) for n, w in CASE]


def details(text, ev):
    """Rows for the 'Seizure' specialist section, and the structured quantities for totals."""
    t = fold(text[:3000])
    qs = quantities(text)
    conf = next((n for n, rx in _CONF_RE if rx.search(t)), "")
    concealment = ""
    m = _CONCEAL_RE.search(t)
    if m:
        concealment = re.split(r" (?:at|from|bound|which|that|and|when|after|on|by) ", re.sub(r"\s+", " ", m.group(0)).strip())[0]
    else:
        w = extract.find_words(_CONCEAL_WORDS, t)
        concealment = ", ".join(w[:3])
    ship = [n for n, rx in _SHIP_RE if rx.search(t)][:3]
    declared = ""
    for dm in _DECLARED_RE.finditer(t):
        if not _NOT_COMMODITY.search(dm.group(1)):
            declared = dm.group(1).strip()
            break
    value = ""
    vm = _VALUE_RE.search(t) or _VALUE_RE2.search(t)
    if vm:
        value = vm.group(1).strip()
        am = _ATTRIB_RE.search(t[max(0, vm.start() - 120): vm.end() + 120])
        value += f" (estimate attributed to {am.group(1).strip()})" if am else " (source of the estimate not stated)"
    other = []
    gm = _GUN_RE.search(t)
    if gm:
        other.append(f"Firearms: {gm.group(0)}")
    am = _AMMO_RE.search(t)
    if am:
        other.append(f"Ammunition: {am.group(0)}")
    cm = _CASH_RE.search(t)
    if cm and not (vm and cm.group(0) in t[vm.start(): vm.end() + 5]):
        other.append(f"Cash: {(cm.group(1) or cm.group(2)).strip()}")
    j = ev.get("journey") or {}
    qty_txt = "; ".join(f"{q['original']}" + (f" ({q['substance']})" if q["substance"] != "Not reported" else "")
                        for q in qs)
    std_txt = "; ".join(f"{q['substance']}: {q['std_qty']:g} {q['std_unit']}" for q in qs
                        if q["std_unit"] != q["unit"])
    qual_txt = "; ".join(dict.fromkeys(q["qualifier"] for q in qs))
    case = [n for n, rx in _CASE_RE if rx.search(t)][:2]
    rows = [["Substance / item (as reported)", "; ".join(substances(text))],
            ["Confirmation status", conf],
            ["Quantity and unit (original)", qty_txt],
            ["Standardised quantity", std_txt or ("Same as original" if qs else "")],
            ["Quantity qualifier", qual_txt],
            ["Concealment method", concealment[:140]],
            ["Shipment / transport type", "; ".join(ship)],
            ["Declared commodity", declared],
            ["Origin", j.get("origin", "") or ev.get("origin", "")],
            ["Transit", "; ".join(j.get("transit", []))],
            ["Destination", j.get("destination", "") or ev.get("destination", "")],
            ["Seizing agency", "; ".join(ev.get("agencies") or [])],
            ["Other seized items", "; ".join(other)],
            ["Reported valuation", value],
            ["Case development", "; ".join(case)]]
    return rows, qs
