# Border Watch OSINT: team guide

This guide explains what the site is, where its information comes from, how it sorts and scores reports, what each field
means, how we protect privacy, and how the team reviews and corrects reports. It is updated with every change to
the site. The change log is at the end.

- **Website:** https://tiffdaleyo.github.io/border-watch-osint/
- **Repository (code, settings, data):** https://github.com/Tiffdaleyo/border-watch-osint

---

## 1. What it is, and what it is not

Border Watch OSINT is an **unofficial** monitor of **open-source news** about anything that affects the movement
of people and goods across borders. That includes document fraud, irregular migration, migrant smuggling, human
trafficking, citizenship fraud, border integrity, visa and entry policy, and seizures at airports and ports. It
covers the whole world, and Caribbean and Jamaica stories come first.

- It is **not a government service**, and it is not linked to any agency's systems.
- It uses **public news only**. It never uses case files, official data or anything from work systems.
- Everything it shows is a **lead to verify**. Check the original article and official sources before acting.
- The repository and website are **public**. Never put case details, names from official systems or anything
  sensitive into them, including the review file.

## 2. How it runs every day

Everything runs automatically on GitHub, free of charge. No one needs to switch anything on.

1. **06:00 Jamaica time, every day:** GitHub starts the run (`.github/workflows/daily.yml`). A run takes about
   30 minutes.
2. **Collect:** it searches the news from the last 2 days (see section 3).
3. **Sort and extract:** it reads each headline and summary, decides which topics it belongs to, and pulls out the
   facts (section 5).
4. **Read full articles:** it opens up to 400 articles per run (about 8 minutes), Jamaica, the Caribbean and
   incidents first. It takes more precise facts from the article text. **The article text itself is never stored.**
   Only the extracted facts and a short summary are kept.
5. **Score:** each incident gets a risk score (section 7).
6. **Apply reviews:** it applies the team's review decisions from `reviews.yaml` (section 9).
7. **Privacy filter:** it removes ID numbers and victims' names (section 8).
8. **Publish:** it rebuilds the website, the CSV download and the weekly bulletin, then saves everything to the
   repository. A commit called "Daily update" appears each day.

To run it by hand: open the **Actions** tab, choose **daily-border-watch-osint**, then click **Run workflow**.

## 3. Where the information comes from

| Source | What it gives | Notes |
|---|---|---|
| Google News | Headlines and links | 9 editions: US, UK, Canada and Nigeria (English); Mexico, Colombia and Spain (Spanish); France (French); Brazil (Portuguese). About 100 English searches plus Spanish, French and Portuguese ones, listed in `config.yaml`. |
| GDELT | A free global news index | Extra coverage. If it is busy, the run skips it and carries on. |
| Agency RSS feeds | Optional | You can add official press-release feeds in `config.yaml` (`rss_feeds`). |
| The full article | Facts in more detail | Opened from the link. Only the facts are kept. |

The same story from several papers is stored **once**. Every publisher's link and date is kept under "Sources"
(up to 10).

## 4. Topics: seven main groups

Every report gets one or more topics. A report can sit in several groups. For example, a fake passport used by a
smuggling network is in both Document & Identity Fraud and Migration & Facilitation.

| Main group | Topics |
|---|---|
| **Document & Identity Fraud** | Passport fraud; visa and permit fraud; identity and document fraud (altered or counterfeit); impostors; supporting-document fraud (fake bank statements, letters, degrees); digital identity fraud (deepfakes, face morphing, fake e-visa sites) |
| **Migration & Facilitation** | Irregular migration; migrant smuggling; immigration enforcement; deportation and returns |
| **Human Trafficking** | Human trafficking (investigations, exploitation type, victim assistance, outcomes) |
| **Citizenship & Residence** | Citizenship and naturalisation (including citizenship by investment); application fraud (sham marriage, false applications, fake consultants) |
| **Border Integrity** | Corruption and insider facilitation; INTERPOL and watch lists (wanted persons); border security; aviation security; terrorism and sanctions |
| **Policy & Systems** | Visa and entry policy; border technology (ETIAS, EES, ETAs, e-gates, biometrics); health travel rules |
| **Seizures & Contraband** | Drugs; firearms; cash couriers; wildlife; cargo operations |

**Choices to explain to the team:**
- Terrorism and sanctions, and aviation security, sit under **Border Integrity**, because they concern screening
  and the security of the border itself.
