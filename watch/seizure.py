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
    # chemicals used to make drugs. The named ones only count inside a seizure report (this module is used for nothing else)
    ("Precursor chemicals", ["precursor*", "precurseur*", "controlled chemicals", "sustancias quimicas controladas",
                             "insumos quimicos", "ephedrine", "pseudoephedrine", "efedrina", "pseudoefedrina",
                             "phenylacetone", "phenyl-2-propanone", "p2p", "bmk", "pmk", "pmk glycidate", "bmk glycidate",
                             "safrole", "safrol", "piperonal", "acetic anhydride", "anhidrido acetico",
                             "potassium permanganate", "permanganato de potasio", "4-anpp", "anpp", "n-phenethyl-4-piperidone"]),
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


def _num(s, mult, lang="en"):
    s = s.replace(" ", "")
    if re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?", s):
        s = s.replace(",", "")
    elif lang != "en" and re.fullmatch(r"\d{1,3}(\.\d{3})+", s):   # 1.200 (Spanish thousands; in English 13.795 kg is a decimal)
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
    if re.match(r"\W*(?:of\s+)?(?:[\w-]+\s+){0,3}?(?:precursor|precurseur|chemicals?\b|quimicos?\b)", after):
        return "Precursor chemicals"      # "50 kg of fentanyl precursors", "2 tonnes of chemicals" -- not the drug itself
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


# words that put a figure in the past or in a running total, so it is not this seizure
_BACKGROUND_RE = re.compile(
    r"\b(?:since|so far|this year|last year|previous(?:ly)?|earlier this|in the past|over the (?:past|last)|past (?:year|decade|\w+ (?:years|months))|"
    r"annual(?:ly)?|per year|a year|each year|every year|(?:in|during|between|from) (?:19|20)\d\d|total of|in total|altogether|cumulative|"
    r"record|largest ever|biggest ever|operation(?:s)? (?:that|which)|across (?:\d+|several|multiple) countries|trafficked|have seized|had seized|"
    r"desde|en lo que va|ja teve|ja foram|este ano|el ano pasado|en total|depuis|cette annee|l'an dernier|desde o inicio|este ano)\b")


def quantities(text, lang="en"):
    """All stated quantities (first 3000 characters), each with its substance, unit and qualifier."""
    t = fold(text[:3000])
    out, seen = [], set()
    for m in _QTY_RE.finditer(t):
        val = _num(m.group("num"), m.group("mult"), lang)
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
        before, after = t[max(0, m.start() - 90): m.start()], t[m.end(): m.end() + 60]
        before, after = re.split(r"[.;!?]\s", before)[-1], re.split(r"[.;!?]\s", after)[0]   # same sentence only
        background = bool(_BACKGROUND_RE.search(before + " " + m.group(0) + " " + after))
        key = (round(val * f, 3), std_unit)
        if key in seen:          # the same figure mentioned twice is one quantity
            continue
        seen.add(key)
        out.append({"substance": sub or "Not reported", "suspected": suspected,
                    "original": re.sub(r"\s+", " ", m.group(0)).strip(), "qty": val, "unit": unit,
                    "std_qty": round(val * f, 3), "std_unit": std_unit,
                    "qualifier": QUAL.get((m.group("qual") or "").strip(), "Exact"),
                    "background": background})
    # the figure counted in totals: per substance and unit, the first one that is not background (a yearly total,
    # an earlier case, a whole operation); the rest stay visible in the record but are not added up
    done = set()
    for q in out[:6]:
        k = (q["substance"], q["std_unit"])
        q["main"] = not q["background"] and q["substance"] != "Not reported" and k not in done
        if q["main"]:
            done.add(k)
    return out[:6]


