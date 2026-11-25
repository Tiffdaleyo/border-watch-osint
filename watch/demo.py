"""Invented sample headlines, used only by `python run.py --demo` to show how the site looks.
None of these events happened. The links point to example.org on purpose."""
import datetime as dt

SAMPLES = [
    (0, "Police dismantle forged passport factory in Port-au-Prince, seize 120 blank passports and laminating equipment", "Haiti"),
    (1, "Two men held at Norman Manley airport with fake Canadian visas, en route to Canada", "Jamaica"),
    (1, "Impostor caught at Heathrow using someone else's passport after arriving from Jamaica", "UK"),
    (2, "Migrant smuggling ring busted: 34 migrants intercepted off the Bahamas, captain arrested", "Bahamas"),
    (3, "Detenidos tres hombres con pasaportes falsos en el aeropuerto de Las Américas con destino a España", "DR"),
    (4, "Immigration officer arrested over bribes for fraudulent visa stamps at Piarco", "Trinidad"),
    (5, "Court sentences woman for human trafficking network moving victims from Venezuela to Trinidad and Tobago", "TT"),
    (6, "Citizenship by investment fraud: five charged over golden passport applications using fake documents", "Caribbean"),
    (8, "Démantèlement d'une filière d'immigration clandestine à Roissy : 12 faux passeports saisis", "France"),
    (9, "Fake ID and birth certificate racket uncovered in Kingston, Jamaica; three charged", "Jamaica"),
    (11, "Passengers with forged residence permits stopped at Madrid Barajas on flight from Colombia", "Spain"),
    (13, "Look-alike fraud: man used his brother's passport to board flight from Montego Bay, Sangster officials say", "Jamaica"),
    (16, "Alien smuggling case: Florida jury convicts boat captain who brought migrants from Bimini, Bahamas", "US"),
    (20, "Polícia Federal prende quadrilha que vendia passaportes falsos em Guarulhos", "Brazil"),
    (24, "Overstay crackdown: 40 foreign nationals arrested in Belize immigration raid", "Belize"),
    (0, "UK announces new visa requirement for nationals of three Caribbean countries from next month", "UK"),
    (1, "Interpol red notice suspect arrested at Sangster airport on arrival from Toronto", "Jamaica"),
    (2, "Coast guard intercepts boat with 52 Haitian migrants near Turks and Caicos", "TCI"),
    (3, "Schengen Entry/Exit System: what travellers from the Caribbean need to know", "EU"),
    (4, "Deportation flight with 38 deportees lands in Kingston, Jamaica", "Jamaica"),
    (5, "Police charge owner of Example Travel Agency over fake visa appointment letters", "Demo watch list"),
    (7, "Dominica pauses citizenship by investment applications from two countries after fraud review", "Dominica"),
    (10, "Migración irregular por el Darién cae 40% este año, según Panamá", "Panama"),
    (12, "Canada ends visa-free travel for some passport holders, introduces electronic travel authorisation changes", "Canada"),
    (0, "Passenger arrested at Norman Manley airport after swallowing 80 cocaine pellets on flight to London", "Jamaica"),
    (1, "Customs seize 12 firearms and 2,000 rounds of ammunition hidden in barrel shipment at Kingston Wharves", "Jamaica"),
    (2, "Airport baggage handler arrested over 25 kg of cocaine concealed in suitcases at Montego Bay", "Jamaica"),
    (3, "Woman held at Miami International with US$180,000 in undeclared cash bound for Jamaica", "US"),
    (4, "Port police find 1.2 tonnes of cocaine in misdeclared banana container from Ecuador via free zone", "Belgium"),
    (6, "Stowaway found in wheel well of cargo flight arriving from Port-au-Prince", "Haiti"),
    (8, "Terror suspect on sanctions list arrested at Istanbul Airport while travelling on a forged passport", "Turkey"),
    (9, "Wildlife smuggling: 40 parrots found in luggage at Georgetown airport", "Guyana"),
    (10, "Caribbean islands introduce airport health screening after dengue outbreak, new entry requirements for travellers", "Caribbean"),
    (15, "Air cargo shipment of counterfeit goods and ganja seized by customs at Sangster", "Jamaica"),
    (30, "Morphing attack detected: forged passport photo blends two faces, airport e-gates flag it", "EU"),
]


def sample_items(today=None):
    today = today or dt.date.today()
    out = []
    for i, (age, title, _) in enumerate(SAMPLES):
        out.append({"title": title, "summary": "", "url": f"https://example.org/demo/{i + 1}",
                    "date": (today - dt.timedelta(days=age)).isoformat(), "source": "DEMO (invented)",
                    "lang": "", "via": "demo"})
    return out