- Health travel rules sit under **Policy & Systems**, because they are entry rules.
- Cargo operations and wildlife sit under **Seizures & Contraband**.
- **Human trafficking and migrant smuggling are always separate topics.** A report gets both only when its own
  words support each one. Vague phrases such as "undocumented migrants" do not count as smuggling.

**Incident or Update:**
- An **Incident** is a crime or enforcement action, such as fraud, smuggling, an arrest or a seizure.
- An **Update** is news without a specific crime, such as a new visa rule, a policy change, a deportation flight or a
  border system. Updates are not risk-scored.

Topic words live in `watch/extract.py` (CATEGORIES). The groups are in the same file (GROUPS).

## 5. The event record: every field

Open **Full record** under any report on the website to see every field. The same fields appear in the CSV
download. **Anything the report does not state is shown as "Not reported".** Nothing is guessed from a headline.

| Field | What it means |
|---|---|
| Event ID | A permanent reference, for example `BWO-2026-0153`. Use it to discuss or review a report. You can search for it on the site. |
| Title | The headline as published. |
| Summary | The opening 2–4 sentences of the article (privacy-filtered), or the news summary if the article could not be read. |
| Primary category | The single most specific topic, for example Human trafficking ahead of Irregular migration. |
| Additional tags | Its other topics. |
| Main group(s) | Which of the 7 groups the topics fall in. |
| Event date | When it happened, **only if the article says so**. It is marked *exact* (a date is written), *approximate* (for example "on Monday" or "last week") or *unknown*. |
| Publication date | When the article was published. |
| First captured / Last updated | When the site first found the report, and when its record last changed (a new source, a full read or a review). |
| Country / territory, City, Airport, Seaport, Border crossing | The places named in the report. |
| Route (as stated) | From → to, only when the report states it, for example "bound for London". |
| Caribbean connection | What kind of link the report has to the region: origin, destination, transit, occurred in or named, or another explicit link. Otherwise "None identified". |
| Jamaica connection | The specific link to Jamaica: a Jamaican airport or port, a journey that started in or was bound for Jamaica, PICA named, or "named in the report (role not stated)". |
| Transport mode | Air passenger, air cargo, maritime cargo, small vessel, land, or postal / courier. "Mixed" means more than one is stated. |
| Document types | Passport, visa, residence or work permit, ID card, birth certificate and so on. |
| Reporting agency | The agencies named, for example JCF, PICA, CBP, NCA or INTERPOL. |
| Reported outcome | The furthest stage stated: sentenced, acquitted, convicted, charged, arrested, refused entry, seized or intercepted, or investigation ongoing. Updates show "Not applicable". |
| Review status | Automatically collected, Awaiting review, Reviewed or Corrected (section 9). |
| Sources | Every publisher that carried the story, with links and dates. |
| Related events | Up to 3 other reports on the same topic within 90 days that share places, a route or wording. Click one to jump to it. |

**Never recorded:** nationality. The site records places (where something happened, a route) and the country that
issued a document. It never records the nationality of a person.

## 6. Specialist fields (shown only for the matching category)

Some categories have extra fields. They appear in the Full record under a "… details" heading, and only for
reports in that category. Each field still shows "Not reported" unless the article states it.

