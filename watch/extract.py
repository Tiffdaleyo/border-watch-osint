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
    # a named identity or travel document other than a passport: ID card, visa, residence or work permit
    "Document fraud": [
        "visa fraud", "fake visa*", "forged visa*", "fraudulent visa*", "counterfeit visa*", "visa scam*",
        "fake work permit*", "forged work permit*", "fraudulent work permit*", "fake residence permit*",
        "forged residence permit*", "fraudulent residence permit*", "fake green card*",
        "fake visa stamp*", "visa racket", "visa* falsa*",
        "faux visa*", "fraude de visa*", "fraude con visa*", "fraudes con visa*", "permiso* de residencia falso*", "permiso* de trabajo falso*",
        "fake ID*", "forged ID*", "fraudulent ID*", "counterfeit ID*", "fake identity card*", "forged identity card*",
        "fake national ID*", "fake ID card*", "identity card fraud", "ID card fraud", "cedula* falsa*",
        "fausse* carte* d'identite", "carteira* de identidade falsa*",
    ],
    # "fake documents" with no type named
    "Unspecified documents": [
        "identity fraud", "fake document*", "forged document*", "fraudulent document*", "counterfeit document*",
        "false document*", "fake identity", "fake identities", "stolen identit*",
        "travel document fraud", "fraudulent travel document*", "fake travel document*", "document fraud",
        "document forger*", "documentos falsos", "documento* falsificado*", "fraude documental", "faux papiers",
        "fraude documentaire", "faux documents", "documentos falsificados", "identidade falsa",
    ],
    "Impostors": [
        "impostor*", "imposter*", "look-alike*", "lookalike*", "someone else's passport",
        "another person's passport", "suplantación de identidad", "usurpation d'identité",
    ],
    # birth, marriage and death certificates and other civil documents
    "Other civil documents": [
        "fake birth certificate*", "forged birth certificate*", "fraudulent birth certificate*",
        "fake death certificate*", "forged death certificate*", "fake marriage certificate*", "forged marriage certificate*",
        "fraudulent marriage certificate*", "fake civil document*", "actas de nacimiento falsas", "acta de nacimiento falsa",
        "acta* de matrimonio falsa*", "faux acte* de naissance", "certidao de nascimento falsa",
    ],
    "Supporting-document fraud": [
        "fake bank statement*", "forged bank statement*", "fraudulent bank statement*", "fake employment letter*",
        "fake job offer*", "fake invitation letter*", "fake sponsorship letter*", "fake supporting document*",
        "forged supporting document*", "fraudulent supporting document*",
        "fake degree*", "fake diploma*", "fake academic certificate*", "forged academic certificate*",
        "fake police certificate*", "fake police clearance*", "fake medical certificate*", "fake vaccination card*",
        "fake vaccination certificate*", "fake COVID certificate*", "fake hotel booking*", "fake travel insurance",
        "fake certificate of employment", "fake admission letter*", "fake acceptance letter*",
    ],
    "Digital identity fraud": [
        "digital identity fraud", "synthetic identit*", "deepfake*", "deep fake*", "face morphing", "morphed photo*",
        "morphing attack*", "biometric spoofing", "biometric fraud", "fake e-visa*", "fraudulent e-visa*",
        "fake ESTA", "fake eTA", "fake ETIAS", "fake online visa*", "fraudulent online visa*", "fake visa website*",
        "fake visa application website*", "visa website scam*", "fake digital ID*", "hacked visa system",
        "fingerprint fraud", "fake biometric*",
    ],
    "Migrant smuggling": [
        "migrant smuggl*", "human smuggl*", "people smuggl*", "smuggling of migrants", "smuggling migrants",
        "smuggled migrants", "alien smuggling", "tráfico de migrantes", "tráfico ilícito de migrantes",
        "trafic de migrants", "passeur*", "filière d'immigration", "contrabando de migrantes", "coyote*",
        "smuggling network*", "smuggling ring*", "smuggling syndicate*",
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
        "migrants detained", "migrants interdicted", "migrant interdiction", "interdicted migrants", "vessel carrying migrants interdicted", "repatriated migrants",
        "migrant surge", "migrant flows", "migration flows", "migration trends", "unauthorized migrants",
        "illegal immigrants", "irregular migrants", "undocumented migrants", "sloop", "asylum seekers",
        "migracion irregular", "migrantes irregulares", "cruces irregulares", "flujo migratorio", "flujos migratorios",
        "migration irreguliere", "migrants intercepte*", "migracao irregular", "migrantes interceptados",
    ],
    "Visa and entry policy": [
        "visa requirement*", "new visa rule*", "visa rule*", "visa policy", "visa policies", "visa-free", "visa free",
        "visa waiver*", "visa exemption*", "visa on arrival", "visa ban*", "visa restriction*", "visa suspension",
        "suspends visa*", "suspended visa*", "visa fee*", "visa regime", "entry requirement*", "entry rule*",
        "entry ban*", "travel ban*", "border closure", "closes border*", "reopens border*", "immigration policy", "immigration rules", "immigration law", "asylum policy", "work visa*", "student visa*",
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
    "Application fraud": [
        "sham marriage*", "marriage fraud", "marriage of convenience", "marriages of convenience", "asylum fraud",
        "fraudulent application*", "false application*", "visa application fraud", "immigration application fraud",
        "citizenship application fraud", "misrepresentation on", "fake immigration consultant*", "ghost consultant*",
        "unlicensed immigration consultant*", "immigration scam*", "visa consultant* arrested", "fake job scheme*",
        "matrimonio* de conveniencia", "matrimonio* falso*", "mariage* blanc*", "mariage* de complaisance",
        "casamento* falso*",
    ],
    "INTERPOL and watch lists": [
        "Interpol", "red notice*", "yellow notice*", "blue notice*", "SLTD", "stolen and lost travel document*",
        "terror watch list*", "terror watchlist*", "terrorist watch list*", "terrorist watchlist*", "security watch list*",
        "immigration watch list*", "border watch list*", "no-fly list*", "terror list", "terrorist list", "sanctions list",
        "alerta roja", "notificacion roja de interpol",
        "wanted fugitive*", "fugitive arrested", "fugitive captured", "most wanted", "extradit*", "Europol",
        "Ameripol", "Frontex", "IMPACS",
        "notificacion roja", "difusion roja", "notice rouge", "difusao vermelha", "extradicion", "extradition",
    ],
    "Deportation and returns": [
        "deportation*", "deported", "deportee*", "deporting", "deports", "removal flight*", "repatriation flight*", "forced return*", "returned migrants", "deportacion*",
        "deportad*", "expulse*", "deportacao", "expulsion*",
    ],
    "Border security": [
        "border security", "border control*", "border guard*", "border patrol", "border agency", "border force",
        "border officer*", "coast guard", "border breach*", "breach of the border", "immigration officer*", "immigration officials", "PICA", "seguridad fronteriza", "control fronterizo",
        "controle aux frontieres", "police aux frontieres", "seguranca de fronteira",
    ],
    "Drug trafficking": [
        "cocaine", "heroin", "cannabis", "marijuana", "ganja", "methamphetamine", "crystal meth", "fentanyl", "MDMA",
        "ecstasy pills", "ketamine", "narcotic*", "drug mule*", "drug courier*", "drug smuggl*", "drug trafficking",
        "drug traffickers", "drugs seized", "drug bust", "drug haul", "swallowed pellets", "swallower*",
        "body packer*", "cocaine pellets", "cocaina", "marihuana", "narcotrafic*", "droga*", "cocaine", "stupefiants",
        "drogue*", "maconha", "trafico de drogas", "trafico de drogas",
        # precursor chemicals: the chemicals used to make drugs
        "precursor chemical*", "chemical precursor*", "drug precursor*", "fentanyl precursor*", "methamphetamine precursor*",
        "precursores quimicos", "insumos quimicos", "sustancias quimicas controladas", "precurseurs chimiques",
        "precursori chimici", "acetic anhydride", "potassium permanganate",
    ],
    "Cash couriers": [
        "undeclared cash", "undeclared currency", "undeclared money", "cash smuggl*", "currency smuggl*", "bulk cash",
        "cash courier*", "money laundering", "money launderer*", "smuggled cash", "smuggling cash", "cash seized",
        "currency seized", "seized cash", "dinero no declarado", "contrabando de divisas", "lavado de dinero",
        "argent liquide non declare", "blanchiment", "dinheiro nao declarado", "lavagem de dinheiro",
    ],
    "Firearms and ammunition": [
        "firearm*", "gun smuggl*", "guns smuggled", "gun running", "gunrunning", "arms trafficking", "arms smuggling",
        "weapons smuggling", "weapons trafficking", "illegal guns", "illegal weapons", "pistol*", "rifle*",
        "ammunition", "rounds of ammunition", "ghost gun*", "gun parts", "armas de fuego", "municiones",
        "trafico de armas", "armes a feu", "trafic d'armes", "munitions", "armas de fogo", "municoes",
    ],
    "Terrorism and sanctions": [
        "foreign terrorist fighter*", "foreign fighter*", "terror suspect*", "terrorism suspect*", "terrorist suspect*",
        "terror charges", "terrorism charges", "terror watchlist", "terror plot", "terrorist", "ISIS", "Islamic State",
        "al-Qaeda", "radicali*ed", "sanctions list", "sanctioned individual*", "sanctions evasion", "OFAC",
        "terrorista*", "terroriste*",
    ],
    "Corruption and insider facilitation": [
        "corrupt customs", "corrupt immigration", "corrupt border", "corrupt officer*", "corrupt official*",
        "bribe*", "bribery", "kickback*", "insider conspirac*", "insider threat", "insider help", "inside job",
        "airport worker*", "airport employee*", "airport staff", "baggage handler*", "airline employee*",
        "airline staff", "ramp agent*", "customs officer* arrested", "customs officer* charged",
        "immigration officer* arrested", "immigration officer* charged", "border officer* arrested",
        "border agent* arrested", "officer* accepted", "colluding officer*", "corrupcion", "soborno*", "coima*",
        "funcionario* de aduana*", "funcionario* de migracion", "corruption", "pot-de-vin", "suborno*",
    ],
    "Travel advisories": [
        "travel advisory", "travel advisories", "travel advice", "do not travel", "reconsider travel",
        "exercise increased caution", "exercise normal precautions", "advises against all travel",
        "advises against all but essential travel",
    ],
    "Stowaways": [
        "stowaway*", "stowed away", "stow away", "hidden in the wheel well", "wheel well", "landing gear compartment",
        "hidden aboard", "hiding aboard", "hidden on board", "found hiding in a container", "polizon*",
        "passager clandestin", "passagers clandestins", "clandestino em aviao", "clandestino a bordo",
    ],
    "Aviation security": [
        "airport security breach", "security breach at", "unruly passenger*", "disruptive passenger*", "airside", "aviation security", "AVSEC", "bomb threat",
        "suspicious package", "polizon*", "passager clandestin", "clandestino em aviao",
    ],
    "Wildlife smuggling": [
        "wildlife trafficking", "wildlife smuggl*", "wildlife crime", "ivory", "rhino horn*", "pangolin*",
        "exotic animal*", "exotic bird*", "protected species", "endangered species", "CITES", "parrots smuggled",
        "smuggled birds", "smuggled reptiles", "shark fins", "trafico de fauna", "trafico de especies",
        "trafic d'especes", "trafico de animais",
    ],
    "Border technology": [
        "ETIAS", "Entry/Exit System", "entry-exit system", "electronic travel authori*ation*", "ETA scheme",
        "ESTA application*", "ESTA program*", "e-visa", "evisa", "e-gate*", "egate*", "biometric border*",
        "biometric screening", "biometric data", "facial recognition", "advance passenger information",
        "passenger name record*", "digital travel credential*", "e-passport*", "biometric passport*",
        "automated border control", "border management system", "travel authori*ation", "biometric entry",
        "biometric exit", "fingerprint* at the border", "sistema biometrico", "pasaporte electronico",
        "passeport biometrique",
    ],
    "Health travel rules": [
        "travel restriction*", "travel advisory", "travel advisories", "health screening", "entry screening",
        "airport screening", "quarantine", "yellow fever certificate", "vaccination requirement*", "vaccine requirement*",
        "proof of vaccination", "outbreak", "mpox", "ebola", "marburg", "cholera", "dengue", "restricciones de viaje",
        "cuarentena", "restrictions de voyage", "restricoes de viagem",
    ],
    "Cargo operations": [
        "air cargo", "cargo shed", "cargo terminal", "cargo flight*", "cargo plane", "shipping container*", "container*",
        "shipment*", "consignment*", "courier package*", "courier parcel*", "parcel*", "postal", "mail centre",
        "mail center", "misdeclar*", "mis-declar*", "falsely declared", "false declaration", "undeclared goods",
        "contraband", "free zone", "transshipment", "trans-shipment", "bill of lading", "wharf", "wharves",
        "carga aerea", "contenedor*", "contrabando", "cargamento*", "conteneur*", "fret aerien",
        "colis", "conteiner*", "encomenda*",
    ],
}

