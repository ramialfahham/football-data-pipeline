# Verification — club regions on the Teams page

Read on prod data on 2026-10-31. The compiled `mart_team_index` and the queries below ran against
the prod datasets; the bytes of each were approved before it ran.

criteria_demonstrated:
  - The seed carries the five corrections: 3045 Dragon El Salvador, 5242 Al Shorta Iraq, 6414 Cano Sport Equatorial Guinea, 15565 GR / SIAF Djibouti, 19116 15 de Agosto Equatorial Guinea, each with its CONCACAF, AFC or CAF source. `base_apif__teams_global` takes the correction before the provider's country, so dim_team carries the corrected one once the seed is built. The 78 existing rows are unchanged apart from the empty `provider_country` field (compared field by field against main).
  - The provider's latest country in `base_apif__teams` for the five ids is France, Sudan, Cyprus, Austria and Paraguay, each equal to the row's `provider_country`, so the warn test does not flag them. A row with an empty `provider_country` is flagged when the provider sends any country, as before.
  - The compiled mart, run on prod data and compared with prod `mart_team_index` on team, country, region, country region, country order, order in country, ranks, entity type and league: one row differs, Auckland City, `region_key` and `country_region_key` NULL to OFC, `country_order` 144 unchanged. No team is added or lost.

dbt parse and SQLFluff (mart and test) pass. pytest: 1,619 passed, 2 skipped. The fast offline gates
pass: layer contract, registry sync, competition type seed, UI metric labels, copy gate (1,170
strings), description hygiene.
