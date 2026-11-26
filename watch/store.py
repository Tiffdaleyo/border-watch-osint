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
            if ev.get("url") and all(s.get("url") != ev["url"] and s.get("publisher") != ev.get("source")
                                     for s in old["sources"]) and len(old["sources"]) < 10:
                old["sources"].append({"publisher": ev.get("source", ""), "url": ev["url"], "date": ev.get("date", ""),
                                       "lang": ev.get("lang", ""), **({"official": True} if ev.get("official") else {})})
                old["last_updated"] = ev.get("first_seen", "")
            continue
        by_id[ev["id"]] = ev
        added += 1
    return list(by_id.values()), added
