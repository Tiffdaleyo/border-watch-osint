"""The main news language(s) of each country, so the site can show where we are blind.

A country whose main language we do not search can look quiet only because we cannot read its news. The
language coverage map uses this table: green = reports found, yellow = we read its language but found nothing,
red = we do not search its main language and found nothing (a blind spot, not a quiet country).
Names follow the world map (Natural Earth short names)."""

NAMES = {"en": "English", "es": "Spanish", "fr": "French", "pt": "Portuguese", "nl": "Dutch", "de": "German",
         "it": "Italian", "ar": "Arabic", "zh": "Chinese", "ru": "Russian", "tr": "Turkish", "fa": "Persian",
         "hi": "Hindi", "bn": "Bengali", "ur": "Urdu", "id": "Indonesian", "ms": "Malay", "th": "Thai",
         "vi": "Vietnamese", "ja": "Japanese", "ko": "Korean", "pl": "Polish", "uk": "Ukrainian", "ro": "Romanian",
         "el": "Greek", "he": "Hebrew", "sw": "Swahili", "am": "Amharic", "so": "Somali", "ht": "Haitian Creole",
         "sv": "Swedish", "no": "Norwegian", "da": "Danish", "fi": "Finnish", "cs": "Czech", "sk": "Slovak",
         "hu": "Hungarian", "bg": "Bulgarian", "sr": "Serbian", "hr": "Croatian", "sq": "Albanian", "my": "Burmese",
         "km": "Khmer", "lo": "Lao", "ne": "Nepali", "si": "Sinhala", "ka": "Georgian", "hy": "Armenian",
         "az": "Azerbaijani", "kk": "Kazakh", "uz": "Uzbek", "mn": "Mongolian", "tl": "Filipino", "ps": "Pashto",
         "et": "Estonian", "lv": "Latvian", "lt": "Lithuanian", "sl": "Slovenian", "mk": "Macedonian", "is": "Icelandic",
         "ti": "Tigrinya", "mg": "Malagasy", "ky": "Kyrgyz", "tg": "Tajik", "tk": "Turkmen", "dz": "Dzongkha"}

