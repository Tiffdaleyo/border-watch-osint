"""Scores each event and builds the summaries shown on the website.

The score is a simple, transparent points system set in config.yaml (section 'risk').
It flags events worth a closer look. It is never proof, and it never scores a person's nationality.
"""
import datetime as dt
from collections import Counter, defaultdict

from .extract import compile_words, find_words, fold


def score_event(ev, risk_cfg, home_places, region_countries, region_words=()):
    art = ev.get("article") or {}
    folded = fold(f"{ev.get('title', '')}. {ev.get('summary', '')}. {art.get('lead', '')}. {'. '.join(art.get('terms', []))}")
    reasons, score = [], 0
    for key, ind in (risk_cfg.get("indicators") or {}).items():
        hits = find_words(compile_words(ind.get("words") or []), folded)
        if key == "airport" and not hits and ev.get("airports"):     # a named airport counts too
            hits = [ev["airports"][0]]
        if hits:
            score += int(ind.get("points", 0))
            reasons.append(f"{ind.get('label', key)} (+{ind.get('points', 0)}: {', '.join(hits[:3])})")
    md = risk_cfg.get("many_documents") or {}
    n = ev.get("documents_count") or 0
    if md and n >= md.get("big_threshold", 10 ** 9):
        score += md.get("big_points", 0)
        reasons.append(f"Large number of documents: {n} (+{md.get('big_points', 0)})")
    elif md and n >= md.get("threshold", 10 ** 9):
        score += md.get("points", 0)
        reasons.append(f"Several documents: {n} (+{md.get('points', 0)})")
    mp = risk_cfg.get("many_people") or {}
    p = ev.get("people_count") or 0
    if mp and p >= mp.get("threshold", 10 ** 9):
        score += mp.get("points", 0)
        reasons.append(f"Many people involved: {p} (+{mp.get('points', 0)})")
    wt = risk_cfg.get("weight") or {}
    kg = ev.get("weight_kg") or 0
    if wt and kg >= wt.get("big_threshold_kg", 10 ** 9):
        score += wt.get("big_points", 0)
        reasons.append(f"Very large quantity: about {kg:g} kg (+{wt.get('big_points', 0)})")
    elif wt and kg >= wt.get("threshold_kg", 10 ** 9):
        score += wt.get("points", 0)
        reasons.append(f"Large quantity: about {kg:g} kg (+{wt.get('points', 0)})")
    score = min(score, 100)
    bands = risk_cfg.get("bands") or {"high": 40, "medium": 20}
    level = "High" if score >= bands["high"] else "Medium" if score >= bands["medium"] else "Low"
    if ev.get("kind") == "Update":
        # policy, security and deportation news: worth knowing, but not a crime to score
        score, level, reasons = 0, "Update", []
    watch = find_words(compile_words(risk_cfg.get("watchlist") or []), folded)
    if watch:
        level = "High"
        reasons.insert(0, f"WATCHLIST match: {', '.join(watch)}")
    ev["score"], ev["level"], ev["reasons"] = score, level, reasons
    home = [fold(x) for x in home_places]
    ev["watch"] = bool(watch)
    ev["home"] = any(h and h in folded for h in home)
    ev["region"] = (ev["home"] or any(c in region_countries for c in ev.get("countries", []))
                    or bool(find_words(compile_words(list(region_words)), folded)))
    return ev


def _date(ev):
    try:
        return dt.date.fromisoformat(ev["date"][:10])
    except Exception:
        return None


def summarise(events, cfg, today=None):
    """Numbers for the website: totals, top countries, routes, airports, and this-week-vs-usual trends."""
    today = today or dt.date.today()
    a = cfg.get("analysis") or {}
    week = int(a.get("trend_days", 7))
    base_weeks = int(a.get("baseline_weeks", 4))

    by_cat, by_country, by_route, by_airport, by_level = Counter(), Counter(), Counter(), Counter(), Counter()
    recent_cat, base_cat = Counter(), Counter()
    per_week = defaultdict(int)
    for ev in events:
        d = _date(ev)
        for c in ev["categories"]:
            by_cat[c] += 1
        for c in ev["countries"]:
            by_country[c] += 1
        if ev.get("origin") or ev.get("destination"):
            o, de = ev.get("origin"), ev.get("destination")
            by_route[f"{o} → {de}" if o and de else (f"Origin: {o}; destination not reported" if o
                     else f"Destination: {de}; origin not reported")] += 1
        for ap in ev.get("airports", []):
            by_airport[ap] += 1
        by_level[ev["level"]] += 1
        if d:
            age = (today - d).days
            monday = d - dt.timedelta(days=d.weekday())
            per_week[monday.isoformat()] += 1
            for c in ev["categories"]:
                if 0 <= age < week:
                    recent_cat[c] += 1
                elif week <= age < week * (base_weeks + 1):
                    base_cat[c] += 1

    trends = []
    for c in sorted(set(recent_cat) | set(base_cat)):
        usual = base_cat[c] / base_weeks
        now = recent_cat[c]
        if now >= 3 and now >= 2 * max(usual, 1):
            note = "Rising"
        elif usual >= 2 and now <= usual / 2:
            note = "Falling"
        else:
            note = "Steady"
        trends.append({"category": c, "this_week": now, "usual_week": round(usual, 1), "note": note})

    return {
        "total": len(events),
        "by_level": dict(by_level),
        "by_category": by_cat.most_common(),
        "by_country": by_country.most_common(25),
        "by_route": by_route.most_common(15),
        "by_airport": by_airport.most_common(15),
        "per_week": sorted(per_week.items())[-26:],
        "trends": trends,
        "home_count": sum(1 for e in events if e.get("home")),
        "update_count": sum(1 for e in events if e.get("kind") == "Update"),
        "watch_count": sum(1 for e in events if e.get("watch")),
        "region_count": sum(1 for e in events if e.get("region")),
    }