# The seven main groups shown on the website. An event can carry several topics, so it can sit in several groups.
GROUPS = [
    ("Document & Identity Fraud", ["Passport fraud", "Document fraud", "Unspecified documents", "Other civil documents",
                                   "Impostors", "Supporting-document fraud", "Digital identity fraud"]),
    ("Migration & Facilitation", ["Irregular migration", "Migrant smuggling", "Immigration enforcement",
                                  "Deportation and returns"]),
    ("Human Trafficking", ["Human trafficking"]),
    ("Citizenship & Residence", ["Citizenship and naturalisation", "Application fraud"]),
    ("Border Integrity", ["Corruption and insider facilitation", "INTERPOL and watch lists", "Border security",
                          "Aviation security", "Stowaways", "Terrorism and sanctions"]),
    ("Policy & Systems", ["Visa and entry policy", "Travel advisories", "Border technology", "Health travel rules"]),
    ("Seizures & Contraband", ["Drug trafficking", "Firearms and ammunition", "Cash couriers", "Wildlife smuggling",
                               "Cargo operations"]),
]
TOPIC_GROUP = {t: g for g, ts in GROUPS for t in ts}


def groups_of(categories):
    return [g for g, ts in GROUPS if any(c in ts for c in categories)]


# Goods topics are kept only when the report is about a border, a journey or a shipment (not a street-level police
# story), or when it names a country we focus on (the Caribbean, by default).
BORDER_CONTEXT = [
    "haven", "luchthaven", "schiphol", "douane", "hafen", "flughafen", "zoll", "porto", "dogana", "frontiera", "grenze", "grens",
    "airport*", "flight*", "passenger*", "luggage", "suitcase*", "baggage", "carry-on", "traveller*", "traveler*",
    "port", "ports", "seaport", "container*", "cargo", "shipment*", "consignment*", "vessel*", "ship", "boat*",
    "border*", "customs", "courier*", "parcel*", "mule*", "swallow*", "smuggl*", "traffick*", "import*", "export*",
    "wharf", "wharves", "aeropuerto*", "aduana*", "puerto*", "frontera*", "contenedor*", "vuelo*", "aeroport*",
    "douane*", "frontiere*", "vol", "aeroporto*", "alfandega*", "fronteira*", "navio*", "travel*", "entry",
]
GOODS_TOPICS = {"Drug trafficking", "Cash couriers", "Firearms and ammunition", "Wildlife smuggling",
                "Terrorism and sanctions", "Health travel rules", "Cargo operations",
                "Corruption and insider facilitation", "Border technology"}