_BY_LANG = {
    "en": ["United States of America", "United Kingdom", "Canada", "Australia", "New Zealand", "Ireland", "Jamaica",
           "Bahamas", "Belize", "Guyana", "Trinidad and Tobago", "Nigeria", "Ghana", "Kenya", "Uganda", "Zambia",
           "Zimbabwe", "South Africa", "Sierra Leone", "Liberia", "Gambia", "Botswana", "Namibia", "Malawi", "Lesotho",
           "eSwatini", "Fiji", "Papua New Guinea", "Solomon Is.", "Vanuatu", "Puerto Rico", "Falkland Is.", "Philippines",
           "India", "Pakistan", "Malaysia", "Sri Lanka", "Bangladesh", "Tanzania", "S. Sudan", "Rwanda", "Greenland"],
    "es": ["Spain", "Mexico", "Guatemala", "Honduras", "El Salvador", "Nicaragua", "Costa Rica", "Panama", "Cuba",
           "Dominican Rep.", "Colombia", "Venezuela", "Ecuador", "Peru", "Bolivia", "Chile", "Argentina", "Uruguay",
           "Paraguay", "Puerto Rico", "Eq. Guinea"],
    "fr": ["France", "Haiti", "Belgium", "Switzerland", "Luxembourg", "Senegal", "Mali", "Niger", "Burkina Faso",
           "Côte d'Ivoire", "Guinea", "Benin", "Togo", "Cameroon", "Gabon", "Congo", "Dem. Rep. Congo",
           "Central African Rep.", "Chad", "Madagascar", "Djibouti", "Burundi", "Morocco", "Algeria", "Tunisia",
           "Mauritania", "New Caledonia", "Fr. S. Antarctic Lands", "Rwanda", "Canada", "Lebanon"],
    "pt": ["Portugal", "Brazil", "Angola", "Mozambique", "Guinea-Bissau", "Timor-Leste"],
    "nl": ["Netherlands", "Suriname", "Belgium"],
    "de": ["Germany", "Austria", "Switzerland", "Luxembourg"],
    "it": ["Italy", "Switzerland"],
    "ar": ["Saudi Arabia", "United Arab Emirates", "Qatar", "Kuwait", "Oman", "Yemen", "Iraq", "Syria", "Jordan",
           "Lebanon", "Palestine", "Egypt", "Libya", "Sudan", "Morocco", "Algeria", "Tunisia", "Mauritania", "Chad",
           "Djibouti", "W. Sahara", "Somaliland"],
    "zh": ["China", "Taiwan"], "ru": ["Russia", "Belarus", "Kazakhstan", "Kyrgyzstan"], "tr": ["Turkey", "N. Cyprus"],
    "fa": ["Iran", "Afghanistan"], "ps": ["Afghanistan"], "hi": ["India"], "bn": ["Bangladesh"], "ur": ["Pakistan"],
    "id": ["Indonesia"], "ms": ["Malaysia", "Brunei"], "th": ["Thailand"], "vi": ["Vietnam"], "ja": ["Japan"],
    "ko": ["South Korea", "North Korea"], "pl": ["Poland"], "uk": ["Ukraine"], "ro": ["Romania", "Moldova"],
    "el": ["Greece", "Cyprus"], "he": ["Israel"], "sw": ["Tanzania", "Kenya"], "am": ["Ethiopia"], "ti": ["Eritrea"],
    "so": ["Somalia", "Somaliland"], "ht": ["Haiti"], "sv": ["Sweden"], "no": ["Norway"], "da": ["Denmark"],
    "fi": ["Finland"], "cs": ["Czechia"], "sk": ["Slovakia"], "hu": ["Hungary"], "bg": ["Bulgaria"],
    "sr": ["Serbia", "Montenegro", "Bosnia and Herz.", "Kosovo"], "hr": ["Croatia", "Bosnia and Herz."],
    "sq": ["Albania", "Kosovo"], "my": ["Myanmar"], "km": ["Cambodia"], "lo": ["Laos"], "ne": ["Nepal"],
    "si": ["Sri Lanka"], "ka": ["Georgia"], "hy": ["Armenia"], "az": ["Azerbaijan"], "kk": ["Kazakhstan"],
    "uz": ["Uzbekistan"], "mn": ["Mongolia"], "tl": ["Philippines"], "et": ["Estonia"], "lv": ["Latvia"],
    "lt": ["Lithuania"], "sl": ["Slovenia"], "mk": ["Macedonia"], "is": ["Iceland"], "mg": ["Madagascar"],
    "tg": ["Tajikistan"], "tk": ["Turkmenistan"], "dz": ["Bhutan"],
}

# for countries where English or French is official but most local news is in another language, that language
# counts as the main one, so "we read English" does not hide a gap
MAIN_FIRST = {"Haiti": ["fr", "ht"], "India": ["en", "hi"], "Pakistan": ["en", "ur"], "Philippines": ["en", "tl"],
              "Bangladesh": ["bn", "en"], "Sri Lanka": ["si", "en"], "Malaysia": ["ms", "en"], "Tanzania": ["sw", "en"],
              "Kenya": ["en", "sw"], "Rwanda": ["en", "fr"], "Morocco": ["ar", "fr"], "Algeria": ["ar", "fr"],
              "Tunisia": ["ar", "fr"], "Lebanon": ["ar", "fr"], "Belgium": ["nl", "fr"], "Switzerland": ["de", "fr", "it"],
              "Canada": ["en", "fr"], "Puerto Rico": ["es", "en"]}

# map name -> the names our reports use
MAP_TO_REPORT = {"United States of America": "United States", "Dominican Rep.": "Dominican Republic",
                 "Bosnia and Herz.": "Bosnia and Herzegovina", "Czechia": "Czech Republic",
                 "Côte d'Ivoire": "Ivory Coast", "Dem. Rep. Congo": "Democratic Republic of the Congo",
                 "Macedonia": "North Macedonia"}


def table():
    """{map country name: [language codes, main first]}"""
    out = {}
    for code, countries in _BY_LANG.items():
        for c in countries:
            out.setdefault(c, [])
            if code not in out[c]:
                out[c].append(code)
    for c, langs in MAIN_FIRST.items():
        out[c] = langs + [x for x in out.get(c, []) if x not in langs]
    return out
