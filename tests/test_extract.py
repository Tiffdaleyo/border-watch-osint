"""Quick checks that the fact-finding works. Run with:  python -m pytest tests"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from watch.extract import extract  # noqa: E402


def test_off_topic_is_dropped():
    assert extract({"title": "Jamaica wins gold in the 100 metres"}) is None


def test_passport_fraud_with_count_and_airport():
    f = extract({"title": "Police seize 45 fake Canadian passports at Norman Manley airport"})
    assert "Passport fraud" in f["categories"]
    assert f["documents_count"] == 45
    assert "Jamaica" in f["countries"]
    assert any("Norman Manley" in a for a in f["airports"])


def test_spanish_headline_and_route():
    f = extract({"title": "Detenidos tres hombres con pasaportes falsos con destino a España"})
    assert "Passport fraud" in f["categories"]
    assert f["people_count"] == 3
    assert f["destination"] == "Spain"


def test_route_from_to():
    f = extract({"title": "Human trafficking victims moved from Venezuela to Trinidad and Tobago"})
    assert (f["origin"], f["destination"]) == ("Venezuela", "Trinidad and Tobago")


def test_nationality_word_is_not_a_country():
    f = extract({"title": "Forged passport found on traveller, Jamaican police say"})
    assert "Jamaica" not in f["countries"]


def test_year_is_not_a_count():
    f = extract({"title": "In 2026 police seized fake passports"})
    assert f["documents_count"] == 0


def test_policy_news_is_an_update():
    f = extract({"title": "UK announces new visa requirement for travellers from Colombia"})
    assert "Visa and entry policy" in f["categories"]
    assert f["kind"] == "Update"


def test_interpol_arrest_is_an_incident():
    f = extract({"title": "Interpol red notice suspect arrested at Sangster airport"})
    assert "INTERPOL and watch lists" in f["categories"]
    assert f["kind"] == "Incident"


def test_spanish_sports_is_not_deportation():
    assert extract({"title": "Noticias de deportes: Jamaica gana"}) is None


def test_drug_courier_at_airport():
    f = extract({"title": "Passenger arrested at Norman Manley airport with 3 kg of cocaine in suitcase"})
    assert "Drug trafficking" in f["categories"] and f["kind"] == "Incident"
    assert f["weight_kg"] == 3


def test_street_drug_story_without_border_angle_is_dropped():
    assert extract({"title": "Police arrest man with cocaine in Manchester flat"}) is None


def test_firearms_in_cargo():
    f = extract({"title": "Customs seize firearms hidden in barrel shipment at Kingston Wharves"})
    assert {"Firearms and ammunition", "Cargo operations"} <= set(f["categories"])
    assert "Jamaica" in f["countries"]


def test_tonnes_converted_to_kg():
    f = extract({"title": "1.2 tonnes of cocaine found in container at port"})
    assert f["weight_kg"] == 1200


def test_health_travel_rule_is_update():
    f = extract({"title": "New entry requirements: airport health screening after outbreak"})
    assert "Health travel rules" in f["categories"] and f["kind"] == "Update"


def test_sports_watch_list_is_not_border_news():
    assert extract({"title": "Star guard named to preseason award watch list"}) is None


def test_article_facts_and_merge():
    from watch import fulltext
    from watch.extract import compile_words
    ev = {"title": "Passenger held at Norman Manley airport", "summary": "", "categories": ["Drug trafficking"],
          "countries": ["Jamaica"], "airports": [], "document_types": [], "kind": "Incident"}
    text = ("Police at Norman Manley International Airport arrested a passenger bound for London after he swallowed "
            "pellets containing 2 kg of cocaine. Jamaica Customs and the JCF said he was charged and later sentenced "
            "to 3 years in prison. ") * 3
    a = fulltext.article_facts(ev, text, [compile_words(["swallowed", "pellets"])], {"Jamaica"})
    assert a["weight_kg"] == 2 and "swallowed" in a["terms"]
    assert a["outcome"] == "Sentenced" and a["sentence"] == "3 years"
    assert "Jamaica Customs" in a["agencies"]
    ev["article"] = a
    fulltext.apply_article(ev)
    assert ev["weight_kg"] == 2 and ev.get("destination") == "United Kingdom" and ev["lead"]


# ---- full event record ----------------------------------------------------------------------
from watch import extract as X, record  # noqa: E402


def test_transport_mode():
    assert record.transport_mode("Passenger arrested with cocaine in suitcase at Norman Manley") == "Air passenger"
    assert record.transport_mode("Guns found in barrel shipped to Kingston Wharves") == "Maritime cargo"
    assert record.transport_mode("Police held a meeting") == ""


def test_event_date_only_from_text():
    assert record.event_date("Officers seized the drugs on November 20 at the airport", "2026-11-24") == ("2026-11-20", "exact")
    assert record.event_date("The suspect was arrested on Monday", "2026-11-26")[1] == "approximate"
    assert record.event_date("Passports seized at airport", "2026-11-24") == ("", "unknown")


def test_assign_ids_permanent():
    evs = [{"id": "a", "date": "2026-11-01", "first_seen": "2026-11-01"}, {"id": "b", "date": "2026-11-02", "first_seen": "2026-11-02"}]
    record.assign_ids(evs)
    assert [e["event_id"] for e in evs] == ["BWO-2026-0001", "BWO-2026-0002"]
    evs.append({"id": "c", "date": "2026-11-03", "first_seen": "2026-11-03"})
    record.assign_ids(evs)
    assert evs[0]["event_id"] == "BWO-2026-0001" and evs[2]["event_id"] == "BWO-2026-0003"


def test_review_status_and_corrections():
    ev = {"event_id": "BWO-2026-0001", "categories": ["Passport fraud"], "level": "Low"}
    record.apply_review(ev, {})
    assert ev["review_status"] == "Automatically collected"
    record.apply_review(ev, {"BWO-2026-0001": {"status": "reviewed", "corrections": {"destination": "Canada"}}})
    assert ev["review_status"] == "Corrected" and ev["destination"] == "Canada"


def test_trafficking_and_smuggling_kept_separate():
    sm = X.extract({"title": "Police dismantle migrant smuggling ring at border"})
    assert "Migrant smuggling" in sm["categories"] and "Human trafficking" not in sm["categories"]
    ht = X.extract({"title": "Human trafficking victims rescued from forced labour farm"})
    assert "Human trafficking" in ht["categories"] and "Migrant smuggling" not in ht["categories"]
    assert record.exploitation("victims of forced labour were rescued") == ["Forced labour"]


def test_groups():
    assert X.groups_of(["Passport fraud", "Drug trafficking"]) == ["Document & Identity Fraud", "Seizures & Contraband"]
    assert all(t in X.TOPIC_GROUP for t in X.CATEGORIES)


def test_jamaica_connection_role():
    site = {"region_countries": ["Jamaica", "Haiti"], "home_country": "Jamaica", "home_places": ["Kingston"]}
    ev = {"title": "Woman held at Norman Manley with cocaine bound for London", "countries": ["Jamaica", "United Kingdom"],
          "origin": "Jamaica", "destination": "United Kingdom", "airports": ["Norman Manley (KIN)"]}
    car, jm = record.connections(ev, site)
    assert car == ["Origin (Jamaica)"] and any("airport" in j for j in jm)


# ---- specialist fields and privacy ----------------------------------------------------------
from watch import privacy, specialist  # noqa: E402


def _sec(ev, text):
    return {name: dict(rows) for name, rows in specialist.sections(ev, text)}


def test_specialist_only_for_matching_category():
    ev = {"categories": ["Drug trafficking"], "kind": "Incident"}
    assert _sec(ev, "Cocaine seized at the port") == {}


def test_document_fraud_fields():
    ev = {"categories": ["Passport fraud"], "kind": "Incident", "document_types": ["Passport"], "documents_count": 12}
    s = _sec(ev, "Officers seized 12 fake Canadian passports and blank booklets from a passenger at check-in")["Document fraud"]
    assert s["Issuing country of the document"] == "Canada"
    assert "Blank" in s["Blank versus issued documents"] and s["Detection stage"].startswith("At check-in")
    assert s["Number of documents"] == "12"


def test_smuggling_fees_and_transit():
    ev = {"categories": ["Migrant smuggling"], "kind": "Incident"}
    s = _sec(ev, "Migrants travelled via Panama and each paid $5,000 to smugglers")["Migrant smuggling"]
    assert s["Reported transit"] == "Panama" and "$5,000" in s["Reported fees and currency"]
    assert "Smugglers / guides" in s["Alleged facilitators (role)"]


def test_trafficking_victims_kept_apart():
    ev = {"categories": ["Human trafficking"], "kind": "Incident"}
    s = _sec(ev, "Police identified 12 potential victims; 4 victims were rescued and referred to a shelter")["Human trafficking"]
    assert "12" in s["Potential / suspected victims (as stated)"] and "4" in s["Identified / rescued victims (as stated)"]
    assert s["Assistance or referral reported"] == "Reported"


def test_policy_fields():
    ev = {"categories": ["Visa and entry policy"], "kind": "Update", "date": "2026-11-20", "countries": ["United Kingdom"]}
    s = _sec(ev, "The Home Office said the new visa requirement takes effect from January 5, 2027 for nationals of Jamaica")["Policy update"]
    assert s["Issuing authority"] == "Home Office" and "January 5, 2027" in s["Effective date"]
    assert s["Status"] == "Active / in force" and "gov.uk" in s["Official guidance link"]


def test_privacy():
    t = privacy.scrub("He showed passport number A1234567. The victim, Jane Doe, was 16.")
    assert "A1234567" not in t and "Jane Doe" not in t
    ht = privacy.scrub("Police rescued Maria Lopez, 17. Suspect John Brown was charged.", trafficking=True)
    assert "Maria Lopez" not in ht and "John Brown" in ht
    ev = {"title": "Trafficking Victims Rescued In Kingston", "summary": "Trafficking Victims Rescued In Kingston  Gleaner",
          "categories": ["Human trafficking"]}
    privacy.apply(ev)
    assert ev["summary"].startswith("Trafficking Victims Rescued In Kingston")


# ---- journeys and stated nationality --------------------------------------------------------
from watch import journey  # noqa: E402


def test_journey_structure():
    ev = {"origin": "Jamaica", "destination": "Spain", "kind": "Incident"}
    j = journey.build(ev, "travelled from Jamaica via Panama to Spain and was intercepted in Panama", True)
    assert j["transit"] == ["Panama"] and j["interception"] == "Panama" and j["completeness"] == "Complete"
    assert j["basis"] == "Explicitly stated in article"
    assert journey.describe(j) == "Jamaica → Panama → Spain"
    assert journey.describe({"origin": "Jamaica"}) == "Origin: Jamaica; destination not reported"


def test_nationality_only_when_stated():
    assert journey.nationalities("Two Venezuelan nationals and a Jamaican woman were held") == ["Venezuela", "Jamaica"]
    assert journey.nationalities("Jamaican police seized cocaine") == []          # an agency, not a person
    assert journey.nationalities("UK student visa rules change") == []             # a visa, not a person
    assert journey.nationalities("Capturan a ciudadano venezolano") == ["Venezuela"]


def test_nationality_not_in_score():
    from watch import analyze
    ev = {"title": "Jamaican man arrested", "summary": "", "categories": ["Passport fraud"], "kind": "Incident",
          "countries": [], "nationality": ["Jamaica"]}
    a = dict(ev)
    analyze.score_event(a, {"indicators": {}, "bands": {"high": 40, "medium": 20}}, [], [], [])
    b = dict(ev, nationality=[])
    analyze.score_event(b, {"indicators": {}, "bands": {"high": 40, "medium": 20}}, [], [], [])
    assert a["score"] == b["score"]


# ---- email alerts ---------------------------------------------------------------------------
from watch import alerts, mailer  # noqa: E402


def test_alert_pick_and_send(monkeypatch):
    evs = [{"event_id": "BWO-2026-0001", "first_seen": "2026-11-26", "kind": "Incident", "level": "High", "score": 45,
            "title": "Fake passports seized", "url": "https://example.org/a"},
           {"event_id": "BWO-2026-0002", "first_seen": "2026-11-26", "kind": "Incident", "level": "Low", "home": True,
            "title": "Jamaica arrest", "url": "https://example.org/b"},
           {"event_id": "BWO-2026-0003", "first_seen": "2026-11-26", "kind": "Update", "level": "Update", "home": True,
            "title": "Visa rule", "url": "https://example.org/c"},
           {"event_id": "BWO-2026-0004", "first_seen": "2026-11-25", "kind": "Incident", "level": "High",
            "title": "Not sent yesterday", "url": "https://example.org/d"},
           {"event_id": "BWO-2026-0005", "first_seen": "2026-11-10", "kind": "Incident", "level": "High",
            "title": "Too old", "url": "https://example.org/e"}]
    # unsent alerts roll over for up to 7 days
    assert [e["event_id"] for e in alerts.pick(evs, "2026-11-26", "Jamaica")] == ["BWO-2026-0001", "BWO-2026-0002", "BWO-2026-0004"]
    sent = []

    class FakeSMTP:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def login(self, u, p): sent.append(("login", u))
        def send_message(self, m): sent.append(("msg", m["Bcc"], m["Subject"]))

    monkeypatch.setattr(mailer.smtplib, "SMTP_SSL", FakeSMTP)
    monkeypatch.setenv("MAIL_USERNAME", "sender@example.org")
    monkeypatch.setenv("MAIL_PASSWORD", "x")
    monkeypatch.setenv("MAIL_TO", "a@example.org, b@example.org")
    monkeypatch.setenv("MAIL_REVIEW_TO", "reviewer@example.org")
    # the morning draft goes to the reviewer only and marks nothing as sent
    assert alerts.send(evs, "2026-11-26", {"home_country": "Jamaica", "url": "https://x/"}, draft=True) == 3
    assert sent[1][1] == "reviewer@example.org" and sent[1][2].startswith("DRAFT") and not evs[0].get("alerted")
    # an excluded report is left out when the reviewer sends
    evs[1]["review_status"] = "Excluded"
    assert alerts.send(evs, "2026-11-26", {"home_country": "Jamaica", "url": "https://x/"}) == 2
    assert sent[3][1] == "a@example.org, b@example.org" and evs[0]["alerted"] and evs[3]["alerted"] and not evs[1].get("alerted")
    assert alerts.pick(evs, "2026-11-26", "Jamaica") == []          # never alerted twice


def test_no_email_without_secrets(monkeypatch):
    for k in ("MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_TO", "MAIL_ALERTS_TO"):
        monkeypatch.delenv(k, raising=False)
    assert mailer.send("s", "<p>h</p>", "t") is False


# ---- seizures and source panel --------------------------------------------------------------
from watch import seizure, sources  # noqa: E402


def test_seizure_units_never_combined():
    qs = seizure.quantities("Police seized more than 25 pounds of suspected marijuana, 40 cannabis plants and 2 litres of liquid cocaine")
    by = {(q["substance"], q["std_unit"]): q for q in qs}
    assert by[("Cannabis", "kg")]["std_qty"] == 11.34 and by[("Cannabis", "kg")]["qualifier"] == "More than"
    assert by[("Cannabis", "kg")]["suspected"]
    assert ("Cannabis", "plants") in by and ("Cocaine", "litres") in by


def test_seizure_details():
    rows, _ = seizure.details("Officers seized 300 kg of cocaine hidden inside a shipment of bananas, worth an estimated "
                              "US$9 million according to police. Two men were charged.", {"agencies": ["JCF"]})
    r = dict(rows)
    assert r["Declared commodity"] == "bananas" and "police" in r["Reported valuation"]
    assert r["Case development"].startswith("Charged") and "300 kg" in r["Quantity and unit (original)"]


def test_repeats_are_one_source():
    ev = {"title": "Cocaine seized at port", "sources": [
        {"publisher": "Paper A", "url": "https://a.example/x", "date": "2026-11-20"},
        {"publisher": "Jamaica Constabulary Force", "url": "https://jcf.gov.jm/x", "date": "2026-11-21", "official": True},
        {"publisher": "Paper B", "url": "https://b.example/x", "date": "2026-11-22"}]}
    sources.panel(ev)
    p = ev["source_panel"]
    assert p["independent"] == 1 and p["supporting"] == 2 and "not counted as separate confirmations" in p["relationship"]
    assert [s["role"] for s in p["sources"]][1] == "Original release"
    assert sources.guess_lang("Incautan cocaína en el puerto de Kingston con la policía") == "Spanish"


def test_stowaways_topic():
    from watch import extract
    r = extract.extract({"title": "Stowaway found in wheel well of flight from Jamaica", "summary": ""})
    assert "Stowaways" in r["categories"] and r["kind"] == "Incident"


def test_english_decimal_not_thousands():
    from watch import seizure
    assert seizure.quantities("NDLEA seizes 13.795kg of cocaine")[0]["std_qty"] == 13.795
    assert seizure.quantities("incautan 1.200 kilos de cocaína", "es")[0]["std_qty"] == 1200


def test_concealment_and_cover_categories():
    from watch import seizure
    rows = dict(seizure.details("Police find 40 kg of cocaine concealed among a shipment of bananas at Kingston wharf", {})[0])
    assert rows["Concealment category"] == "Cargo cover load"
    assert rows["Cover load / goods used as cover"] == "bananas (Fruit and vegetables)"
    rows = dict(seizure.details("Woman held with cocaine pellets she swallowed", {})[0])
    assert rows["Concealment category"] == "Swallowed / internal body"
    # a drug courier is a person, not a courier parcel
    assert "Courier" not in dict(seizure.details("NDLEA arrests two cocaine couriers", {})[0])["Concealment category"]


def test_review_approval_marks_only_published_new_items(tmp_path):
    import json
    from watch import record
    p = tmp_path / "published.json"
    p.write_text(json.dumps({"baseline": ["BWO-1"], "approved": {}}))
    shown = [{"event_id": "BWO-1"}, {"event_id": "BWO-2"}]
    assert record.save_approved(str(p), shown, "2026-11-28") == 1
    appr = record.load_approved(str(p))
    assert appr == {"BWO-2": "2026-11-28"}
    ev = {"event_id": "BWO-2", "level": "Low"}
    record.apply_review(ev, {}, appr)
    assert ev["review_status"] == "Reviewed"
    ev1 = {"event_id": "BWO-1", "level": "Low"}
    record.apply_review(ev1, {}, appr)
    assert ev1["review_status"] == "Automatically collected"
    assert record.last_publish(str(p), before="2026-11-29") == "2026-11-28"


def test_alerts_since_date():
    from watch import alerts
    evs = [{"first_seen": "2026-11-27", "date": "2026-11-27", "kind": "Incident", "level": "High"},
           {"first_seen": "2026-11-25", "date": "2026-11-25", "kind": "Incident", "level": "High"}]
    assert len(alerts.pick(evs, "2026-11-28", "Jamaica", since="2026-11-26")) == 1


def test_interception_needs_a_stop_near_the_place():
    ev = {"kind": "Incident", "airports": ["Santo Domingo Las Americas (SDQ)"], "countries": ["Peru"], "location": {}}
    text = "Peru joins a network against document fraud. Officials met at Las Americas airport in Santo Domingo."
    assert journey.interception(text, ev) == ("", "")
    text2 = "Two women were arrested at Las Americas airport carrying forged passports."
    assert journey.interception(text2, ev)[1] == "Dominican Republic"
    j = journey.build({"kind": "Incident", "airports": [], "location": {}}, text, False)
    assert j["interception"] == "" and j["basis"] == ""


def test_cooperation_news_is_an_update_and_nationals_from_is_not_an_origin():
    assert extract({"title": "Perú refuerza sus fronteras: Migraciones se incorpora a red internacional contra fraude documental"})["kind"] == "Update"
    assert extract({"title": "Nine countries join forces to combat document fraud"})["kind"] == "Update"
    assert extract({"title": "Police arrest two over fake passports after agreement with Interpol"})["kind"] == "Incident"
    assert X.find_route("Thirteen foreign nationals from Brazil were arrested") == ("", "")
    assert X.find_route("a flight from Brazil to Spain")[0] == "Brazil"


def test_american_as_an_adjective_is_not_a_nationality():
    assert journey.nationalities("American workers and taxpayers lost millions") == []
    assert journey.nationalities("U.S. Customs and Border Protection officers seized guns") == []
    assert journey.nationalities("a U.S. citizen was arrested at the airport") == ["United States"]
    assert journey.nationalities("three Jamaican men were arrested") == ["Jamaica"]


def test_precursor_chemicals_are_their_own_substance():
    from watch import seizure as S
    q = S.quantities("Police seized 50 kg of fentanyl precursors at the port")
    assert q[0]["substance"] == "Precursor chemicals" and q[0]["std_unit"] == "kg"
    q = S.quantities("Customs seized 2,000 litres of acetic anhydride in a container")
    assert q[0]["substance"] == "Precursor chemicals" and q[0]["std_unit"] == "litres"
    assert S.substances("Police seized 50 kg of fentanyl precursors") == ["Precursor chemicals"]
    assert S.quantities("seized 10 kg of cocaine at the airport")[0]["substance"] == "Cocaine"
    assert "Drug trafficking" in extract({"title": "Customs seize 3 tonnes of precursor chemicals at Kingston port"})["categories"]
