#!/usr/bin/env python3
"""
Border Watch OSINT - the daily run.

  python run.py              # search the news (last 2 days), analyse, rebuild the website in docs/
  python run.py --days 30    # first run: fill in the last 30 days of history
  python run.py --demo       # no internet needed: invented sample data, to see how the site looks
  python run.py --rebuild    # no searching: just rebuild the website from the stored data
"""
import argparse
import datetime as dt
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from watch import analyze, collect, demo, extract, fulltext, record, report, store  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=None, help="how many days back to search")
    ap.add_argument("--demo", action="store_true", help="use invented sample data (no internet)")
    ap.add_argument("--rebuild", action="store_true", help="only rebuild the website from stored data")
    args = ap.parse_args()

    with open(os.path.join(HERE, "config.yaml"), encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    site = cfg.get("site") or {}
    days = args.days or (cfg.get("run") or {}).get("lookback_days", 2)
    db_path = os.path.join(HERE, "data", "demo_events.json" if args.demo else "events.json")
    out_dir = os.path.join(HERE, "docs")
    os.makedirs(out_dir, exist_ok=True)

    events = store.load(db_path)
    added = 0
    if not args.rebuild:
        if args.demo:
            print("Demo mode: using invented sample headlines.")
            cfg.setdefault("risk", {})["watchlist"] = ["Example Travel Agency"]   # demo watch list entry
            items = demo.sample_items()
        else:
            print(f"Searching the news for the last {days} days...")
            items = collect.collect(cfg, days)
        print(f"  {len(items)} headlines found in total")
        new = []
        focus = set(site.get("region_countries", [])) | {site.get("home_country", "")}
        for it in items:
            facts = extract.extract(it, focus)
            if not facts:
                continue
            ev = {**it, **facts, "id": store.make_id(it), "first_seen": dt.date.today().isoformat()}
            ev["date"] = ev.get("date") or ev["first_seen"]
            new.append(ev)
        print(f"  {len(new)} are on-topic")
        events, added = store.merge(events, new)
        print(f"  {added} new events added (the rest were repeats of stories already stored)")
        rc = cfg.get("run") or {}
        if not args.demo and rc.get("read_full_articles", True):
            risk_words = [extract.compile_words(i.get("words") or [])
                          for i in ((cfg.get("risk") or {}).get("indicators") or {}).values()]
            fulltext.read_articles(events, cfg, risk_words, focus,
                                   budget_minutes=float(rc.get("read_budget_minutes", 8)),
                                   limit=int(rc.get("read_limit", 400)))

    if args.rebuild:
        # re-read every stored headline with the current word lists, so changes apply to the whole history
        focus = set(site.get("region_countries", [])) | {site.get("home_country", "")}
        kept = []
        for ev in events:
            facts = extract.extract(ev, focus)
            if facts or (ev.get("article") or {}).get("categories"):
                ev.update(facts or {})
                kept.append(ev)
        print(f"Re-read {len(events)} stored events with the current word lists; {len(kept)} still on-topic.")
        events = kept

    # Re-score everything, so a change to config.yaml applies to the whole history.
    for ev in events:
        ev.setdefault("kind", "Incident")
        fulltext.apply_article(ev)
        analyze.score_event(ev, cfg.get("risk") or {}, site.get("home_places", []), site.get("region_countries", []),
                             site.get("region_words", []))
    # the full event record: ID, dates, location, connections, transport, outcome, review status, sources, related
    reviews = record.load_reviews(os.path.join(HERE, "reviews.yaml"))
    record.assign_ids(events)
    today = dt.date.today().isoformat()
    for ev in events:
        before = (ev.get("review_status"), ev.get("outcome"), ev.get("transport_mode"), ev.get("event_date"))
        record.build(ev, site, reviews)
        after = (ev.get("review_status"), ev.get("outcome"), ev.get("transport_mode"), ev.get("event_date"))
        if not ev.get("last_updated"):
            ev["last_updated"] = ev.get("first_seen", today)
        elif before[0] is not None and before != after:
            ev["last_updated"] = today
        if (ev.get("article") or {}).get("read_on", "") > ev["last_updated"]:
            ev["last_updated"] = ev["article"]["read_on"]
    record.related(events)
    store.save(db_path, events)

    keep_from = (dt.date.today() - dt.timedelta(days=(cfg.get("run") or {}).get("report_days", 180))).isoformat()
    # reports marked "excluded" in reviews.yaml stay in the data file but are not shown or counted
    shown = sorted([e for e in events if e.get("date", "") >= keep_from and e.get("review_status") != "Excluded"],
                   key=lambda e: e["date"], reverse=True)
    summary = analyze.summarise(shown, cfg)
    report.write_dashboard(out_dir, shown, summary, cfg, added, demo=args.demo)
    report.write_csv(out_dir, shown)
    report.write_bulletin(out_dir, shown, summary, cfg)
    print(f"Website rebuilt in docs/ with {len(shown)} events "
          f"({summary['by_level'].get('High', 0)} High, {summary['region_count']} in the {site.get('region_name', 'region')}).")


if __name__ == "__main__":
    main()
