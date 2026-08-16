# Task contract — extend country_name_overrides to the full provider set (#69)

objective: >
  `country_name_overrides.csv` carries 3 rows from `!45`, covering only the league surface. #69's
  discovery found the provider sends 245 distinct country strings that resolve to 224 real
  entities, across four dims. Extend the seed to the full set — 67 rows — so every provider
  spelling maps to one canonical English name. This is step 2 of #69's order of work landing as
  data; `dim_country` and the foreign keys are the NEXT unit, not this one.
refs: GitLab #69 (discovery + the naming rulings), #62 (the page that needs it), `!45` (the 3-row seed)

scope_paths:
  - dbt_project/seeds/country_name_overrides.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_country_name_overrides_still_needed.sql
  - .claude/active_work.md

impact_map: >
  writers: the seed is authored by hand. Its ONLY reader is `base_apif__leagues.sql`, which joins
    it on `provider_country` and `coalesce`s over `stg_apif__leagues.country` (added by `!45`).

  downstream: `dbt ls --select country_name_overrides+ --resource-type model` — the seed feeds
    `base_apif__leagues` and everything below it, the same 16 models `!45`'s contract listed.
    ⚠ In practice the blast radius is far narrower: only `dim_league.league_country` changes,
    because `grep -rn "league_country" dbt_project/models/4_intermediate/ dbt_project/models/5_marts/`
    still returns zero — nothing downstream of `dim_league` reads the column.

  blast_radius: MEASURED against prod. `dim_league.league_country` today holds 15 countries plus
    `World` across 45 rows. Of the 67 new rows, exactly TWO change a value that is currently live:
      Turkey  -> Turkey   (unchanged: provider already sends 'Turkey' for TSL)
      South-Korea / Korea Republic -> South Korea (unchanged from `!45`)
    The other 65 rows target `dim_team`, `dim_player` and `dim_coach`, which **do not read this
    seed yet** — so they are inert until `dim_country` lands. Stated plainly because a 67-row seed
    looks like a 67-row change and is not.
    ⚠ ONE row changes an existing mapping's TARGET rather than adding one: nothing. `!45`'s three
    rows keep their targets (Saudi Arabia, South Korea, United States of America) under the new
    rule; only their `source`/`note` text is restated.

  layer_rules: `scripts/check_layer_contract.py`. A seed is configuration, read in BASE where the
    correction already lives (`feedback_entity_corrections_in_base`) — the core dim publishes and
    does not correct. No model changes at all in this MR.

  deploy_order: additive and safe. `dbt seed` runs before the models in every build path, and the
    join is a left join with `coalesce`, so an unmatched provider string falls through to its
    original value exactly as today.

decisions_taken: >
  FOUR CPO rulings, 2026-08-16, recorded in full in `escalations.log` as part of this same commit.
  ⚠ That entry was MISSING from review round 1 and scope-auditor FAILED the branch for it —
  correctly. §11 requires every escalation to land in the log, and §2 says why: "a reviewer cannot
  check whether a claimed ruling exists without it." Each ruling was given after seeing what the
  previous one produced, and the sequence matters because each corrected the one before:

  1. "official form" — the register is the UN English short name, from the UN list the CPO
     supplied (197 entries, six languages), with the diplomatic qualifier stripped.
  2. "Republic of Ireland, keep the long form" — one exception; it renders beside Northern Ireland.
  3. "modern correct name, keep the everyday short form" — given on seeing that rule 1 produced
     `Russian Federation`, `Syrian Arab Republic`, `Lao People's Democratic Republic`. A genuine
     RENAME stands (Czechia, North Macedonia, Eswatini); a FORMAL STATE TITLE is shortened.
  4. "the single source of truth is always english" then, shown that the UN keeps exactly two
     endonyms in its English column, "No, Ivory Coast and Turkey" — so `Türkiye` -> `Turkey`,
     `Côte d'Ivoire` -> `Ivory Coast`, and no label carries a diacritic.

  MEASURED, priced first (461,533 + 474,334 bytes, whole population): 245 distinct provider
  strings across the four dims; 224 canonical entities; 67 rows where the provider string differs
  from the canonical name. 188 of the 224 are UN states — the rest are football associations
  (England n=2723, Scotland, Wales, Northern Ireland, Kosovo, Chinese Taipei), territories, one
  unrecognised state and one historical (Yugoslavia, CPO: "stays as historical").

  ⚠ TWO ROWS ARE EXCEPTIONS TO THE RULE AND SAY SO IN THEIR OWN `source`: `USA` ->
  `United States of America` (the everyday short form would be `United States`) and `Ireland` ->
  `Republic of Ireland`. Citing the general rule as their authority would have been false.

  NEW MECHANISM: none. Same seed, same join, same still-needed test as `!45` — 3 rows to 67.
  RECURRING COST: none. One seed, one left join on a 45-row table.

decisions_reserved:
  - `entity_type` (un_state / association / territory / unrecognised / historical) exists in the
    discovery analysis and is deliberately NOT a column here. The CPO's words on being shown a
    7-column draft: "we only need a mapping between what the provider gives us and what we turn
    into the single source of truth name". It belongs to `dim_country` if anything reads it.
  - `label_i18n_key` per country — 224 keys x 3 locales is a real copy cost and the CPO's to
    authorise. Absent, not forgotten.
  - Confederation per country. #69's shape proposes `dim_country` carries its region, but there is
    NO SOURCE: the registry gives confederation per COMPETITION and the UN file has none.
  - Whether `dim_country` supersedes this seed or sits beside it, as `team_name_overrides` sits
    beside `dim_team`. Next unit.

done_when:
  - The seed carries 67 rows plus the header; `provider_country` is unique.
  - Every row has a `source` and a `note`; the two exception rows cite their own authority.
  - No `country_name` value carries a diacritic.
  - `assert_country_name_overrides_still_needed` passes — no row where override == provider, and
    no row whose provider string has vanished from staging.
  - The seed's `schema.yml` description is corrected: `!45`'s text cites `Timor-Leste` as correctly
    hyphenated and NOT to be touched, and this MR renames it to `East Timor`. Leaving that would
    be a stale claim contradicting the data beneath it.
  - `dbt parse` succeeds; `python scripts/check_layer_contract.py` passes.

amendments:
  - 2026-08-16: + dbt_project/tests/assert_country_name_overrides_still_needed.sql — authority:
    standing rule `feedback_never_loosen_a_guard` (when my change breaks a test, narrow it to
    where it still holds; deleting the assertion ships a silent hole).
    content: `!45` wrote that test to check each override's provider string against
    `stg_apif__leagues.country` ALONE, because the seed was leagues-only. MEASURED against prod:
    that staging column holds just 19 distinct values, of which only 3 are correctable forms
    (`Saudi-Arabia`, `South-Korea`, `USA`). Extending the seed to 67 rows therefore makes **64 of
    them fail** the `provider.country is null` branch — they are real corrections for strings the
    provider sends on the TEAM, PLAYER and COACH surfaces, which that test never looked at.
    The test is widened to the union of all four provider surfaces
    (`stg_apif__leagues.country`, `stg_apif__teams.team_country`,
    `stg_apif__coaches.coach_birth_country`, `stg_apif__player_profiles.birth_country`), matching
    the scope the seed now has. The assertion is unchanged and nothing is downgraded to `warn`.
