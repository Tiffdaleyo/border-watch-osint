# Border Watch OSINT: team guide

This guide explains what the site is, where its information comes from, how it sorts and scores reports, what each field
means, how privacy is protected, and how the team reviews and corrects reports. It is updated with every change to
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

1. **About 05:15 Jamaica time, every day:** GitHub starts the run (`.github/workflows/daily.yml`). A run takes
   about 30 minutes. GitHub sometimes starts scheduled runs hours late, so there are two back-up start times
   (07:15 and 10:15). A back-up runs only if that day's collection has not happened yet.
2. **Collect:** it reads the official press releases first, then searches the news from the last 2 days
   (section 3).
3. **Sort and extract:** it reads each headline and summary, decides which topics it belongs to, and pulls out the
   facts (section 5).
4. **Read full articles:** it opens up to 400 articles per run (about 8 minutes), Jamaica, the Caribbean and
   incidents first. It takes more precise facts from the article text. **The article text itself is never stored.**
   Only the extracted facts and a short summary are kept.
5. **Score:** each incident gets a review-priority score (section 7).
6. **Apply reviews:** it applies the team's review decisions from `reviews.yaml` (section 9).
7. **Privacy filter:** it removes ID numbers and victims' names (section 8).
8. **Publish:** it rebuilds the website, the CSV and the bulletin page, and emails alerts for new high-priority or
   Jamaica incidents. Nothing waits for a review.
9. **Mondays, 07:00 Jamaica time:** a **draft** of the weekly bulletin (PDF, with charts and analysis) is emailed to
   the designated reviewer only. The team receives it after the reviewer presses **Send bulletin** (section 2b).

To run it by hand: open the **Actions** tab, choose **daily-border-watch-osint**, then click **Run workflow**.

## 2b. Review marks and the bulletin check

**Daily reports** go on the site automatically. A review is optional and is done report by report.

- **Automatically collected:** the normal state. The report was found and processed by the system and has not been
  checked by a person. Treat it as a lead.
- **Awaiting review:** the system found a reason to look again, for example the headline and the article disagree
  on the outcome.
- **Reviewed:** a person checked this report against its sources and recorded it in `reviews.yaml` (section 9).
  Only the reports listed there carry this mark, and the "Reviewed by a person" card counts them.

To review a report, fix it or remove it, add its Event ID to `reviews.yaml` (section 9). The change appears at the
next morning's run. To see it at once, open **Actions → publish → Run workflow**, which rebuilds the site (and sends any of today's alerts not yet sent) in about
2 minutes.

**The weekly bulletin is checked before the team gets it.**
1. Every Monday at about 07:00 Jamaica time, an email arrives for the reviewer only: **"DRAFT for review: Border
   Watch weekly bulletin"**, with the PDF attached. It covers the 7 days up to that Monday.
2. To correct or remove a report in it, record the decision in `reviews.yaml` by its Event ID (section 9).
3. To send it, open **Actions → send-bulletin → Run workflow** (the draft email has a direct link). The same week is
   rebuilt with any corrections, emailed to the team, and its PDF saved on the website as `docs/bulletin.pdf`.
   To send an older week, type its date in the box before pressing the button.

Who gets the draft: the address in the `MAIL_REVIEW_TO` secret; if that is not set, `MAIL_ALERTS_TO`, and failing
that `MAIL_TO`. If no one presses Send bulletin, the team receives nothing that week.

## 3. Where the information comes from

| Source | What it gives | Notes |
|---|---|---|
| **Official press releases** (read first, marked **OFFICIAL**) | Releases published by the agencies themselves | PICA, Jamaica Constabulary Force, Jamaica Information Service, US CBP, US ICE, US DHS, US Department of Justice, UK Border Force, UK Home Office, UK National Crime Agency, Canada Border Services Agency, Europol, Frontex, IOM, UNODC, UK Visas and Immigration and EU Migration and Home Affairs. Every release must still match a topic, since most police news is not border-related. |
| **Embassies, high commissions and foreign ministries** (marked **OFFICIAL**, shown under *Official Updates → Embassies & high commissions*) | Releases from diplomatic missions and foreign ministries | **Read directly (feeds):** US Department of State travel advisories (sorted by their title only, because the long advisory text mentions many unrelated topics), UK government news for Jamaica, Barbados, Trinidad and Tobago, the Bahamas, Guyana, Haiti, the Dominican Republic and Belize, UK Foreign Office (FCDO), Global Affairs Canada, the Dominican Republic Foreign Ministry and the Consulate General of Jamaica in Toronto. **Searched through Google News** (most mission websites block automated readers or have no feed, so their own pages are found through a news search of that website): U.S. Embassy Kingston and the US embassies in Barbados, Trinidad and Tobago, the Bahamas, Haiti, the Dominican Republic, Guyana and Belize; Jamaica's Ministry of Foreign Affairs and Foreign Trade; Jamaica's embassy in Washington, high commissions in London and Ottawa and consulates in New York, Miami and Toronto; the Chinese Embassy in Jamaica; the High Commission of India in Kingston; the Canadian High Commission; the EU Delegation; and the Cuban, Nigerian, Venezuelan and Japanese foreign ministries. Results from a mission's own website are marked OFFICIAL. **News about missions:** four extra searches by name ("High Commission" Jamaica, embassies and visas or deportees, Jamaican embassies and consulates abroad, and the Ministry of Foreign Affairs and Foreign Trade) catch news reports about any mission. These are ordinary news, not OFFICIAL. Only border-related releases and reports are kept. A mission that publishes nothing online, or nothing about border topics, will not appear. Add more in `config.yaml`: a feed with `kind: mission`, or a search under `mission_searches`. |
| Google News | Headlines and links | 12 editions: US, UK, Canada and Nigeria (English); Mexico, Colombia and Spain (Spanish); France (French); Brazil (Portuguese); the Netherlands (Dutch, which also covers news from Aruba, Curaçao, Sint Maarten and Suriname); Germany (German); Italy (Italian). About 100 English searches plus searches in the other languages, listed in `config.yaml`. |
| GDELT | A free global news index | Extra coverage. If it is busy, the run skips it and carries on. |
| Extra RSS feeds | Optional | Add any feed in `config.yaml` (`rss_feeds`, or `official_feeds` to mark it official). |
| The full article | Facts in more detail | Opened from the link. Only the facts are kept. |

