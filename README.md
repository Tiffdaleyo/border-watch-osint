# Border Watch OSINT

**Unofficial project, open-source news only.** Not a government service and not linked to any agency's official systems.

A free, automatic open-source news monitor for **anything that affects the movement of people across borders**: irregular migration trends, fake passports and visas, identity fraud, impostors, migrant smuggling and human trafficking, new visa and entry requirements, citizenship fraud and citizenship-by-investment, INTERPOL and watch-list news, deportations and border security. It covers the **whole world**, with **Caribbean and Jamaica** stories shown first and highlighted. No paid accounts, no API keys.

Every morning (06:00 Jamaica time) GitHub runs it for you. It:

1. **Collects** official press releases first (PICA, JCF, CBP, ICE, UK Border Force, Home Office, NCA, CBSA, Europol, Frontex, IOM, UNODC and others, marked OFFICIAL), then headlines from Google News (9 country/language editions) and the GDELT global news index.
2. **Sorts** each report into topics and marks it as an **Incident** (a crime: fraud, smuggling, an arrest) or an **Update** (a new visa rule, a policy change, a deportation flight, a border system).
3. **Extracts** the facts: topic, document type, countries, airports, route (from → to), number of documents and people. It reads English, Spanish, French and Portuguese.
4. **Scores** each incident from 0 to 100 using plain, visible indicators (organised network, document factory, insider, impostor, INTERPOL notice, transit route, scale...). High = worth a closer look, never proof. It never scores nationality.
5. **Publishes** a website (`docs/index.html`) with a Caribbean-first list, a visa and policy changes list, your watch list hits, charts, filters and search, a CSV file for Excel and a weekly one-page bulletin (`docs/bulletin.html`).

> Leads from open-source news only. Verify every item against the original article and official sources before acting. This repository is public: never put case files, names from official systems or anything classified in it.

**Team guide:** [TEAM-GUIDE.md](TEAM-GUIDE.md) explains everything in plain language (sources, topics, every field, scoring, privacy rules, reviews, limits) and keeps a change log.

**Privacy:** ID and passport numbers, victims' names, private addresses and emails are removed from summaries before anything is saved or published (`watch/privacy.py`). Names of people charged or convicted, officials and agencies are kept as the source states them. Nationality is recorded only when stated in words and is never used in the risk score.

**Email:** a one-page PDF bulletin every Monday and alert emails for new high-risk or Jamaica-linked incidents, once the email secrets are added (see TEAM-GUIDE.md, section 11).

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
- **Topics now covered**, in seven main groups (a report can carry several topics; human trafficking and migrant smuggling are separate and both are applied only when the report supports each):
  - *Document & Identity Fraud*: passport fraud, visa and permit fraud, identity and document fraud (altered, counterfeit), impostors, supporting-document fraud, digital identity fraud
  - *Migration & Facilitation*: irregular migration, migrant smuggling, immigration enforcement, deportation and returns
  - *Human Trafficking*: trafficking investigations, with exploitation type and victim assistance when reported
  - *Citizenship & Residence*: citizenship and naturalisation (incl. citizenship by investment), application fraud (sham marriage, false applications, fake consultants)
  - *Border Integrity*: corruption and insider facilitation, INTERPOL and watch lists, border security, aviation security, terrorism and sanctions
  - *Policy & Systems*: visa and entry policy, border technology (ETIAS, EES, ETAs, e-gates, biometrics), health travel rules
  - *Seizures & Contraband*: drugs, firearms, cash couriers, wildlife, cargo operations

  Topic words live in `watch/extract.py` (CATEGORIES); the groups are in GROUPS in the same file.
- **Reviewing reports:** open `reviews.yaml`, press the pencil, add the report's Event ID with `reviewed`, `corrected` or `excluded` (instructions are inside the file), then Commit changes. The site shows it after the next daily run. Excluded reports are hidden from the site but kept in the data.
- **The event record:** every report has a permanent ID (BWO-2026-0001), primary category and tags, event date (exact, approximate or unknown) and publication date, first captured and last updated, location (country, city, airport, seaport, border crossing), journey (origin, transit points, intended destination, interception, completeness, source basis), nationality only when stated in words (never inferred, never scored), Caribbean and Jamaica connection, transport mode, reporting agency, reported outcome, review status, all sources and related events. Anything the report does not state is shown as "Not reported": nothing is guessed from a headline. Open "Full record" under any report on the site, or download the CSV.
- **Change your region:** edit `site > region_countries` and `region_words`.
- **Change the risk points:** edit `risk > indicators`.
- **Recognise a new airport or city:** add it in `watch/places.py`.

## Known limits (first version)

- It reads headlines and short summaries, not full articles, so some facts are missed.
- Word matching, not AI: expect some off-topic items and some misses. Report them and adjust the words.
- Trends ("Rising", "Falling") need about 5 weeks of history.