| Category | Extra fields |
|---|---|
| Document fraud | Document type; issuing country of the document; reported fraud method (counterfeit, forged or altered, stolen blank, stolen genuine, fraudulently obtained genuine, impostor, document factory); number of documents; blank versus issued documents; detection stage (check-in, boarding gate, departure or arrival immigration, transit, baggage, application, mail, cargo, at sea, land border, inland) |
| Visa / permit fraud | Visa or permit type; purported issuing authority; reported method (forged visa or stamp, forged approval or letter, fraudulent supporting documents, fake agent or website, bribery, sham marriage) |
| Impostor use | Use of another person's genuine document; detection point; the source's own description of the method |
| Migrant smuggling | Reported origin, transit and destination; transport mode; people intercepted; alleged facilitators **by role only** (network, smugglers, boat captain, driver, travel agent, document supplier, corrupt official, safe house); reported fees and currency |
| Human trafficking | Exploitation type; potential or suspected victims and identified or rescued victims, **kept separate as the source states them**; assistance or referral reported; proceedings |
| Citizenship / residence fraud | Programme involved; application stage; alleged misrepresentation; documents involved; administrative or court outcome |
| Border integrity | Organisation or role implicated (only in corruption or insider reports); alleged conduct; location; investigation, disciplinary or criminal outcome |
| Wanted-person interception | Notice or warrant (Red Notice, arrest warrant, extradition request…); agency reporting it; stated basis; reported outcome (arrested, extradited, deported…) |
| Policy update | Issuing authority; affected travellers or documents; announcement date; effective date; exceptions; status (proposed, active, delayed or withdrawn); official guidance link (that country's official immigration site) |

These fields fill in best when the full article was read. Most older reports were captured from headlines only.
They fill in as articles are re-read, up to 400 per day.

## 7. Risk score

Only **incidents** are scored, from 0 to 100. **High** means 40 points or more, and **Medium** means 20 or more.
A high score means "worth a closer look", never proof. The score **never** uses nationality. Click "Why this score"
on any report to see which indicators it matched.

| Indicator | Points |
|---|---|
| Document factory or forging equipment | 20 |
| Terrorism link | 20 |
| Organised network or ring | 15 |
| Possible insider or corruption | 15 |
| Impostor or look-alike use of a genuine document | 15 |
| Exploitation or trafficking indicators | 15 |
| Wanted person or INTERPOL notice | 15 |
| Concealment method (body, luggage, cargo) | 15 |
| Cargo red flags (misdeclared, front company, transshipment) | 15 |
| Weapons involved | 10 |
| Transit or onward route | 10 |
| Citizenship or residence by investment | 10 |
| Digital, biometric or e-visa fraud | 10 |
| Detected at an airport or border post | 5 |
| 5+ documents (50+ documents) | 10 (20) |
| 10+ people | 10 |
| 10+ kg (500+ kg) | 10 (20) |
| A watch-list term | always High |

Points and words are set in `config.yaml` under `risk`. The watch list is `risk: watchlist:`. Add public names or
terms to track, such as a known front company.

## 8. Privacy rules, and why

The site republishes public news, but it is itself public. So it follows the same care an analyst would.

| Rule | What happens | Why |
|---|---|---|
| Passport, ID and similar numbers | Replaced with "[number withheld]" everywhere, including headlines | They identify a person and add nothing to trend analysis. Even when printed once in a paper, republishing them in a searchable database creates a new risk. |
| Victims' names | Removed from summaries in human-trafficking reports (sentences about victims, rescued people, minors) and wherever a name directly follows "victim" | Victims are protected people. Publishing their identity can put them at risk and harm cases. |
| Suspects, people charged or convicted, officials, agencies | Kept as the source states them, with the allegation or outcome attributed to the source | These are publicly documented cases, and the names help explain them. |
| Private street addresses and email addresses | Replaced with "[address withheld]" or "[email withheld]" | Not needed for the analysis. |
| Nationality | Never recorded or scored | It should not drive risk. |
| Headlines | Kept as published (only numbers removed) | They are the publisher's own public words and the link to the source. |
| Full article text | Never stored | Copyright, and the data minimisation principle. |

The filter works by word matching, so it can miss a name or remove a harmless one. If you spot a name that should
not be there, mark the report **excluded** or **corrected** in `reviews.yaml`.

## 9. Reviewing and correcting reports (`reviews.yaml`)

Every report starts as **Automatically collected**. High-risk reports and those naming Jamaica start as
**Awaiting review**.

To record a review:

1. Open https://github.com/Tiffdaleyo/border-watch-osint/blob/main/reviews.yaml and click the **pencil** icon.
2. Under `reviews:`, add the report's Event ID with one of these statuses:
   - `reviewed`: checked, and it is right.
   - `corrected`: you fixed fields. List them under `corrections:`.
   - `excluded`: off-topic or wrong. It is hidden from the site and the counts, but kept in the data file.
3. You can add a `note` (a short public reason) and `by` (your initials).
4. Click **Commit changes**. The site shows the result after the next daily run, or straight away if you run the
   workflow by hand.

Fields you can correct: title, primary_category, categories, event_date, event_date_quality, countries, origin,
destination, transport_mode, outcome, agencies, summary_text, level.

```yaml
reviews:
  BWO-2026-0042:
    status: reviewed
    by: RR
  BWO-2026-0107:
    status: corrected
    note: Route was Kingston to Toronto
    corrections:
      destination: Canada
      transport_mode: Air passenger
  BWO-2026-0200:
    status: excluded
    note: Sports story, not border related
```

Keep the spaces at the start of lines exactly as shown, two per level. **Never put case details in this file: it
is public.**

## 10. Using the website

- **Filter bar (top):** choose the period, the scope (World, Caribbean or Jamaica), the main group, topic, country,
  transport mode, review status, or incidents and updates. You can also search headlines or an Event ID. Every
  chart, list and number follows the filters. Click any bar or map bubble to filter by it.
- **Key numbers:** reports, high-risk incidents, Caribbean, Jamaica, policy updates and weight seized, compared with
  the previous period.
- **Map:** countries named. A red pulse means the country has high-risk incidents.
- **Priority feed:** high-risk incidents and anything naming Jamaica.
- **Trend lookup:** research a route (origin → destination) with live news-index results and ready-made searches.
- **Charts:** activity over time and risk mix by main group, topics, countries, routes, airports and transport mode.
- **Seizures & Contraband** and **Policy & Systems** sections, plus watch-list hits.
- **All reports:** a sortable table. Click **Full record** for every field, including specialist fields. Click
  **Why this score** to see the indicators matched.
- **Downloads:** the CSV (opens in Excel, with every field) and the **weekly bulletin** (one page to print or email).

## 11. Known limits

- It works by **word matching, not AI**. Expect some off-topic items and some misses. Use `excluded`, and tell the
  maintainer which words cause trouble.
- **Weights** are the first weight the article mentions. An article that reports a yearly total can inflate the
  "weight seized" figure.
- **Event dates, transport mode, outcomes and specialist fields** depend on the full article. Paywalled or blocked
  sites cannot be read, so those reports show more "Not reported".
- **Google News and GDELT** sometimes limit requests. On a busy day, some searches are skipped and caught up the
  next day.
- The **Trend lookup** live results depend on GDELT being reachable from your browser.
- The site shows the last **180 days**. Older data stays in `data/events.json`.

## 12. Changing settings

Everything adjustable is in `config.yaml`. Edit it on GitHub with the pencil icon, then commit.

| To change | Where |
|---|---|
| Search words | `sources: google_news: queries:` (per language) and `sources: gdelt: queries:` |
| News editions | `sources: google_news: editions:` |
| Add an agency RSS feed | `sources: rss_feeds:` |
| Home country and region | `site: home_country`, `home_places`, `region_countries` |
| Risk points and bands | `risk: indicators:`, `risk: bands:` |
| Watch list | `risk: watchlist:` |
| How far back to search / show | `run: lookback_days`, `run: report_days` |
| Full-article reading | `run: read_full_articles`, `read_limit`, `read_budget_minutes` |

Topic words and the seven groups are in `watch/extract.py`. Specialist-field words are in `watch/specialist.py`.
Privacy rules are in `watch/privacy.py`.

## 13. Files at a glance

| File | Purpose |
|---|---|
| `config.yaml` | All settings |
| `reviews.yaml` | Team review decisions |
| `run.py` | Runs every step in order |
| `watch/collect.py` | Searches the news |
| `watch/extract.py` | Topics, groups, places, routes, numbers |
| `watch/fulltext.py` | Reads full articles (facts only) |
| `watch/record.py` | The event record (IDs, dates, location, connections, review status, sources, related) |
| `watch/specialist.py` | Category-specific fields |
| `watch/privacy.py` | Privacy filter |
| `watch/analyze.py` | Risk score and trends |
| `watch/report.py`, `watch/dashboard.html` | Website, CSV and bulletin |
| `data/events.json` | All stored reports |
| `docs/` | The published website |
| `TEAM-GUIDE.md` | This guide |

---

## Change log

| Date | Change |
|---|---|
| 2026-11-25 | Site created: daily collection from Google News and GDELT, topic sorting, risk score, website, CSV and weekly bulletin. |
| 2026-11-25 | Scope widened from document fraud to the whole border picture: migration, visa policy, citizenship, INTERPOL, deportations, drugs, cash, firearms, terrorism, aviation security, wildlife, health rules, cargo. Worldwide, Caribbean first. |
| 2026-11-25 | Dashboard redesigned: dark interactive dashboard with map, charts, filters and click-to-filter. |
| 2026-11-25 | Trend lookup added (route research). |
| 2026-11-25 | Full-article reading added (facts only; text never stored). |
| 2026-11-26 | Full event record: Event IDs, primary category and tags, event vs publication date, location, Caribbean and Jamaica connection, transport mode, agency, outcome, review status (`reviews.yaml`), all sources, related events, "Not reported" for anything not stated. |
| 2026-11-26 | Topics reorganised into seven main groups. New topics: supporting-document fraud, digital identity fraud, application fraud, corruption and insider facilitation, border technology. Trafficking and smuggling kept separate. Seizures & Contraband section and transport-mode chart added. |
| 2026-11-26 | Specialist fields per category, and the privacy filter (ID numbers, victims' names, private addresses and emails removed; charged or convicted names kept as reported). This team guide started. |
