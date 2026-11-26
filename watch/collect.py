"""Searches free news sources: Google News, GDELT and any RSS feeds listed in config.yaml.
No API keys, no accounts. Only the headline, short summary, date, source name and link are kept."""
import datetime as dt
import email.utils
import html
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BorderWatchOSINT/1.0; open-source news monitor)"}


def log(*a):
    print(*a, flush=True)


THROTTLED = [0]     # how many times a service said "too many requests" in this run
DEADLINE = [None]   # time.monotonic() after which no new searches start (set by collect)


def _late():
    return DEADLINE[0] is not None and time.monotonic() > DEADLINE[0]


def _get(url, timeout=20, tries=3):
    for attempt in range(tries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            if r.status_code == 429:          # "too many requests": count it, wait a little, try once more
                THROTTLED[0] += 1
                if attempt or _late() or THROTTLED[0] > 20:
                    return None
                time.sleep(8)
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as exc:
            if attempt == tries - 1:
                log(f"    ! could not read {url[:90]}... ({type(exc).__name__})")
            time.sleep(3)
    return None


def strip_html(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def _rss_date(s):
    try:
        return email.utils.parsedate_to_datetime(s).date().isoformat()
    except Exception:
        return ""


def google_news(query, ed, days):
    q = urllib.parse.quote(f"{query} when:{days}d")
    url = f"https://news.google.com/rss/search?q={q}&hl={ed['hl']}&gl={ed['gl']}&ceid={ed['ceid']}"
    r = _get(url)
    if not r:
        return []
    out = []
    try:
        root = ET.fromstring(r.content)
    except ET.ParseError:
        return []
    for it in root.iter("item"):
        title = strip_html(it.findtext("title"))
        source = strip_html(it.findtext("source"))
        if source and title.endswith(" - " + source):        # Google adds " - Source name" to each headline
            title = title[: -len(source) - 3]
        summary = strip_html(it.findtext("description"))
        if summary.startswith(title):                       # Google's summary often just repeats the headline
            summary = ""
        out.append({"title": title, "summary": summary, "url": it.findtext("link") or "",
                    "date": _rss_date(it.findtext("pubDate")), "source": source,
                    "lang": ed["lang"], "via": f"Google News {ed['gl']}"})
    return out


def gdelt(query, days, maxrec=75):
    params = {"query": query, "mode": "ArtList", "format": "json", "timespan": f"{max(1, days)}d",
              "maxrecords": str(maxrec), "sort": "DateDesc"}
    r = _get("https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode(params), timeout=15, tries=2)
    if not r:
        return None             # GDELT did not answer
    try:
        data = r.json()
    except ValueError:          # GDELT answers in plain text when it is busy
        return None
    out = []
    for a in data.get("articles", []):
        sd = a.get("seendate", "")
        date = f"{sd[:4]}-{sd[4:6]}-{sd[6:8]}" if len(sd) >= 8 else ""
        out.append({"title": a.get("title", ""), "summary": "", "url": a.get("url", ""), "date": date,
                    "source": a.get("domain", ""), "lang": (a.get("language") or "")[:2].lower(), "via": "GDELT"})
    return out


def rss_feed(feed):
    r = _get(feed["url"])
    if not r:
        return []
    try:
        root = ET.fromstring(r.content)
    except ET.ParseError:
        return []
    out = []
    atom = "{http://www.w3.org/2005/Atom}"
    for it in list(root.iter("item")) + list(root.iter(atom + "entry")):
        title = strip_html(it.findtext("title") or it.findtext(atom + "title"))
        link = it.findtext("link") or ""
        if not link:
            el = it.find(atom + "link")
            link = el.get("href", "") if el is not None else ""
        date = _rss_date(it.findtext("pubDate") or "") or (it.findtext(atom + "updated") or "")[:10]
        summary = strip_html(it.findtext("description") or it.findtext(atom + "summary") or "")[:600]
        out.append({"title": title, "summary": summary, "url": link, "date": date,
                    "source": feed.get("name", ""), "lang": "", "via": "RSS"})
    return out


def page_links(feed):
    """Press-release pages without RSS: takes the links whose address contains `link_contains`."""
    import urllib.parse
    r = _get(feed["url"])
    if not r:
        return []
    out, seen = [], set()
    for m in re.finditer(r'<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r.text, re.S):
        href = urllib.parse.urljoin(feed["url"], m.group(1))
        text = strip_html(m.group(2))
        # a date written in the link ("News 25 November 2026 Title") or in the address (/2026/11/25/)
        date = ""
        dm = re.search(r"(\d{1,2}) (January|February|March|April|May|June|July|August|September|October|November|December) (20\d\d)", text)
        if dm:
            date = dt.datetime.strptime(" ".join(dm.groups()), "%d %B %Y").date().isoformat()
            text = text[dm.end():].strip() if dm.start() < 15 else text
        um = re.search(r"/(20\d\d)/(\d\d)/(\d\d)/", href)
        if um and not date:
            date = "-".join(um.groups())
        if (feed.get("link_contains", "") in href and href.rstrip("/") != feed["url"].rstrip("/")
                and 25 <= len(text) <= 220 and href not in seen):
            seen.add(href)
            out.append({"title": text, "summary": "", "url": href, "date": date, "source": feed.get("name", ""),
                        "lang": "", "via": "Official page"})
    return out[: int(feed.get("max", 15))]


def official_sources(cfg):
    """Official press releases (agency RSS feeds and news pages). Collected first, so Google limits never block them."""
    items = []
    for feed in (cfg.get("sources") or {}).get("official_feeds") or []:
        res = page_links(feed) if feed.get("type") == "page" else rss_feed(feed)
        for it in res:
            it["official"] = True
            it["agency_country"] = feed.get("country", "")
            if feed.get("kind") == "mission":   # embassy, high commission, consulate or foreign ministry
                it["mission"] = True
        items += res
        log(f"  Official {feed.get('name', feed['url'])}: {len(res)} items")
    return items


def collect(cfg, days, budget_minutes=None, official_only=False):
    src = cfg.get("sources") or {}
    budget = budget_minutes or float((cfg.get("run") or {}).get("search_budget_minutes", 20))
    DEADLINE[0] = time.monotonic() + budget * 60
    delay = float((cfg.get("run") or {}).get("delay_seconds", 1.5))
    items = official_sources(cfg)
    if official_only:
        src = {k: v for k, v in src.items() if k not in ("google_news", "gdelt", "rss_feeds")}
    gn = src.get("google_news") or {}
    if gn.get("enabled"):
        def one_edition(ed):
            found = []
            for q in (gn.get("queries") or {}).get(ed["lang"], []):
                if _late() or THROTTLED[0] > 20:
                    log(f"  Google News {ed['gl']}: stopping early (time budget reached or Google is limiting requests)")
                    break
                found += google_news(q, ed, days)
                time.sleep(delay)
            log(f"  Google News {ed['gl']}/{ed['lang']}: {len(found)} headlines")
            return found
        # the editions are searched side by side (3 at a time) so the daily run stays short
        with ThreadPoolExecutor(max_workers=3) as pool:
            for found in pool.map(one_edition, gn.get("editions", [])):
                items += found
    gd = src.get("gdelt") or {}
    if gd.get("enabled"):
        got, fails = 0, 0
        for q in gd.get("queries", []):
            if _late() or fails >= 2:      # GDELT is often slow; give up after two failed searches
                log("  GDELT: skipped the rest (time budget or GDELT not answering)")
                break
            res = gdelt(q, days)
            fails = fails + 1 if res is None else 0
            res = res or []
            items += res
            got += len(res)
            time.sleep(max(delay, 5))       # GDELT asks for one request every 5 seconds
        log(f"  GDELT: {got} headlines")
    for feed in src.get("rss_feeds") or []:
        res = rss_feed(feed)
        items += res
        log(f"  RSS {feed.get('name', feed['url'])}: {len(res)} items")
    if THROTTLED[0]:
        log(f"  note: news services asked us to slow down {THROTTLED[0]} times")
    cutoff = (dt.date.today() - dt.timedelta(days=days + 1)).isoformat()
    official_names = {n.lower() for n in src.get("official_publishers") or []}
    for i in items:          # a news-search result published by an agency itself is official too
        if i.get("source", "").lower() in official_names:
            i["official"] = True
    return [i for i in items if i["title"] and i["url"] and (not i["date"] or i["date"] >= cutoff)]