def substances(text):
    t = fold(text[:3000])
    out = []
    for name, rx in _SUB_RE:
        # "fentanyl precursors" are chemicals, not fentanyl
        m = next((x for x in rx.finditer(t) if name == "Precursor chemicals"
                  or not re.match(r"\s*(?:precursor|precurseur)", t[x.end():x.end() + 14])), None)
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
_GUN_RE = re.compile(r"(?<![a-z]-)(?<!\bak )(?<!\bar )(?<!\w)(\d[\d,]*|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|an?)\s+(?:[\w-]+\s+){0,2}?"
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


# ---- standard categories, so concealment methods and cover loads can be counted and compared over time ----
CONCEALMENT_TYPES = [
    ("Swallowed / internal body", ["swallow*", "ingest*", "pellets", "body cavity", "body cavities", "internally",
                                   "cocaine-filled capsules", "capsules in his stomach", "capsules in her stomach",
                                   "drug mule*", "body packer*", "stuffer*", "ingerid*", "capsulas", "boulettes"]),
    ("Strapped or taped to the body", ["strapped to", "taped to", "body pack*", "around his waist", "around her waist",
                                       "under his clothing", "under her clothing", "in his underwear", "in her underwear",
                                       "adheridos al cuerpo", "adherida al cuerpo"]),
    ("Clothing or footwear", ["shoe*", "sneaker*", "boots", "soles", "clothing", "garment*", "jacket*", "wig*",
                              "zapato*", "calzado", "ropa", "prendas", "chaussures", "vetements"]),
    ("Luggage: false bottom or lining", ["false bottom*", "double bottom*", "double-bottom*", "lining of", "suitcase lining",
                                         "luggage lining", "doble fondo", "double fond", "fundo falso"]),
    ("Luggage contents", ["suitcase*", "luggage", "baggage", "carry-on", "backpack*", "checked bag*", "maleta*",
                          "equipaje*", "valise*", "bagage*", "malas"]),
    ("Toiletries, cosmetics or personal items", ["toiletr*", "shampoo", "lotion*", "cosmetic*", "perfume*", "aseo",
                                                 "deodorant*", "cream jar*", "soap"]),
    ("Electronics or appliances", ["speaker*", "sound system", "laptop*", "television*", "printer*", "appliance*",
                                   "bocina*", "equipo de sonido", "electrodomestico*", "microwave*", "refrigerator*"]),
    ("Inside food or goods", ["coconut*", "cereal*", "fruit*", "banana*", "pineapple*", "avocado*", "coffee", "candy",
                              "sweets", "chocolate*", "canned", "tins of", "bottles of", "juice", "rum", "sauce*",
                              "spice*", "hollowed", "cocos", "frutas", "cajas de cereal"]),
    ("Liquid or impregnated", ["liquid cocaine", "dissolved", "impregnated", "soaked", "in liquid form", "liquid form",
                               "diluted", "infused"]),
    ("Courier parcel or mail", ["parcel*", "courier shipment*", "courier parcel*", "courier package*", "courier service*", "courier company", "by courier", "via courier", "express courier", "by mail", "airmail", "mail parcel*", "postal", "package addressed", "encomienda*", "colis",
                                "envelope*"]),
    ("Shipping container (structure or rip-on/rip-off)", ["rip-on", "rip-off", "rip on/rip off", "container wall*",
                                                          "container floor", "container door*", "refrigeration unit*",
                                                          "reefer unit*", "reefer machinery", "container roof",
                                                          "contaminated container*", "gancho ciego"]),
    ("Cargo cover load", ["among legitimate", "mixed with", "among a shipment", "among the cargo", "within a shipment",
                          "in a shipment of", "in a consignment of", "among bags of", "among boxes of", "among crates",
                          "inside boxes of", "inside crates", "pallets of", "cover load", "legitimate cargo",
                          "legitimate goods", "entre cajas de", "camuflad*", "cargamento de"]),
    ("Vehicle hidden compartment", ["hidden compartment*", "secret compartment*", "trap compartment*", "rocker panel*",
                                    "fuel tank*", "gas tank*", "spare tyre*", "spare tire*", "dashboard", "door panel*",
                                    "bumper*", "chassis", "compartimento oculto", "compartimiento oculto", "caleta*"]),
    ("Vessel hull or compartment", ["hull", "sea chest*", "below deck", "bilge", "engine room", "ballast",
                                    "submerged", "attached to the hull", "divers", "casco del", "semi-submersible"]),
    ("Aircraft", ["aircraft panel*", "lavatory", "toilet panel*", "wheel well", "cargo hold", "aircraft seat*",
                  "galley", "avionics bay"]),
    ("Furniture, machinery or structures", ["furniture", "machinery", "machine part*", "generator*", "pipes",
                                            "tiles", "granite", "marble", "timber", "logs", "pallet*",
                                            "statue*", "muebles", "maquinaria"]),
    ("Barrel or drum", ["barrel*", "drum*", "barril*", "tonel*"]),
]
_CT_RE = [(n, extract.compile_words(w)) for n, w in CONCEALMENT_TYPES]

# goods used as cover (declared or legitimate goods the contraband was hidden in or among)
COVER_GOODS = [
    ("Fruit and vegetables", ["banana*", "pineapple*", "avocado*", "coconut*", "mango*", "plantain*", "citrus",
                              "oranges", "limes", "lemons", "fruit*", "vegetables", "potatoes", "onions", "yams",
                              "platano*", "banano*", "piña*", "pina*", "cocos", "frutas"]),
    ("Frozen or fresh fish and meat", ["frozen fish", "fish", "shrimp*", "prawns", "seafood", "frozen meat", "beef",
                                       "chicken", "pescado", "camaron*", "mariscos"]),
    ("Coffee, cocoa, sugar or grain", ["coffee", "cocoa", "cacao", "sugar", "rice", "flour", "grain*", "beans",
                                       "cereal*", "cafe", "azucar", "arroz"]),
    ("Drinks", ["rum", "beer", "wine", "juice", "liquor", "alcohol", "spirits", "water bottles", "ron", "cerveza"]),
    ("Building materials and stone", ["granite", "marble", "tiles", "cement", "ceramic*", "bricks", "timber", "lumber",
                                       "wood", "plywood", "stone", "ceramica*", "madera", "granito"]),
    ("Scrap, waste and used goods", ["scrap metal", "scrap", "plastic waste", "waste", "used clothing",
                                     "second-hand clothing", "used tyres", "used tires", "chatarra"]),
    ("Machinery, vehicles and parts", ["machinery", "machine part*", "spare parts", "auto parts", "car parts",
                                       "engine*", "generator*", "vehicles", "tyres", "tires", "maquinaria", "repuestos"]),
    ("Furniture and household goods", ["furniture", "household goods", "personal effects", "appliance*", "mattress*",
                                       "muebles", "menaje"]),
    ("Clothing and textiles", ["clothing", "textiles", "fabric*", "garments", "shoes", "footwear", "ropa", "textil*"]),
    ("Cosmetics and toiletries", ["cosmetic*", "toiletr*", "shampoo", "soap", "perfume*", "cosmeticos"]),
    ("Electronics", ["electronics", "speakers", "televisions", "laptops", "phones", "electronicos"]),
    ("Chemicals and fertiliser", ["chemical*", "fertili*er", "paint", "resin", "solvent*", "quimicos", "fertilizante*"]),
    ("Charcoal, wood pellets or animal feed", ["charcoal", "wood pellets", "animal feed", "pet food", "carbon vegetal"]),
    ("Flowers and plants", ["flowers", "roses", "plants", "flores"]),
]
_CG_RE = [(n, extract.compile_words(w)) for n, w in COVER_GOODS]


def concealment_types(text):
    """Standard concealment categories named in the text (several can apply)."""
    t = fold(text)
    found = [n for n, rx in _CT_RE if rx.search(t)]
    if "Luggage: false bottom or lining" in found and "Luggage contents" in found:
        found.remove("Luggage contents")          # the more precise one is enough
    if "Cargo cover load" in found and "Inside food or goods" in found and not re.search(r"inside|hollow|filled|stuffed", t):
        found.remove("Inside food or goods")
    return found[:3]


def cover_goods(text):
    """Goods the contraband was declared as, hidden in, or hidden among: (category, words as reported)."""
    t = fold(text)
    out = []
    for n, rx in _CG_RE:
        m = rx.search(t)
        if m:
            out.append((n, m.group(0)))
    return out[:3]


_COVER_CUE = re.compile(r"(?:hidden|concealed|stashed|secreted|packed|camouflaged|disguised|declared as|manifested as|"
                        r"among|amongst|mixed with|inside|within|shipment of|consignment of|cargo of|load of|boxes of|"
                        r"crates of|bags of|pallets of|ocult\w*|escondid\w*|camuflad\w*|entre|cargamento de|dissimul\w*)")


def _cover_zone(t):
    """Only the words right after a concealment cue (so 'a fish market' elsewhere in the story is not a cover load)."""
    return " ".join(t[m.end(): m.end() + 70] for m in _COVER_CUE.finditer(t))


# ---- insider signals: staff of an airport, port, airline, customs, police or a carrier named as involved ----
INSIDER_ROLES = [
    ("Airport staff", ["baggage handler*", "ramp agent*", "ramp worker*", "airport worker*", "airport employee*",
                       "airport staff", "ground staff", "ground handler*", "airside worker*", "aviation security officer*",
                       "trabajador* del aeropuerto", "empleado* del aeropuerto", "maletero*"]),
    ("Airline crew or staff", ["flight attendant*", "cabin crew", "air hostess*", "pilot*", "airline employee*",
                               "airline staff", "airline worker*", "crew member*", "azafat*", "tripulante*"]),
    ("Port or dock worker", ["dock worker*", "port worker*", "port employee*", "stevedore*", "longshorem*", "dockworker*",
                             "crane operator*", "terminal worker*", "terminal employee*", "wharf worker*", "port staff",
                             "trabajador* portuario*", "estibador*", "docker*"]),
    ("Ship's crew", ["ship's crew", "crew of the vessel", "seafarer*", "sailor*", "captain of the", "ship captain",
                     "vessel's captain", "marinero*", "tripulacion"]),
    ("Customs officer", ["customs officer*", "customs official*", "customs agent*", "customs employee*", "customs staff",
                         "customs inspector*", "funcionario* de aduana*", "agente* de aduana*", "douanier*"]),
    ("Immigration or border officer", ["immigration officer*", "immigration official*", "border officer*",
                                       "border agent*", "border guard*", "border patrol agent*", "passport control officer*",
                                       "agente* de migracion", "oficial* de migracion"]),
    ("Police or military", ["police officer*", "policeman", "policemen", "police constable*", "cop", "cops",
                            "soldier*", "army officer*", "navy officer*", "coast guard officer*", "military officer*",
                            "agente* de policia"]),
    ("Postal or courier staff", ["postal worker*", "postal employee*", "mail carrier*", "courier company employee*",
                                 "courier employee*", "courier staff", "warehouse worker*"]),
    ("Logistics, shipping or clearing agent", ["clearing agent*", "customs broker*", "freight forwarder*", "shipping agent*",
                                               "logistics company employee*", "logistics employee*", "agente de carga",
                                               "agente aduanal"]),
    ("Government official", ["government official*", "public official*", "civil servant*", "ministry official*",
                             "funcionario* publico*"]),
]
_ROLE_RE = [(n, extract.compile_words(w)) for n, w in INSIDER_ROLES]
_AFTER = re.compile(r"^[\w\s,'-]{0,25}?\b(?:was|were|is|are|has been|have been|had been)?\s*(?:arrested|charged|detained|held|"
                    r"implicated|accused|suspected|indicted|convicted|sentenced|jailed|dismissed|sacked|suspended|"
                    r"bribed|paid|recruited|involved|colluded|conspired|pleaded|admitted|helped|facilitated|"
                    r"detenid|arrestad|implicad|acusad|sobornad)\w*"
                    # "customs officers arrested a passenger": the officers made the arrest, so it is not a signal
                    r"(?!\s+(?:a|an|the|two|three|four|five|several|\d+|passengers?|man|men|woman|women|suspects?|"
                    r"travell?ers?|people|persons|individuals|him|her|them|nationals?|foreigners?|drugs|cocaine)\b)")
_BEFORE = re.compile(r"(?:arrest(?:ed|s)?|charg(?:ed|es)|detain(?:ed|s)?|jail(?:ed|s)?|sentenc(?:ed|es)|convict(?:ed|s)?|"
                     r"accus(?:ed|es)|implicat(?:ed|es)|dismiss(?:ed|es)?|suspend(?:ed|s)?|indict(?:ed|s)?|bribed|recruited|"
                     r"paid|help of|helped by|assisted by|with the help of|in collusion with|colluding|corrupt|rogue|"
                     r"detienen a|detenido a|arrestan a)"
                     r"(?:\s+(?:of|a|an|the|two|three|four|five|several|\d+|former|serving|off-duty|senior|junior|alleged|"
                     r"suspected|dos|tres|un|una|los|las))*\s+$")
_INSIDER_WORD = re.compile(r"insider|inside help|inside job|bribe|bribery|corrupt|collu|kickback|soborn|cohecho")


def insider_roles(text):
    """Staff roles named as involved: the role is the one arrested, charged, bribed or helping (not the officers who
    made the arrest), or the sentence calls it insider help, bribery or corruption."""
    found = []
    for sent in re.split(r"(?<=[.!?;])\s+|\n", fold(text)):
        flag = bool(_INSIDER_WORD.search(sent))
        for n, rx in _ROLE_RE:
            if n in found:
                continue
            for m in rx.finditer(sent):
                if flag or _AFTER.search(sent[m.end(): m.end() + 60]) or _BEFORE.search(sent[max(0, m.start() - 45): m.start()]):
                    found.append(n)
                    break
    return found[:3]


def details(text, ev):
    """Rows for the 'Seizure' specialist section, and the structured quantities for totals."""
    t = fold(text[:3000])
    qs = quantities(text, (ev.get("lang") or "en")[:2])
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
            ["Concealment category", "; ".join(concealment_types(" ".join([concealment, t])))],
            ["Shipment / transport type", "; ".join(ship)],
            ["Declared commodity", declared],
            ["Cover load / goods used as cover", "; ".join(f"{w} ({n})" for n, w in cover_goods(" ".join([declared, _cover_zone(t)])))],
            ["Origin", j.get("origin", "") or ev.get("origin", "")],
            ["Transit", "; ".join(j.get("transit", []))],
            ["Destination", j.get("destination", "") or ev.get("destination", "")],
            ["Seizing agency", "; ".join(ev.get("agencies") or [])],
            ["Other seized items", "; ".join(other)],
            ["Insider signal (staff named as involved)", "; ".join(insider_roles(text[:3000]))],
            ["Reported valuation", value],
            ["Case development", "; ".join(case)]]
    return rows, qs
