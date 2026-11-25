# Border Watch OSINT

**Unofficial project, open-source news only.** Not a government service and not linked to any agency's official systems.

A free, automatic open-source news monitor for **anything that affects the movement of people across borders**: irregular migration trends, fake passports and visas, identity fraud, impostors, migrant smuggling and human trafficking, new visa and entry requirements, citizenship fraud and citizenship-by-investment, INTERPOL and watch-list news, deportations and border security. It covers the **whole world**, with **Caribbean and Jamaica** stories shown first and highlighted. No paid accounts, no API keys.

Every morning (06:00 Jamaica time) GitHub runs it for you. It:

1. **Collects** headlines from Google News (9 country/language editions), the GDELT global news index and any agency RSS feeds you add.
2. **Sorts** each report into topics and marks it as an **Incident** (a crime: fraud, smuggling, an arrest) or an **Update** (a new visa rule, a policy change, a deportation flight, a border system).
3. **Extracts** the facts: topic, document type, countries, airports, route (from → to), number of documents and people. It reads English, Spanish, French and Portuguese.
4. **Scores** each incident from 0 to 100 using plain, visible indicators (organised network, document factory, insider, impostor, INTERPOL notice, transit route, scale...). High = worth a closer look, never proof. It never scores nationality.
5. **Publishes** a website (`docs/index.html`) with a Caribbean-first list, a visa and policy changes list, your watch list hits, charts, filters and search, a CSV file for Excel and a weekly one-page bulletin (`docs/bulletin.html`).

> Leads from open-source news only. Verify every item against the original article and official sources before acting. This repository is public: never put case files, names from official systems or anything classified in it.

## Files

| File | What it does |
|---|---|
| `config.yaml` | **All the settings**: search words, news editions, risk points, your home country and region. Edit this to change what it looks for. |
| `run.py` | Runs everything in order. |
| `watch/collect.py` | Searches the news sources. |
| `watch/extract.py` | Finds topics, places, routes and numbers in each headline. |
| `watch/places.py` | Country, city and airport names it recognises. |
| `watch/analyze.py` | Risk score and summaries (topics, countries, routes, weekly trends). |
| `watch/report.py`, `watch/dashboard.html` | Build the website, CSV and bulletin. |
| `watch/demo.py` | Invented sample headlines for the demo. |
| `.github/workflows/daily.yml` | Tells GitHub to run it every day and save the results. |
| `data/events.json` | The growing history of events (plain text). |
| `docs/` | The website GitHub Pages shows. |

## Run it by hand on GitHub

**Actions** tab → **daily-border-watch-osint** → **Run workflow**. Use `30` days for the very first run to fill in a month of history.

## Run it on your own computer (optional)

```
pip install -r requirements.txt
python run.py --demo      # invented data, no internet needed
python run.py --days 30   # real search, last 30 days
```

## Common changes

- **Add a search phrase:** add it under `sources > google_news > queries` (and `gdelt > queries`) in `config.yaml`.
- **Add an agency feed:** add `- {name: "Agency", url: "https://.../rss"}` under `rss_feeds`.
- **Flag a name, company, vessel or route:** add it under `risk > watchlist`. Any matching report becomes High and appears in the "Watch list hits" box. The site is public, so only list things that are already public.
- **Topics now covered:** passport, visa and document fraud; impostors; irregular migration; visa and entry rules; citizenship; INTERPOL and watch lists; deportations; border security; drug trafficking; cash couriers; firearms; terrorism and sanctions; aviation security; wildlife smuggling; health travel rules; cargo operations; migrant smuggling and human trafficking. Topic words live in `watch/extract.py` (CATEGORIES).
- **Change your region:** edit `site > region_countries` and `region_words`.
- **Change the risk points:** edit `risk > indicators`.
- **Recognise a new airport or city:** add it in `watch/places.py`.

## Known limits (first version)

- It reads headlines and short summaries, not full articles, so some facts are missed.
- Word matching, not AI: expect some off-topic items and some misses. Report them and adjust the words.
- Trends ("Rising", "Falling") need about 5 weeks of history.
