"""
Add new matchPreview footer + formContext i18n keys to all three locale files.
Writes with straight ASCII quotes to avoid curly-quote encoding issues.
"""
import json

LOCALES = {
    "de": {
        "formContext": "Form: letzte 5 Spiele dieser Saison",
        "formContextDomestic": "Form: letzte 5 Spiele dieser Saison",
        "formContextDomesticPreseason": "Form: komplette Vorsaison",
        "formContextWcQualifiers": "Form: alle Qualifikationsspiele",
        "formContextWcTournament": "Form: alle bisherigen WM-Spiele",
        "footAvgDesc": "Durchschnittswert pro Spiel im Formfenster",
        "footPctDesc": "Quote über alle Formspiele kombiniert – Summe der Treffer geteilt durch Summe der Versuche, kein Mittelwert der Einzelquoten",
        "footMissingDesc": "Vom Datenanbieter nicht geliefert",
        "footMissingWcDesc": "Keine Qualifikationsdaten verfügbar. Gastgeberländer spielen keine Qualifikation und zeigen – bei allen Formkennzahlen vor Turnierbeginn.",
    },
    "en": {
        "formContext": "Form: last 5 matches this season",
        "formContextDomestic": "Form: last 5 matches this season",
        "formContextDomesticPreseason": "Form: full previous season",
        "formContextWcQualifiers": "Form: all qualifying matches",
        "formContextWcTournament": "Form: all World Cup matches so far",
        "footAvgDesc": "Per-match average in the form window",
        "footPctDesc": "Ratio across all form matches combined – total hits ÷ total attempts, not an average of per-match rates",
        "footMissingDesc": "Not provided by the data source",
        "footMissingWcDesc": "No qualifying data available for this team. Host nations do not play qualifiers and show – for all form metrics before the tournament begins.",
    },
    "fi": {
        "formContext": "Muoto: viimeiset 5 ottelua tällä kaudella",
        "formContextDomestic": "Muoto: viimeiset 5 ottelua tällä kaudella",
        "formContextDomesticPreseason": "Muoto: koko edellinen kausi",
        "formContextWcQualifiers": "Muoto: kaikki karsintaottelut",
        "formContextWcTournament": "Muoto: kaikki tähänastiset MM-ottelut",
        "footAvgDesc": "Ottelukohtainen keskiarvo muotojaksolla",
        "footPctDesc": "Suhde kaikilla muoto-otteluilla yhteensä – onnistumisten summa jaettuna yritysten summalla, ei ottelukohtaisten prosenttien keskiarvo",
        "footMissingDesc": "Tietolähde ei toimittanut tätä arvoa",
        "footMissingWcDesc": "Joukkueella ei ole karsintadataa saatavilla. Isäntämaat eivät pelaa karsinnoissa ja näyttävät – kaikissa muotoluvuissa ennen turnauksen alkua.",
    },
}

FILES = {
    "de": "site/i18n/de.json",
    "en": "site/i18n/en.json",
    "fi": "site/i18n/fi.json",
}

KEYS_TO_REMOVE = ["foot", "footWc", "footDataGap"]

ORDER_AFTER = "errorPrefix"

for lang, path in FILES.items():
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    mp = data.setdefault("matchPreview", {})

    for k in KEYS_TO_REMOVE:
        mp.pop(k, None)

    for k, v in LOCALES[lang].items():
        mp[k] = v

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"{lang}: written ok")
