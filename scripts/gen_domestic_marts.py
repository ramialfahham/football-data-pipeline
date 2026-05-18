from pathlib import Path

src = Path("dbt_project/models/5_marts/mart_matchday_insights_bl1.sql").read_text(encoding="utf-8")
for code, name in [("PL", "Premier League"), ("PD", "La Liga"), ("BL2", "2. Bundesliga")]:
    t = src.replace("BL1", code)
    t = t.replace(
        f"when um.league_code = '{code}' then 'Bundesliga'",
        f"when um.league_code = '{code}' then '{name}'",
    )
    t = t.replace(f"Canonical Bundesliga ({code})", f"Canonical {name} ({code})")
    t = t.replace(f"Bundesliga ({code}) matchday", f"{name} ({code}) matchday")
    out = Path(f"dbt_project/models/5_marts/mart_matchday_insights_{code.lower()}.sql")
    out.write_text(t, encoding="utf-8")
    print(out)