# Topics that describe crime. Anything else (policy, security, deportation news) is an "Update", not an incident.
CRIME_TOPICS = {"Passport fraud", "Document fraud", "Unspecified documents", "Impostors",
                "Other civil documents", "Supporting-document fraud", "Digital identity fraud", "Application fraud",
                "Migrant smuggling", "Human trafficking", "Drug trafficking", "Cash couriers",
                "Firearms and ammunition", "Wildlife smuggling", "Stowaways"}
# These count as an incident only when something happened (arrest, seizure, interception...).
ACTION_TOPICS = {"Citizenship and naturalisation", "INTERPOL and watch lists", "Irregular migration",
                 "Immigration enforcement", "Terrorism and sanctions", "Aviation security", "Cargo operations",
                 "Corruption and insider facilitation"}
# Broad topics: kept on their own only when something happened (arrest, interception...) or a place we watch is named.
BROAD_TOPICS = {"Immigration enforcement", "Deportation and returns", "Border security"}

# "fake Canadian visas", "forged Nigerian passport": a warning word up to 2 words before a document word.
FAKE_WORDS = ["fake", "forged", "fraudulent", "counterfeit", "false", "falsified", "doctored", "altered", "bogus",
              "phony", "phoney", "stolen", "illegally obtained", "falso", "falsos", "falsa", "falsas", "falsificado",
              "falsificados", "faux", "falsifie", "falsifies"]
