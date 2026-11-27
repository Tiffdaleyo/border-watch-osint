"""Keeps every event in one file, data/events.json, so the history grows day by day.
It is a plain text file: you can open it on GitHub and read it."""
import hashlib
import json
import os
import re

from .extract import fold


def load(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, events):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    events = sorted(events, key=lambda e: (e.get("date", ""), e["id"]), reverse=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=1)


def title_key(title):
    """The same story often appears in several papers with the same headline. This key spots that."""
    return re.sub(r"[^a-z0-9 ]", "", fold(title))[:90].strip()


def make_id(item):
    return hashlib.sha1(title_key(item["title"]).encode()).hexdigest()[:12]


def merge(existing, new):
    """Adds new events, skipping repeats of a story already stored. Returns (all events, number added)."""
    by_id = {e["id"]: e for e in existing}
    added = 0
    for ev in new:
        old = by_id.get(ev["id"])
        if old:
            # same story seen again: remember the extra source, keep the earliest date
            srcs = set(old.get("other_sources", [])) | {ev.get("source", "")}
            srcs.discard(old.get("source", ""))
            srcs.discard("")
            old["other_sources"] = sorted(srcs)
            # keep every publisher's link and date (up to 10) so the record lists all sources
            if old.get("sources") is None:
                old["sources"] = [{"publisher": old.get("source", ""), "url": old.get("source_url") or old.get("url", ""),
                                   "date": old.get("date", "")}]
            if ev.get("official"):
                old["official"] = True
            if ev.get("mission"):
                old["mission"] = True
            if ev.get("url") and all(s.get("url") != ev["url"] and s.get("publisher") != ev.get("source")
                                     for s in old["sources"]) and len(old["sources"]) < 10:
                old["sources"].append({"publisher": ev.get("source", ""), "url": ev["url"], "date": ev.get("date", ""),
                                       "lang": ev.get("lang", ""), **({"official": True} if ev.get("official") else {})})
                old["last_updated"] = ev.get("first_seen", "")
            continue
        by_id[ev["id"]] = ev
        added += 1
    return list(by_id.values()), added


# ---------------------------------------------------------------------------------------------
# the same story from several outlets, with different headlines: grouped into one event
# ---------------------------------------------------------------------------------------------
import collections as _col
import datetime as _dt
import math as _math
import re as _re

from . import extract as _extract

_STOP = set("the a an of in on at to for and or with by from after over as is are was were be has have its it this "
            "that into than more about new says say said us u.s. de la el los las en y del por con para un una le les "
            "des du et au pour sur dans da do dos das em no na com".split())


def _toks(title):
    t = _re.sub(r"(\d)[,.](\d{3})", r"\1\2", _extract.fold(title))
    return {w for w in _re.findall(r"[a-z][a-z'-]{2,}|\d+(?:\.\d+)?", t) if w not in _STOP}


def group_duplicates(events, window_days=4):
    """Reports of one story with different headlines (e.g. eight outlets on the same arrest) become one event: the
    earliest keeps its Event ID and gains every other report as a source; the others' IDs are kept in merged_ids so
    old links still find it. Two reports count as the same story only when, within a few days, they are the same kind,
    share their specific numbers (if both give numbers) and countries (if both name countries), and their headlines
    share several distinctive words. Returns (events, number merged)."""
    toks = [_toks(e.get("title", "")) for e in events]
    nums = [{w for w in t if w[0].isdigit() and len(w) >= 2} for t in toks]
    ctry = [set(e.get("countries") or []) for e in events]
    df = _col.Counter(w for t in toks for w in t)
    n = len(events) or 1
    idf = {w: _math.log(n / c) for w, c in df.items()}

    def day(e):
        try:
            return _dt.date.fromisoformat((e.get("date") or "")[:10])
        except ValueError:
            return _dt.date.min

    days = [day(e) for e in events]

    def same(i, j):
        a, b = events[i], events[j]
        if a.get("title_only") or b.get("title_only") or a.get("kind") != b.get("kind"):
            return False
        if nums[i] and nums[j] and not nums[i] & nums[j]:
            return False
        if ctry[i] and ctry[j] and not ctry[i] & ctry[j]:
            return False
        sh = toks[i] & toks[j]
        small = min(len(toks[i]), len(toks[j])) or 1
        anchor = bool(nums[i] & nums[j]) or any(df[w] <= 20 for w in sh if not w[0].isdigit())
        return anchor and len(sh) >= 3 and len(sh) / small >= 0.4 and sum(idf[w] for w in sh) >= 16

    order = sorted(range(len(events)), key=lambda i: (days[i], events[i].get("first_seen", ""), events[i].get("event_id", "")))
    groups = []
    for i in order:
        home = None
        for g in reversed(groups):
            if (days[i] - days[g[0]]).days > window_days:
                break
            if same(g[0], i) and (len(g) < 2 or sum(same(m, i) for m in g) * 2 >= len(g)):
                home = g
                break
        if home:
            home.append(i)
        else:
            groups.append([i])
    drop = set()
    for g in groups:
        if len(g) < 2:
            continue
        main = events[g[0]]
        main.setdefault("sources", [{"publisher": main.get("source", ""), "url": main.get("source_url") or main.get("url", ""),
                                     "date": main.get("date", ""), "lang": main.get("lang", "")}])
        for k in g[1:]:
            d = events[k]
            drop.add(k)
            main["merged_ids"] = sorted(set(main.get("merged_ids", [])) | {d.get("event_id", "")} | set(d.get("merged_ids", [])) - {""})
            for s in d.get("sources") or [{"publisher": d.get("source", ""), "url": d.get("source_url") or d.get("url", ""),
                                           "date": d.get("date", ""), "lang": d.get("lang", "")}]:
                if len(main["sources"]) < 25 and all(s.get("url") != x.get("url") for x in main["sources"]):
                    main["sources"].append(s)
            main["other_sources"] = sorted((set(main.get("other_sources", [])) | {d.get("source", "")} |
                                            set(d.get("other_sources", []))) - {"", main.get("source", "")})
            if d.get("official"):
                main["official"] = True
            if d.get("alerted"):
                main["alerted"] = True
            if (d.get("article") or {}).get("read") and not (main.get("article") or {}).get("read"):
                main["article"] = d["article"]
            main["first_seen"] = min(main.get("first_seen") or "9", d.get("first_seen") or "9")
    return [e for i, e in enumerate(events) if i not in drop], len(drop)
