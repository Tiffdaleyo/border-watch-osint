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