PROXIMITY = {
    "Passport fraud": ["passport", "passports"],
    "Document fraud": ["visa", "visas", "work permit", "work permits", "residence permit", "residence permits",
                       "green card", "green cards", "visa stamp", "visa stamps",
                       "id", "ids", "id card", "id cards", "identity card", "identity cards"],
    "Unspecified documents": ["documents", "travel documents"],
    "Other civil documents": ["birth certificate", "birth certificates", "marriage certificate", "marriage certificates"],
}

# Words that show something happened (an arrest, a seizure, a conviction).
ACTION_WORDS = [
    "arrest*", "detain*", "intercept*", "seiz*", "charged", "convicted", "sentenced", "jailed", "busted",
    "dismantl*", "nabbed", "caught", "held", "raid*", "indicted", "pleaded guilty", "pleads guilty", "remanded",
    "uncovered", "foiled", "cracked down", "crackdown", "rescued", "stopped",
    "detenid*", "arrestad*", "capturad*", "incautad*", "decomisad*", "desarticulad*", "desmantelad*",
    "aprehendid*", "cae", "caen", "cayo", "capturan", "detienen", "arrestan", "interpellé*", "arrêté*", "démantelé*", "saisi*", "condamné*", "preso*", "presa*", "detido*",
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



# Dutch, German and Italian words (Aruba, Curacao, Sint Maarten, Suriname, Bonaire and Europe's main ports)
MORE_LANGUAGES = {
    "Passport fraud": ["vals paspoort", "valse paspoorten", "paspoortfraude", "vervalst paspoort", "gefalschte* reisepass*",
                       "gefalschte* pass", "passfalschung", "passaporto falso", "passaporti falsi"],
    "Unspecified documents": ["valse documenten", "vervalste documenten", "identiteitsfraude", "gefalschte* dokumente",
                                    "urkundenfalschung", "documenti falsi", "falsi documenti"],
    "Document fraud": ["visumfraude", "vals visum", "visabetrug", "visti falsi", "visto falso"],
    "Migrant smuggling": ["mensensmokkel", "mensensmokkelaar*", "schleuser*", "schleusung", "scafisti", "scafista",
                          "traffico di migranti", "favoreggiamento dell'immigrazione clandestina"],
    "Human trafficking": ["mensenhandel", "menschenhandel", "tratta di esseri umani"],
    "Irregular migration": ["illegale migratie", "irreguliere migratie", "irregulare migration", "irregulare migranten",
                            "migranti irregolari", "sbarchi"],
    "Visa and entry policy": ["visumplicht", "visumvrij", "inreisregels", "visumpflicht", "visafrei", "einreiseregeln",
                              "obbligo di visto", "esenzione dal visto"],
    "Drug trafficking": ["cocaine onderschept", "cocaine in beslag", "drugssmokkel", "drugskoerier*", "bolletjesslikker*",
                         "kokain sichergestellt", "drogenschmuggel", "drogenkurier*", "cocaina sequestrata",
                         "traffico di droga", "narcotraffico", "ovuli di cocaina"],
    "Firearms and ammunition": ["wapensmokkel", "vuurwapens in beslag", "waffenschmuggel", "traffico di armi"],
    "Cash couriers": ["contant geld in beslag", "bargeldschmuggel", "contanti non dichiarati"],
    "Deportation and returns": ["uitzetting", "abschiebung*", "rimpatri*", "espulsione"],
    "Border security": ["grensbewaking", "marechaussee", "kmar", "kustwacht", "bundespolizei", "grenzkontrolle*",
                        "guardia di finanza", "controlli alle frontiere"],
    "INTERPOL and watch lists": ["internationaal gesignaleerd", "internationale fahndung", "mandato di arresto internazionale"],
}
for _k, _w in MORE_LANGUAGES.items():
    CATEGORIES[_k] = CATEGORIES[_k] + _w
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
    # "nationals from Brazil" or "citizens from Cuba" is a nationality, not where a journey started
    m = re.search(r"(?<!\w)(?<!nationals )(?<!national )(?<!citizens )(?<!citizen )(?<!natives )(?<!native )"
                  r"(?:from|desde|depuis|vindo de|procedente de|proveniente de|en provenance d[eu']?)\s+(?:the\s+)?(" + alt
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


_MONEY_BEFORE = re.compile(r"(?:[$€£¥₦₹]|us\$|j\$|r\$|c\$|tt\$|rs\.?|usd|eur|gbp|jmd|cad|sar|aed|inr|ngn|mxn|php|"
                           r"rp|ksh|ghs|zar|cop|brl|ars)\s?$")
_MONEY_BETWEEN = re.compile(r"\b(?:riyals?|dollars?|euros?|pounds? sterling|naira|rupees?|pesos?|reais|dirhams?|shillings?|"
                            r"cedis?|rand|yuan|yen|francs?|usd|eur|gbp|jmd|worth|per|each|a head|for|fees?|paid|"
                            r"cost|price|bribes?|in cash|million|billion|thousand|lakh|crore|mil|millones)\b")
_MODEL_BEFORE = re.compile(r"(?:ak|ar|m|g|mp|sks|fn|cz|rpk|pkm|vz|type)[-\s]?$")


def find_count(rx, text):
    """The largest count of documents or people named in the text. Money is never a count: a number right after a
    currency sign or code ("€22,000 for fake passports", "$21,000 per person"), or with a money word between the
    number and the item, is skipped, and so is a weapon model number ("AK-47")."""
    best = 0
    t = fold(text)
    pos = 0
    while True:
        m = rx.search(t, pos)
        if not m:
            break
        pos = m.end(1)              # look again right after this number, so "AK-47 rifles and 20 passports" finds 20
        n = _to_int(m.group(1))
        if not (1 < n < 1_000_000) or 1900 <= n <= 2100:      # skip years like "2026"
            continue
        before = t[max(0, m.start(1) - 6): m.start(1)]
        if _MONEY_BEFORE.search(before) or _MODEL_BEFORE.search(before):
            continue
        if _MONEY_BETWEEN.search(t[m.end(1): m.end()]) or re.match(r"\s*(?:per|each|a head|for each)\b", t[m.end():]):
            continue
        best = max(best, n)
    return best


# ---------------------------------------------------------------------------------------------
# main entry point
# ---------------------------------------------------------------------------------------------
_CONTEXT_RE = compile_words(BORDER_CONTEXT)
_STRICT_RE = compile_words(["customs", "immigration", "airport*", "port", "ports", "seaport", "border*", "wharf",
                            "wharves", "passport*", "visa*", "aduana*", "migracion", "aeropuerto*", "frontera*", "douane*",
                            "aeroport*", "frontiere*", "alfandega*", "aeroporto*", "fronteira*", "ETIAS", "ESTA",
                            "Entry/Exit System", "e-gate*", "traveller*", "traveler*", "passenger*"])
_KG_RE = re.compile(r"(?<!\w)(\d[\d,\.]*)\s*(?:-\s*)?(kg|kgs|kilo|kilos|kilogram|kilograms|kilogrammes|tonnes?|tons?|"
                    r"lbs?|pounds)(?!\w)")


def find_weight_kg(text):
    """Largest weight in the text, in kilograms (pounds and tonnes converted)."""
    best = 0.0
    for m in _KG_RE.finditer(fold(text)):
        num = m.group(1).replace(",", "")
        try:
            n = float(num)
        except ValueError:
            continue
        unit = m.group(2)
        if unit.startswith("ton"):
            n *= 1000
        elif unit.startswith(("lb", "pound")):
            n *= 0.4536
        best = max(best, n)
    return round(best, 1)


_PERSONAL_BAN_RE = re.compile(r"\b(?:court|judge|magistrate|bail|tribunal|defie[sd]|defying|flees?|fled|plea|request to lift|"
                              r"bid to lift|lifts? (?:his|her) |(?:his|her) (?:overseas |foreign )?travel ban|"
                              r"barred from leaving|freed with|released with|released on bail|banned from leaving|surrender(?:ed)? (?:his|her) passport)")
_GROUP_BAN_RE = re.compile(r"\b(?:nationals|citizens of|countries|proclamation|executive order|travellers from|travelers from)\b")


# document categories that name the type of document ("Unspecified documents" is used only when none is named)
NAMED_DOCS = {"Passport fraud", "Document fraud", "Other civil documents"}
# names used before 28 Nov 2026 (kept in older stored article facts)
OLD_CATEGORY = {"Visa and permit fraud": "Document fraud"}


# cooperation news: agreements, networks, training. With no arrest, seizure or other action word, it is an Update.
_COOP_RE = re.compile(r"(?<!\w)(?:agreements?|memorand(?:um|a) of understanding|mou|sign(?:s|ed)? (?:an? )?(?:deal|pact|accord)|"
                      r"cooperation|co-operation|partnership|join(?:s|ed)? (?:forces|hands)|join(?:s|ed)? (?:the |an? )?(?:\w+ ){0,2}(?:network|alliance|"
                      r"initiative|platform|coalition|operation)|(?:international|regional|global) network|workshops?|"
                      r"training|summit|conference|forum|alliances?|acuerdos?|convenios?|memorando|cooperacion|alianza|se (?:incorpora|une|suma)|"
                      r"red (?:internacional|regional)|taller|capacitacion|firma(?:n|ron)? (?:un )?(?:acuerdo|convenio)|accords?|"
                      r"partenariat|acordos?|parceria|cooperacao)(?!\w)")


def extract(item, focus_countries=()):
    """item = dict with at least 'title' (and optionally 'summary'). Returns the facts, or None if off-topic."""
    text = f"{item.get('title', '')}. {item.get('summary', '')}"
    folded = fold(text)
    cats = {name: find_words(rx, folded) for name, rx in _CAT_RE.items()}
    for name, rx in _PROX_RE.items():
        cats[name] = sorted(set(cats.get(name, [])) | {m.group(0) for m in rx.finditer(folded)})
    cats = {k: v for k, v in cats.items() if v}
    if "Unspecified documents" in cats and set(cats) & NAMED_DOCS:
        cats.pop("Unspecified documents")      # the type is named, so the documents are not unspecified
    actions = find_words(_ACTION_RE, folded)
    if actions and re.search(r"(?<!\w)(?:migrant|migrante|immigrant|refugee|asylum seeker)s?(?!\w)", folded):
        cats.setdefault("Irregular migration", ["migrants + " + actions[0]])
    if not cats:
        return None
    countries = find_countries(text)
    # goods topics need a border, journey or shipment angle, or a country we focus on
    if not _CONTEXT_RE.search(folded) and not (set(countries) & set(focus_countries)):
        for k in GOODS_TOPICS:
            cats.pop(k, None)
    # corruption or border technology on its own needs a clear border agency or place, not just "travel"
    for k in ("Corruption and insider facilitation", "Border technology"):
        if k in cats and len(cats) == 1 and not _STRICT_RE.search(folded):
            cats.pop(k)
    # a court's travel ban on one person (bail, a politician barred from leaving) is not an entry rule
    pol = cats.get("Visa and entry policy")
    if pol and all(w.startswith(("travel ban", "entry ban")) for w in pol) and _PERSONAL_BAN_RE.search(folded) \
            and not _GROUP_BAN_RE.search(folded):
        cats.pop("Visa and entry policy")
        if not cats:
            return None
    # "Cargo operations" on its own needs something that happened or a crime word
    if set(cats) == {"Cargo operations"} and not actions:
        return None
    if not cats:
        return None
    if set(cats) <= BROAD_TOPICS and not actions and not countries:
        return None
    crime = bool(set(cats) & CRIME_TOPICS) or (
        bool(actions) and bool(set(cats) & ACTION_TOPICS))
    if crime and not [a for a in actions if a != "held"] and _COOP_RE.search(folded):
        crime = False          # a country joins a network or signs an agreement against a crime: news, not a case
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
        "weight_kg": find_weight_kg(text),
    }