**Not reachable automatically (checked 26 Nov 2026):**
- INTERPOL and the US Coast Guard block automated readers. INTERPOL news still arrives through Google News and is
  marked official.
- The Jamaica Customs Agency website has a security-certificate error.
- No CARICOM IMPACS news page was found. The CARICOM website has a security-certificate error.
- US embassy websites (Jamaica, Trinidad and Tobago, Barbados, the Bahamas, Haiti, the Dominican Republic and Guyana)
  refuse automated readers. Their news still arrives through Google News.
- The Canadian immigration department (IRCC) news feed returned nothing. The Jamaica Ministry of Foreign Affairs,
  the EU Delegation to Jamaica and the ETIAS site have no readable news feed.

To re-check which sources answer, open the **Actions** tab and run **check-sources**. It changes nothing.

Why official sources matter: the agency's own wording is more reliable than a news summary. The site always reads
them first, so they still arrive on days when Google limits requests. On those days you can also run the daily
workflow with **official_only** ticked.

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
| **Border Integrity** | Corruption and insider facilitation; INTERPOL and watch lists (wanted persons); border security; aviation security; **stowaways** (people hidden on aircraft, ships or containers); terrorism and sanctions |
| **Policy & Systems** | Visa and entry policy; **travel advisories** (for example the US State Department's Level 1 to 4 advisories); border technology (ETIAS, EES, ETAs, e-gates, biometrics); health travel rules |
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
| Publication date | When the article was published. A few official pages show no date; then it says "First seen (the source page shows no date)". |
| Source type | *Official release (agency)* or *News report*. |
| First captured / Last updated | When the site first found the report, and when its record last changed (a new source, a full read or a review). |
| Incident location: countries named, City, Airport, Seaport, Border crossing | The places named in the report (where it happened, or places mentioned). |
| Journey: origin | Where the journey started, only when stated ("from Jamaica"). |
| Transit points, in order | Places passed through, only when stated ("via Panama"). |
| Intended destination | Where the journey was going, only when stated ("bound for Spain"). |
| Interception location | Where it was stopped: the airport, seaport or crossing named, or "intercepted in/at/off X". |
| Route completeness | *Complete* (origin and destination stated), *Partial* (only part stated) or *Not reported*. |
| Source basis | *Explicitly stated in article* (the full article was read) or *Stated in headline or summary*. |
| Journey (summary) | For example "Jamaica → Panama → Spain", or for an incomplete journey "Origin: Jamaica; destination not reported". |
| Nationality (as stated) | Only when the report says it in words, for example "a Jamaican national", "two Venezuelan migrants", "citizens of Haiti". See below. |
| Caribbean connection | What kind of link the report has to the region: origin, destination, transit, occurred in or named, or another explicit link. Otherwise "None identified". |
| Jamaica connection | The specific link to Jamaica: a Jamaican airport or port, a journey that started in or was bound for Jamaica, PICA named, or "named in the report (role not stated)". |
| Transport mode | Air passenger, air cargo, maritime cargo, small vessel, land, or postal / courier. "Mixed" means more than one is stated. |
| Document types | Passport, visa, residence or work permit, ID card, birth certificate and so on. |
| Reporting agency | The agencies named, for example JCF, PICA, CBP, NCA or INTERPOL. |
| Reported outcome | The furthest stage stated: sentenced, acquitted, convicted, charged, arrested, refused entry, seized or intercepted, or investigation ongoing. Updates show "Not applicable". |
| Review status | Automatically collected, Awaiting review, Reviewed or Corrected (section 9). |
| Sources | Every publisher that carried the story, with links and dates. |
| Related events | Up to 3 other reports on the same topic within 90 days that share places, a route or wording. Click one to jump to it. |

**Four different things, kept apart on purpose:**

| | Means | Example |
|---|---|---|
| Incident location | Where it happened | Arrested at Norman Manley airport (Jamaica) |
| Journey origin | Where the journey started | Flight from Jamaica |
| Document issuing country | The country a document claims to be from | A fake Canadian passport |
| Nationality | The person's nationality, as the report states it | A Venezuelan national |

**Nationality rules.** Nationality is useful for analysis and reporting, so it is recorded, but under strict rules:
- It is recorded **only when the report states it in words**, next to a person: "Jamaican woman", "nationals of
  Haiti", "ciudadano venezolano".
- It is **never inferred** from a name, a route, an origin or a document's issuing country.
- "Jamaican police" or "UK student visa" do not count, because the word does not describe a person.
- It is **never used in the review-priority score**. A tested rule checks that the score stays the same with or without it.
- It can be used as a filter (Any nationality) and appears in two charts: *Nationality (as stated)* and
  *Nationality by journey*.
- A pattern in the data is a lead for analysis. It is never a reason to treat an individual traveller differently.

## 6. Specialist fields (shown only for the matching category)

Some categories have extra fields. They appear in the Full record under a "… details" heading, and only for
reports in that category. Each field still shows "Not reported" unless the article states it.

| Category | Extra fields |
|---|---|
| Document fraud | Document type; issuing country of the document; reported fraud method (counterfeit, forged or altered, stolen blank, stolen genuine, fraudulently obtained genuine, impostor, document factory); number of documents; blank versus issued documents; detection stage (check-in, boarding gate, departure or arrival immigration, transit, baggage, application, mail, cargo, at sea, land border, inland) |
| Visa / permit fraud | Visa or permit type; purported issuing authority; reported method (forged visa or stamp, forged approval or letter, fraudulent supporting documents, fake agent or website, bribery, sham marriage) |
| Impostor use | Use of another person's genuine document; detection point; the source's own description of the method |
| Migrant smuggling | Reported origin, transit and destination (also in the journey fields); transport mode; people intercepted; alleged facilitators **by role only** (network, smugglers, boat captain, driver, travel agent, document supplier, corrupt official, safe house); reported fees and currency |
| Human trafficking | Exploitation type; potential or suspected victims and identified or rescued victims, **kept separate as the source states them**; assistance or referral reported; proceedings |
| Citizenship / residence fraud | Programme involved; application stage; alleged misrepresentation; documents involved; administrative or court outcome |
| Border integrity | Organisation or role implicated (only in corruption or insider reports); alleged conduct; location; investigation, disciplinary or criminal outcome |
| Wanted-person interception | Notice or warrant (Red Notice, arrest warrant, extradition request…); agency reporting it; stated basis; reported outcome (arrested, extradited, deported…) |
| Seizure (drugs, firearms, cash, wildlife, cargo incidents) | Substance or item as reported (keeps "suspected"); confirmation status (suspected, field-tested, laboratory-confirmed); quantity and unit as written ("more than 1,100 kg"); standardised quantity (pounds and tonnes to kg, gallons to litres; counts stay counts); quantity qualifier (exact, approximate, more than, up to); concealment method (the words as reported) and **concealment category** (standard list, see below); shipment or transport type (container, baggage, on the body, courier parcel, air cargo, vessel, vehicle, barrel, sea cargo); declared commodity ("declared as bananas"); **cover load / goods used as cover**, with a category; origin, transit and destination; seizing agency; other seized items (firearms, ammunition, cash, kept separate); reported valuation, with who gave the estimate, kept apart from quantity; case development (investigation, arrest, charge, court outcome, correction) |
| Policy update | Issuing authority; affected travellers or documents; announcement date; effective date; exceptions; status (proposed, active, delayed or withdrawn); official guidance link (that country's official immigration site) |

**Concealment and cover loads, recorded the same way every time (for trends).** Every seizure gets up to three
standard **concealment categories** and up to three **cover-load categories**, worked out from the report's own words.
The exact words are kept too, so the category can always be checked.

| Concealment categories | Cover-load categories |
|---|---|
| Swallowed / internal body · Strapped or taped to the body · Clothing or footwear · Luggage: false bottom or lining · Luggage contents · Toiletries, cosmetics or personal items · Electronics or appliances · Inside food or goods · Liquid or impregnated · Courier parcel or mail · Shipping container (structure or rip-on/rip-off) · Cargo cover load · Vehicle hidden compartment · Vessel hull or compartment · Aircraft · Barrel or drum · Furniture, machinery or structures | Fruit and vegetables · Frozen or fresh fish and meat · Coffee, cocoa, sugar or grain · Drinks · Building materials and stone · Scrap, waste and used goods · Machinery, vehicles and parts · Furniture and household goods · Clothing and textiles · Cosmetics and toiletries · Electronics · Chemicals and fertiliser · Charcoal, wood pellets or animal feed · Flowers and plants |

A cover load is only recorded when the goods are named next to a concealment word ("hidden among", "declared as",
"in a shipment of"), so a story that mentions fish somewhere else does not count. An empty category means the report
did not say how it was hidden.

In the **Seizures & Contraband** section: a **Concealment methods** chart, a **Cover loads** chart (click a bar to
filter everything to it) and a **Concealment trends** chart showing seizures per week for the six most common
methods, so a method that starts rising stands out. Both categories are also columns in the CSV downloads.

These fields fill in best when the full article was read. Most older reports were captured from headlines only.
They fill in as articles are re-read, up to 400 per day.

**Seizure totals.** The Seizures & Contraband section on the site shows **one total per substance and unit**, for
example "Cocaine 2.3 t", "Cannabis 340 plants" or "Ammunition 532 rounds". Kilograms, litres, tablets, plants and
counts are **never added together**, and the old single "weight seized" number has been replaced. Totals are as
reported, not verified. They can include approximate figures or totals quoted in background paragraphs, and the
table says when they do.

## 7. Review priority (the score)

> **Review priority = what to read first. It never means a person, country or region is risky.** The site says this under the filter bar, in "About the data" and in every "Why this score".

On the site this is called **Review priority** (it was "High-risk" before). It tells a reviewer what to look at first;
it is not a judgement about any person or country. Only **incidents** are scored, from 0 to 100. **High** means 40 points or more, and **Medium** means 20 or more.
A high score means "worth a closer look", never proof. The score **never** uses nationality (section 5). Click "Why this score"
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
| Nationality | Recorded only when stated in words; never inferred; never scored | Useful for analysis and reporting, but it must not drive risk or be guessed. |
| Headlines | Kept as published (only numbers removed) | They are the publisher's own public words and the link to the source. |
| Full article text | Never stored | Copyright, and the data minimisation principle. |

The filter works by word matching, so it can miss a name or remove a harmless one. If you spot a name that should
not be there, mark the report **excluded** or **corrected** in `reviews.yaml`.

## 8b. Source panel: how reliable is the sourcing?

Every Full record ends with a **source panel**:

| Field | What it shows |
|---|---|
| Publisher and URL | Every site that carried the story, with date, type, role and language. |
| Source type | Official release, court publication, news report, or other (social media or blog). |
| Original or republished | The earliest copy found, or the official release if there is one, is the *original*. Every later copy of the same headline is *republished*. |
| Source language | English, Spanish, French or Portuguese, detected from the text. |
| Supporting sources | How many other sites repeated it. |
| Source relationship | For example "1 independent source; 4 republications of the same report (not counted as separate confirmations)". It also notes when a news report says it is based on an official statement. |
| Review note | What the reviewer checked (from `reviews.yaml`). |
| Uncertainty / conflict note | Automatic notes, such as different quantities stated for the same substance, details the report doesn't state, or a journey only partly stated. A reviewer can add their own. |
| Correction history | Every change: reviewer corrections (field, old value → new value, by whom, when) and the automatic update when the full article was read. |

**Five websites repeating one police release count as one source, not five confirmations.** In the reports table
this shows as "1 independent source + 4 repeats".

**What "Reviewed" means:** a person checked the record against its sources and found it matches them. It does
**not** mean the allegations are proven. People named are suspects unless a court outcome is recorded.

## 9. Reviewing and correcting reports (`reviews.yaml`)

Every report starts as **Automatically collected**. High review-priority reports and those naming Jamaica start as
**Awaiting review**.

To record a review:

1. Open https://github.com/Tiffdaleyo/border-watch-osint/blob/main/reviews.yaml and click the **pencil** icon.
2. Under `reviews:`, add the report's Event ID with one of these statuses:
   - `reviewed`: checked, and it is right.
   - `corrected`: you fixed fields. List them under `corrections:`.
   - `excluded`: off-topic or wrong. It is hidden from the site and the counts, but kept in the data file.
3. You can add a `note` (what you checked), `by` (your initials), `date` (for example 2026-11-27) and
   `uncertainty` (anything missing or contradictory). Corrections appear in the record's correction history.
4. Click **Commit changes**. The site shows the result after the next daily run, or straight away if you run the
   workflow by hand.

Fields you can correct: title, primary_category, categories, event_date, event_date_quality, countries, origin,
transit (a list), destination, interception, nationality (a list), transport_mode, outcome, agencies, summary_text, level.

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

The site is organised into **sections**, like the pages of a website. The **side menu on the left** lists them, with
a count of reports beside each one, and below them the **Investigation tools** (section 10b). On a phone the menu
sits at the top and scrolls sideways.

| Section | What it covers |
|---|---|
| **Overview** | A short summary. It opens on the Caribbean. It shows key numbers (reports collected, reviewed by a person, review priority high, Caribbean, Jamaica, updates, largest seizure total), a "Sections at a glance" panel, the map (it shows where countries are named in the news read, not how much happens there; quiet areas may be ones the site cannot read, see Language coverage), the priority feed, activity over time and the latest developments. Detailed charts are inside each section. |
| **Passports & Documents** | Document & Identity Fraud group |
| **Immigration & Irregular Movement** | Migration & Facilitation group: irregular movements, smuggling, enforcement, deportations |
| **Human Trafficking** | Human trafficking only (kept separate from smuggling) |
| **Citizenship & Residence** | Citizenship policy, citizenship by investment, application fraud |
| **Border Security** | Border Integrity group: watch lists and INTERPOL, aviation security, stowaways, corruption, terrorism |
| **Seizures & Contraband** | Narcotics, firearms, cash, wildlife and cargo seizures worldwide, with totals by substance and unit |
| **Visa & Entry Rules** | Policy & Systems group: visa and entry rules, travel advisories, travel authorisations, border technology, health rules |
| **Official Updates** | Only official releases, with tabs for **Agencies** and **Embassies & high commissions**, plus a "Who published" chart |

A report about several subjects appears in every section it belongs to. For example, a fake passport used by a
smuggling ring appears in both Passports & Documents and Immigration.

**How every section works:**
- A heading and one line saying what the section covers.
- **Quick buttons** for the section's sub-topics, with counts. For example, Seizures has Drug trafficking, Firearms,
  Cash couriers, Wildlife and Cargo.
- Only the charts that matter for that subject. Seizures shows the seizure totals, transport mode and airports;
  Visa & Entry Rules shows the policy feed.
- **⬇ Download this view (CSV)** saves exactly what is on screen, after every filter, as a spreadsheet that opens in
  Excel. **⬇ JSON** gives the same reports for analysts. The file name says the section, the topic and the date.
- **🔗 Copy link** copies a link straight to the section, for example `…/border-watch-osint/#seizures`. Bookmark it or
  send it to the team.

**Section links:** `#overview`, `#documents`, `#migration`, `#trafficking`, `#citizenship`, `#border`, `#seizures`,
`#policy`, `#official`. A link ending in an Event ID (for example `#BWO-2026-0123`) still opens that report.

**Everywhere on the site:**
- **Light or dark:** the site opens in a light theme. The **☾ Dark** button at the top right switches to dark (and
  **☀ Light** switches back). Each computer or phone remembers its own choice.
- **Any selector box (top):** type or paste anything: a word, a name, an email, a phone number, a flight number, an
  IMO ship number, a container number, a port code, a website or an Event ID. The site searches its own reports at
  once and says what kind of selector it detected. A port code (e.g. JMKIN) opens in **Port lookup**. A flight number
  opens in the **Flight tracker**. IMO and MMSI ship numbers are recognised, because they appear in seizure and
  stowaway news, but the site has no ship-tracking tool and no link to one.
  The "Try" examples show the idea.
- **Filter bar:** choose the period, the scope (World, Caribbean or Jamaica), topic, country, nationality, transport
  mode, news vs official releases, review status, or incidents and updates. Every chart, list and number follows the filters, and the filters stay on when you change section.
  Click any bar or map bubble to filter by it. **Reset** clears the filters but keeps you in the section.
- **Key numbers (clickable):** reports collected, reviewed by a person, review priority high, Caribbean, Jamaica, policy updates and the largest
  seizure total, compared with the previous period. Click a card to open its list: **Reports** jumps to the table;
  **Review priority: high**, **Caribbean**, **Jamaica** and **Policy & other updates** filter to just those reports (click again
  to remove); **Largest seizure total** opens the Seizures section.
- **"Filters on" line:** every filter that is switched on is listed under the section heading, each with a ✕ to
  remove it, plus **Clear all**. If a section shows fewer reports than you expect, look here first. A link from an
  alert email opens one report by its Event ID; opening any section from the menu clears that search.
- **Map:** countries named. A red pulse means the country has high review-priority incidents.
- **Reported journeys map:** distinct markers for origin (●), transit (◆), intended destination (▲) and interception
  (📍). A line shows a connection the report states between two places. **It is not an actual flight or sailing
  path.** Line width = number of reports. Next to it, the **Journeys** list shows incomplete journeys as, for
  example, "Origin: Jamaica; destination not reported".
- **Nationality (as stated)** and **Nationality by journey:** see the nationality rules in section 5.
- **Priority feed:** high review-priority incidents and anything naming Jamaica.
- **Seizures section extras:** reports over time by drug, top corridors, hotspots, a concealment × drug table,
  insider signals (with % cards), concealment trends and cover loads.
- **Trend lookup** (Immigration, Trafficking, Passports): research a route (origin → destination) with
  live news-index results and ready-made searches.
- **All reports:** a sortable table. Click **Full record** for every field, including specialist fields. Click
  **Why this score** to see the indicators matched.
- **Full downloads:** the complete CSV (every report, every field) and the **weekly bulletin** are linked above the
  table.

## 10b. Tools (side menu)

All tools are part of this site and use only the collected news and public reference lists.

| Tool | What it does |
|---|---|
| **Travel document check** | Type or paste the machine-readable zone (MRZ) of a passport, ID card or visa. The page reads every field and checks it against the ICAO Doc 9303 rules: check digits, real dates, known country codes and layout. It flags an expired or nearly expired document, a minor, an issuing state that differs from the nationality, a possibly truncated name and specimen documents, and lists what to check next. It works only in the browser and nothing typed is saved or sent. A passing check only means the MRZ is consistent, because forgers can calculate check digits too |
| **Visa requirements** | Passport to destination: visa free (with days), eTA, e-Visa, visa on arrival, visa required or no admission. It also shows "who needs a visa to enter…" (for example Jamaica) and "where can this passport go…". The data is the public Passport Index dataset as of 12 Jan 2025, so it may be out of date. Always confirm with the official immigration authority |
| **Flight tracker** | Type a flight number (BW2591), a callsign (BWA2591) or an airport code (KIN, MKJP). It shows the airline, the radio callsign, the live position from the free ADS-B network (adsb.lol) when the aircraft is airborne and in range, the published route on a map, and links to the flight's history. For an airport it shows the details and links to live traffic and arrival and departure boards. Only the flight number is sent to adsb.lol |
| **Suspect profile** | Build a one-page profile of a person of interest: names and other spellings, date of birth (a minor is flagged), nationality as stated on the document, role in the case, and each identifier (document, phone, email, username, website, address, company, vehicle) with where it came from and whether it is confirmed. It then offers ready-made open-source searches for each item: green buttons search this site's reports; the others open outside websites (Google, social media, sanctions lists, company registers, domain records). Print or save it as PDF, or copy it as text. Nothing typed is saved or sent, but clicking an outside search sends the search words to that website |
| **Case summary** | Turn the facts of an airport case into a one-page summary for a supervisor, a referral or a hand-over: place (KIN, MBJ, OCJ), case type, flight and route, people and their roles, what happened, documents examined, the indicators observed (the tick list changes with the case type: suspected impostor, fraudulent or altered document, possible trafficking victim, irregular migrant or refused entry), action taken and next steps. Print or save it as PDF, or copy it as text. Nothing typed is saved or sent. It does not replace official forms |
| **Case playbooks** | Step-by-step checklists for four airport cases: suspected impostor, fraudulent document, possible trafficking victim, and irregular migrant or refused entry. Each one covers what to look for, first steps at the desk, what to check (with buttons to the right tool on this site), how to refer and record, and what to avoid. **Start a case summary** opens the Case summary with the case type already chosen. Each playbook prints on its own. It is a memory aid drawn from public guidance (ICAO, IOM, UNODC, OSCE): agency procedures and the law come first |
| **Port lookup** | Type a port name or UN/LOCODE (e.g. Kingston or JMKIN). It shows the reports and seizures linked to that port, with the substances and hiding methods. It covers 179 world ports and uses every date, not only the chosen period |
| **Route lookup** | Research a journey from one country to another (the Trend lookup) |
| **Repeat links** | The same route, cover cargo, hiding method, port, document type, container, vessel or flight showing up in separate cases. These are **leads to check, not proof** |
| **Language coverage** | A map of where the site can and cannot see. Green means reports were found. Light green means reports were found, but only through other languages. Yellow means the main language is searched but nothing was found. Red means a **blind spot**: the main language is not searched yet. Languages searched: English, Spanish, French, Portuguese, Dutch, German and Italian |
| **Any-selector search** | Jumps to the search box at the top |

**Good to know:** don't type case details into outside websites (for example Flightradar24). Follow your agency's
rules for online enquiries.

## 10c. "What this suggests"

Each section opens with a short written analysis, worked out from the reports in the current view. It covers:

- **Seizures:** concealment, cover loads and routes, transport, hotspots, insider signals, and rising methods or substances.
- **Passports & Documents:** document types, fraud methods, where fraud was caught, and claimed issuing countries.
- **Immigration:** routes, transport, interception countries, facilitators and fees.
- **Trafficking:** exploitation types, routes and victim support.
- **Visa & Entry Rules and Citizenship:** whether rules are tightening or easing, and the countries in the news.
- **Border Security:** insider risk, main topics and airports.

"Rising" appears only once four weeks have been collected. Every point is a pattern to look into, not a finding.
Small numbers are marked as early signals.

## 10d. Weekly bulletin (web page)

The blue **📰 Weekly bulletin** button at the top of the site opens a one-page summary of the last 7 days. It has:

- key numbers;
- **Highlights** written from the week's counts (main topics, how seizures were hidden, routes, insider signals,
  Jamaica, and what is rising);
- unverified seizure totals;
- the top incidents to review;
- Caribbean and Jamaica;
- policy and entry rules;
- watch list hits.

**Past weeks:** each finished week (Monday to Sunday) has its own page, linked at the bottom and under
**All bulletins**. The last 26 weeks are kept. Pages are rebuilt every day, so a late report or a correction also
updates past weeks.

It also has **charts** (reports per day by group, main groups, countries, review priority, seizures by substance and
by hiding method, transport, routes) and a written **Analysis** for each area: seizures, documents, irregular
movement, trafficking, visa and entry rules, and border integrity.

**Print / save as PDF** gives a clean printout of 2 to 3 pages: the menus are left out. The weekly email uses the
same page (section 2b).

## 11. Email: Monday bulletin and alerts

**What the team receives:**
- **Weekly bulletin:** a one-page PDF covering the 7 days up to Monday: key numbers, top incidents, Caribbean and
  Jamaica, policy, and watch-list hits. A draft goes to the reviewer at 7:00 AM Jamaica time on Monday, and the team
  receives it once the reviewer presses **Send bulletin** (section 2b). The sent PDF is saved as `docs/bulletin.pdf`.
  The website's "Weekly bulletin" page shows the latest 7 days and updates every day.
- **Alerts:** one email after each daily run (about **6:30 AM Jamaica time**). It lists every **new** incident that
  is High risk or linked to Jamaica, each with a link to its full record. No new incidents means no email, and a
  report is never alerted twice. Alerts come once a day, when the daily run finishes. They can't be truly instant,
  because the site only collects news once a day. Only stories dated within the **last 7 days** are emailed; an
  older story found for the first time still goes on the site, but not in the alert. One email shows at most 25.

**Who receives them:** the list is stored privately as a GitHub "secret", not in the public files. Team members are
put in Bcc, so they don't see each other's addresses.

**One-time setup (about 15 minutes):**
1. **Create a sending Gmail account** just for the site, for example `borderwatch.yourteam@gmail.com`. Don't use a
   work or personal account.
2. **Turn on 2-Step Verification** for that account: Google Account, then Security, then 2-Step Verification. Gmail
   requires it before you can make an app password.
3. **Create an app password:** go to https://myaccount.google.com/apppasswords, type a name such as "Border Watch",
   then click Create. Copy the 16-letter password it shows.
4. **Add the secrets to GitHub.** Open the repository, then Settings, then Secrets and variables, then Actions, then
   **New repository secret**. Add each of these:

   | Name | Value |
   |---|---|
   | `MAIL_USERNAME` | the Gmail address from step 1 |
   | `MAIL_PASSWORD` | the 16-letter app password from step 3 (no spaces) |
   | `MAIL_TO` | who gets the weekly bulletin, separated by commas: `a@example.com, b@example.com` |
   | `MAIL_ALERTS_TO` | optional: who gets alerts, if different (otherwise `MAIL_TO` is used) |

5. **Send a test:** open Actions, then **weekly-bulletin**, then **Run workflow**. Everyone in `MAIL_TO` should get
   the PDF within 2 minutes. If nothing arrives, open that run's log. It says what went wrong, for example a wrong
   password.
6. **Test the alert email:** open Actions, then **test-email**, then **Run workflow**. It sends one alert email,
   marked **[TEST]**, with the 3 most recent high review-priority or Jamaica-linked reports. It does not mark anything as
   alerted, so the real daily alerts are unaffected.

To add or remove people later, edit the `MAIL_TO` secret. Until the secrets exist, the site works normally and
simply sends nothing.

**Note:** alerts and the bulletin come from public news and are leads to verify. Don't reply to them with case
details.

## 11b. Data quality rules

- **Money is never a count.** "11,500 riyal work visa", "€22,000 for fake passports" and "$21,000 per person" are
  sums of money, so they are not counted as documents or people. Weapon models ("AK-47", "M-16", "Glock 19") are not
  counted as firearms.
- **Repeat coverage is one event.** When several outlets report the same case within 4 days (same kind of event,
  same numbers, same countries, several distinctive headline words in common), the earliest report keeps its
  Event ID and the others become extra sources. Their old Event IDs still find it in the search box. Cases reported
  in two languages are not always matched; report any you spot to the site administrator.
- **Charged is not convicted.** Phrases like "if convicted" or "faces up to 10 years" are ignored. If the headline
  says charged or arrested but the article text says convicted or sentenced, the headline's stage is shown and the
  report is marked **Awaiting review** with the note "Outcome needs checking".
- **A court's travel ban on one person is not an entry rule.** Bail conditions or a politician barred from leaving
  their country are no longer filed under Visa and entry rules. Bans on nationals of whole countries still are.
- **Comparisons need history.** The "vs previous 90 days" line only shows when collection covered the whole earlier
  period. Until then the cards say **Insufficient comparison history**.
- **Seizure totals are unverified.** For each report, one figure per substance is added: the headline figure if there
  is one, otherwise the first figure that is not background. Background means yearly totals, earlier cases, whole
  operations or "since January" figures. The same large figure reported again within 30 days (other languages,
  follow-ups) counts once. Archived pages add nothing. The totals are indications, never official statistics.
- **Reviewed vs collected.** The "Reviewed by a person" card counts events marked reviewed or corrected in
  `reviews.yaml`. Everything else is collected automatically and should be treated as a lead.

## 12. Known limits

- It works by **word matching, not AI**. Expect some off-topic items and some misses. Use `excluded`, and report to the
  site administrator which words cause trouble.
- **Weights and seizure totals** follow the rules in section 11b. Some background figures can still slip through.
- **Event dates, transport mode, outcomes and specialist fields** depend on the full article. Paywalled or blocked
  sites cannot be read, so those reports show more "Not reported".
- **Google News and GDELT** sometimes limit requests. On a busy day, some searches are skipped and caught up the
  next day.
- The **Trend lookup** live results depend on GDELT being reachable from your browser.
- The site shows the last **180 days**. Older data stays in `data/events.json`.

## 13. Changing settings

Everything adjustable is in `config.yaml`. Edit it on GitHub with the pencil icon, then commit.

| To change | Where |
|---|---|
| Search words | `sources: google_news: queries:` (per language) and `sources: gdelt: queries:` |
| News editions | `sources: google_news: editions:` |
| Official sources | `sources: official_feeds:` (and `official_publishers:`) |
| Add any RSS feed | `sources: rss_feeds:` |
| Email recipients | GitHub secrets `MAIL_TO` and `MAIL_ALERTS_TO` (never in the files) |
| Home country and region | `site: home_country`, `home_places`, `region_countries` |
| Risk points and bands | `risk: indicators:`, `risk: bands:` |
| Watch list | `risk: watchlist:` |
| How far back to search / show | `run: lookback_days`, `run: report_days` |
| Full-article reading | `run: read_full_articles`, `read_limit`, `read_budget_minutes` |

Topic words and the seven groups are in `watch/extract.py`. Specialist-field words are in `watch/specialist.py`.
Privacy rules are in `watch/privacy.py`.

## 14. Files at a glance

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
| `watch/journey.py` | Structured journeys and stated nationality |
| `watch/mailer.py`, `watch/alerts.py`, `tools/send_weekly.py` | Email: alerts and the Monday PDF |
| `.github/workflows/weekly-bulletin.yml` | Sends the Monday bulletin |
| `.github/workflows/test-email.yml`, `tools/test_alert.py` | Sends a [TEST] alert email on demand |
| `.github/workflows/check-sources.yml`, `tools/check_sources.py` | Checks which official sources answer |
| `watch/analyze.py` | Review-priority score and trends |
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
| 2026-11-26 | Structured journeys (origin, transit points in order, intended destination, interception location, route completeness, source basis), with a journey map using distinct markers. Incomplete journeys are shown as "Origin: X; destination not reported". Nationality is now recorded when stated in words (never inferred, never scored), with a filter and two charts. |
| 2026-11-26 | Official press releases added as sources (PICA, JCF, JIS, CBP, ICE, DHS, DOJ, UK Border Force, Home Office, NCA, CBSA, Europol, Frontex, IOM, UNODC), read first and marked OFFICIAL, with a filter. A Monday one-page PDF bulletin by email and daily alert emails for new high-risk or Jamaica-linked incidents (ready; they start once the email secrets are added). Articles that fail to load are now retried instead of skipped. |
| 2026-11-26 | Seizure fields (substance, confirmation, quantity and unit, standardised quantity, qualifier, concealment, shipment type, declared commodity, route, agency, other items, valuation, case development). Seizure totals now shown per substance and unit, never combined. |
| 2026-11-26 | Source panel on every record: source type, original or republished, language, supporting sources, independent vs repeated reporting, review note, uncertainty / conflict note, correction history. "Reviewed" defined as checked against sources, not proven. |
| 2026-11-26 | Email switched on. Test bulletin sent successfully. A **test-email** button added to send a [TEST] alert email on demand. |
| 2026-11-26 | Alerts limited to stories dated within the last 7 days, after the first live alert listed 145 incidents from the backlog. |
| 2026-11-26 | Site organised into **sections** (Overview, Passports & Documents, Immigration & Irregular Movement, Human Trafficking, Citizenship & Residence, Border Security, Seizures & Contraband, Visa & Entry Rules, Official Updates), each with its own link, quick sub-topic buttons, relevant charts and a download of the current view. New **Stowaways** and **Travel advisories** topics. Embassy, high commission and foreign-ministry sources added. Fixed: English figures such as "13.795 kg" were read as 13,795 kg. |
| 2026-11-26 | Key-number cards are clickable. A "Filters on" line shows every active filter with a ✕. An Event ID search from an alert link now clears when you open a section. |
| 2026-11-26 | Light theme by default, with a Light / Dark button that each device remembers. |
| 2026-11-26 | Side menu on the left. Big **Any selector** box that searches the reports, detects the selector type. |
| 2026-11-27 | Concealment and cover loads recorded in standard categories on every seizure, with charts, filters and a weekly concealment trend in the Seizures section, and columns in the CSV. |
| 2026-11-27 | Data-quality fixes: money and weapon models no longer read as counts; repeat coverage grouped into one event (about 730 repeats merged); charged vs convicted conflicts flagged; personal court travel bans out of policy; "Insufficient comparison history"; seizure totals audited and labelled unverified (cocaine fell from 354 t to about 70 t). |
| 2026-11-27 | Presentation: the site opens on the Caribbean (World and Jamaica one click away); "High-risk" renamed "Review priority"; shorter Overview (key numbers, map, priority feed, latest developments, section tiles), with detailed charts inside each section; new "Reviewed by a person" card next to "Reports collected". |
| 2026-11-27 | Seizure charts (by drug over time, corridors, hotspots, concealment × drug, insider signals with %), Port lookup (name or UN/LOCODE), Repeat links table, Language coverage map, "What this suggests" analysis in every section. Dutch, German and Italian news searched. The side menu lists the site's own tools only (links to outside investigation tools removed). |
| 2026-11-27 | **Weekly bulletin** button in the site heading: a web page for the last 7 days with highlights, plus a page for every past week and an "All bulletins" list. It prints cleanly on A4. |
| 2026-11-27 | Bulletin now has charts and a written analysis for each area. **Review before publishing:** the daily run makes a draft emailed to the reviewer; the live site, alerts and the team bulletin wait for the reviewer's Publish / Send bulletin (section 2b). |
| 2026-11-27 | The daily run starts earlier (about 05:15 Jamaica time), with back-up start times at 07:15 and 10:15 in case GitHub delays it. |
| 2026-11-27 | New tools in the side menu: **Travel document check** (MRZ reader and ICAO checks), **Visa requirements** (passport to destination, who needs a visa for Jamaica) and **Flight tracker** (airline and callsign decoding, live position, route, airport details). Flight numbers typed in the search box open in the Flight tracker. |
| 2026-11-27 | New tools in the side menu: **Suspect profile** (one-page profile with open-source searches for each identifier) and **Case summary** (one-page airport case summary with indicator tick lists). Both work only in the browser. |
| 2026-11-27 | New tool: **Case playbooks** for four airport case types, linked to the other tools and to the Case summary. |
| 2026-11-27 | Wider embassy and high commission coverage: 2 new feeds, plus Google News searches of the websites of 23 embassies, high commissions, consulates and foreign ministries (including Jamaica's own missions abroad) and 4 searches for news about missions. |
| 2026-11-27 | **Automatic publishing restored:** the daily run updates the site and sends alerts straight away. Only reports recorded in `reviews.yaml` carry the **Reviewed** mark; the rest show as Automatically collected or Awaiting review (section 2b). |
| 2026-11-27 | **Weekly bulletin checked before sending:** the Monday bulletin is a draft for the reviewer; the team receives it after **Send bulletin**. Daily reports still go live automatically (section 2b). |
| 2026-11-27 | The site now states plainly: "Review priority = what to read first. It never means a person, country or region is risky." |
| 2026-11-27 | No ship tracking: the outside ship-position link was removed from the search box. IMO and MMSI numbers are still recognised in reports and Repeat links. The ship example in "Try" was replaced with a flight number. |
| 2026-11-27 | The "Where it is happening" map now carries a caution: it shows where countries are named in the news read, not how much happens there; quiet areas may be ones the site cannot read (see Language coverage). |
| 2026-11-27 | Charts over time start on the first day the site collected reports (26 Oct 2026), not at the start of the chosen period, so weeks before collection no longer look like "no reports". |
| 2026-11-27 | The site explains how "rising" is decided: under every "What this suggests" (at least 3 reports in the last 14 days and more than double the 14 days before, shown once 4 weeks are collected), under the "this week compared with usual" table and in the bulletin (at least 3 reports in the last 7 days and at least double the average week of the 4 weeks before). |
| 2026-11-28 | Fixed chart labels being cut off at the left edge (for example "Document & Identity Fraud" in Review priority by main group): charts now measure labels in the page's own font and keep a wider margin. Very long labels are shortened with "…"; the full name shows on hover. |
| 2026-11-28 | "Update" is explained on the site: "Update = news with no specific crime (new visa rule, travel advisory, deportation flight, border system); not scored." It appears under the Review priority by main group chart, on the priority filter and Update badges (on hover), and in About the data. |
