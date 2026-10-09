# Acceptance evidence — Sint Maarten in the country list

Read from the committed seed with a script, and from the log of the nightly run that failed on 2026-10-09.

criteria_demonstrated:
  - THE ROW. countries.csv holds 225 countries; sint-maarten,Sint Maarten sits between singapore and slovakia.
    country_key and country_name are unique, none is blank, every name is ASCII. dim_country.sql's header
    comment counts 225 rows; the edit is inside a {# #} comment, so the compiled SQL is unchanged.
  - THE FAILING VALUE. The nightly's relationships test returned one row ("Got 1 result"), player L. Bleeker,
    whose player_birth_country reads "Sint Maarten". That value is now a country_name in countries.csv, so the
    test has no value left to return. Every other model in the run passed (PASS=1477, ERROR=1, SKIP=0).
  - pytest tests/ passes: 1490 passed, 2 skipped.
