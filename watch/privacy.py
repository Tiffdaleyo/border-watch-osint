"""Privacy filter, applied to every summary before it is saved or published.

What it does (agreed with the project owner):
  - Passport, ID and similar document numbers are replaced by "[number withheld]" everywhere.
  - Private street addresses are replaced by "[address withheld]".
  - Victims' names are removed: in human-trafficking reports a personal name is removed unless the words just before it
    show a suspect, accused, charged or convicted person, or an official; elsewhere a name right after "victim" is removed.
  - Names of people charged or convicted, officials and agencies are kept as the source states them.
  - Headlines are kept as published (only numbers are removed from them).
"""
import re

from .places import COUNTRIES

NUM = "[number withheld]"
_ID_RE = re.compile(
    r"(?i)\b((?:passport|id|identity card|identity|national id|document|licen[cs]e|trn|ssn|social security|cedula|cédula|"
    r"visa|permit|pasaporte|passeport)\s*(?:no\.?|number|num\.?|#|nr\.?)?\s*[:#]?\s*)([A-Z]{0,3}[- ]?\d[\d -]{4,13}\d)\b")
_BARE_RE = re.compile(r"\b[A-Z]{1,2}\d{6,9}\b|\b\d{3}-\d{3}-\d{3}\b")
_ADDR_RE = re.compile(
    r"\b\d{1,5}\s+(?:[A-Z][a-z]+\s){1,3}(?:Street|St\.|Road|Rd\.|Avenue|Ave\.|Lane|Drive|Close|Crescent|Boulevard|Way|"
    r"Terrace|Court|Place|Avenida|Calle|Rue)\b")
_VICTIM_RE = re.compile(r"(\b(?i:victims?)(?:,|\s+(?i:named|identified as))?\s+)((?:[A-Z][a-z'’-]+\s?){2,3})(?=[,.;:]|\s+(?:was|were|is|aged|\d))")
_CUE_RE = re.compile(r"(?i)\b(victims?|survivors?|rescued|girls?|boys?|wom[ae]n|minors?|child(?:ren)?|teen(?:ager)?s?|\d{1,2}-year-old|aged \d)")

_STOP = set("""Police Ministry Department National Agency Force Court Office Service Services Unit Coast Guard Airport International
Republic Island Islands Saint St United Nations Trafficking Human Persons Anti Counter Federal Bureau Border Customs Immigration
Passport Citizenship Constabulary Defence Defense Army Navy Organised Organized Crime Investigation Investigations Prosecutor
Prosecutors Public Prosecution Attorney General Minister Prime President Government Security Commission Council Authority
High Supreme Magistrate Magistrates Parish Circuit District State States Kingdom Union European Caribbean America American
North South East West Central New Old The A An In On At For Of And But With From By Monday Tuesday Wednesday Thursday Friday
Saturday Sunday January February March April May June July August September October November December Mr Mrs Ms Dr
Sergeant Inspector Superintendent Corporal Constable Detective Officer Senator Judge Justice Division Branch Task Team
Operation Interpol Europol Frontex Home Affairs Foreign Interior Justice Labour Labor Health Social Development Children Child
Women Child's Protection Family Services Agency Centre Center Hospital University College School Church Port Wharf Wharves
International Organization Organisation Migration Office Embassy Consulate Bank Group Network Ring Cartel Gang Programme Program
Act Law Bill Report Reports News Daily Times Gleaner Observer Star Post Herald Tribune Guardian Express Mail Today Weekly Online
COVID Christmas Easter Said Says According Meanwhile However Also Two Three Four Five Six Seven Eight Nine Ten Victims Victim
Officers Officials Authorities Rescue Rescued Assistance Support Shelter Safe House Region Regional Latin Western Eastern
Southern Northern Middle Gulf Sea Ocean Atlantic Pacific Bay River City Town County Province Parish Street Road Avenue
Circle Zone Wing Cell Desk Squad Directorate Company Corporation Ltd Limited Inc Electric Power Supply Airlines Airways
Balkans Boulevard Sector Station Detachment Command Headquarters Summary Writer Posted Updated Published Photo Image Video""".split())
_PLACE_WORDS = {w for aliases in COUNTRIES.values() for a in aliases for w in re.findall(r"[A-Z][a-zé'-]+", a)}
_NAME_RE = re.compile(r"\b([A-Z][a-zà-ÿ'’-]+(?:\s+(?:de|da|del|van|von|la|le)?\s*[A-Z][a-zà-ÿ'’-]+){1,3})\b")


_ACCUSED_RE = re.compile(r"(?i)(suspects?|accused|defendants?|convicted|sentenced|charged|indicted|alleged trafficker|"
                         r"trafficker|ringleader|leader|officer|official|minister|judge|prosecutor|director|commissioner)"
                         r"[\s,:]*(?:[a-z]+\s){0,2}$")


def _strip_names(text):
    def repl(m):
        words = re.findall(r"[A-Z][a-zà-ÿ'’-]+", m.group(1))
        if any(w in _STOP or w in _PLACE_WORDS for w in words):
            return m.group(0)
        if _ACCUSED_RE.search(text[max(0, m.start() - 40): m.start()]):
            return m.group(0)          # a named suspect, convicted person or official: kept as the source states it
        return "[name withheld]"
    return _NAME_RE.sub(repl, text)


def _title_case(text):
    words = re.findall(r"[A-Za-z][a-z'’-]{3,}", text)
    return bool(words) and sum(w[0].isupper() for w in words) / len(words) > 0.6


def scrub(text, trafficking=False, numbers_only=False):
    if not text:
        return text
    t = _ID_RE.sub(lambda m: m.group(1) + NUM, text)
    t = _BARE_RE.sub(NUM, t)
    t = _ADDR_RE.sub("[address withheld]", t)
    t = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b", "[email withheld]", t)
    if numbers_only:
        return t            # headlines keep their wording
    t = _VICTIM_RE.sub(lambda m: m.group(1) + "[name withheld]" + (" " if m.group(2).endswith(" ") else ""), t)
    if trafficking:
        # only in sentences about victims (rescued, girls, minors...): other sentences are about suspects and agencies
        t = " ".join(_strip_names(x) if _CUE_RE.search(x) else x for x in re.split(r"(?<=[.!?])\s+", t))
    return re.sub(r"(\[name withheld\]\s*){2,}", "[name withheld] ", t).replace("  ", " ")


def apply(ev):
    """Scrub every free-text field of a report (and the stored article facts) in place."""
    ht = "Human trafficking" in ev.get("categories", [])
    head = (ev.get("title") or "")[:40]
    for k in ("summary", "lead", "summary_text"):
        if ev.get(k):
            # a summary that just repeats the headline is treated like the headline
            ev[k] = scrub(ev[k], ht, numbers_only=bool(head) and ev[k].strip().startswith(head))
    if ev.get("title"):
        ev["title"] = scrub(ev["title"], numbers_only=True)
    art = ev.get("article") or {}
    for k in ("lead", "summary_text"):
        if art.get(k):
            art[k] = scrub(art[k], ht)
    for sec in (ev.get("specialist") or []) + (art.get("specialist") or []):
        for row in sec[1]:
            row[1] = scrub(row[1], ht)
    return ev
