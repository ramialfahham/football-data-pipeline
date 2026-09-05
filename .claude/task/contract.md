# Task contract — one authoritative competition name, corrected in base

objective: >
  **Make `dim_league.league_name` the single source of truth for a competition's display name**,
  by giving leagues the override seed that teams, countries and coaches already have. Today the
  provider's name reaches the site uncorrected, and it is not unique: API-Football calls
  Brasileirão "Serie A", the same string as Italy's Serie A, so two competitions render an
  identical title, description and H1.
refs: >
  **#55** — "Competition display name has no single source: registry and dim_league disagree, and
  neither is the name we show", open since 2026-08-10. It specifies this fix in full: *"One field,
  in the warehouse, that every surface reads. Published by `dim_league`, with corrections applied
  in base… The registry keeps what it is good at and stops carrying a display name."* This task is
  its WAREHOUSE HALF. ⚠ I did not find #55 until after building, and filed **#106** as a duplicate
  of it, which is closed. The pattern it names is documented independently in
  `dbt_project/docs/layering.md:227` (cross-source reconciliation lives in base) and
  `dbt_project/seeds/schema.yml:472-497` (a correction cites an external source, never taste).
  Surfaced by the build of `feat/navigation-rules-competition-shell`, which is BLOCKED on it (the
  SEO audit refuses two pages with byte-identical titles). That branch is stashed as
  `TEMP-nav-rules-competition-shell`.

scope_paths:
  - .claude/task/contract.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - dbt_project/seeds/league_name_overrides.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/2_base/api_football/base_apif__leagues.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/tests/assert_league_name_overrides_are_corrections.sql
  - dbt_project/tests/assert_competition_name_is_unique.sql

impact_map: >
  writers: no ingestion loader changes. The RAW tables and `stg_apif__leagues` are untouched; the
    correction is applied in the BASE layer, which is where the transformation layer cleans and
    reconciles (CPO 2026-08-14) and where `base_apif__leagues` ALREADY applies exactly this
    pattern for `league_country` via `country_name_overrides`.
  downstream: `dbt ls --select base_apif__leagues+ --resource-type model` (dbt 1.7.19, run
    2026-09-04) returns 17 models:
      base_apif__competition_seasons · base_apif__league_entity · base_apif__leagues ·
      dim_competition_season · dim_league · dim_player_team_season_mapping · fct_standings ·
      int_team_season__deserved_vs_actual · int_team_season__standings_primary ·
      mart_competition_index · mart_fixture_standing_context · mart_matchday_insights ·
      mart_roster · mart_standings · mart_team_profile · mart_team_season ·
      mart_team_season_insights
    ⚠ Only the ones that CARRY `league_name` can change, which is a much smaller set — measured
    with `grep -rn "league_name" dbt_project/models`: `dim_league` (publishes it),
    `mart_competition_index:103` (`as competition_name`) and `mart_matchday_insights:139`.
    ⚠ `league_name` also arrives by TWO OTHER staging paths that this change does NOT touch and
    must not be assumed fixed: `stg_apif__fixtures_next:35` and
    `stg_apif__standings:30` → `base_apif__standings:41`. Neither reaches a mart, so no page
    renders the uncorrected copy — but the REASON matters and an earlier version of this line got
    it wrong (corrected on `analytics-engineer-reviewer`'s trace): it claimed `fct_standings` does
    `select *` from the base "so it does carry the column". It does not. The `select *` is only in
    its import CTE; `fct_standings`' terminal SELECT is an explicit column list that OMITS
    `league_name`, so `mart_standings`' own `select *` propagates nothing. The fixtures path dies
    the same way in `base_apif__fixtures_next`, and `mart_matchday_insights:139` reads
    `l.league_name` from a `dim_league` join, i.e. the CORRECTED value. Recorded because "the
    league name is fixed" would be false as a blanket claim, and because a right conclusion resting
    on a wrong mechanism is the kind of thing that rots into a real defect.
  layer_rules: `check_layer_contract.py` — staging stays raw cleanup only (untouched); the
    correction sits in base; `dim_league` PUBLISHES and does not coalesce, which is the rule
    `base_apif__leagues`' own comment states ("the core dim publishes rather than corrects —
    there is no coalesce in dim_league") and which `feedback_entity_corrections_in_base` records.
  deploy_order: the seed must load before the model builds — `dbt build` orders seeds first via
    `ref()`, so no manual sequencing. Prod picks it up on the next `fdp-nightly` run (04:00 UTC);
    until then the committed `site_v2/src/data/competition_index.json` still holds the old names,
    so the frontend does not change on merge alone. ⚠ That is the sequencing that keeps
    `feat/navigation-rules-competition-shell` blocked: it needs this merged, a nightly, and a
    re-export of `competition_index.json`.
  blast_radius: the `league_name` value for the competitions whose seed row is present, wherever
    `dim_league` publishes it — the fixture payload's `league_name` and
    `mart_competition_index.competition_name`. No count, rank, metric or date changes anywhere.
    Row counts are unchanged: the seed is joined LEFT on `league_code`, and
    `assert_league_name_overrides_are_corrections` fails if a seed row matches no league or
    already equals the provider string.

decisions_taken: >
  The MECHANISM is the CPO's, quoted above and already the repo's approach: a seed mapping applied
  in base. This is the THIRD instance of an existing documented pattern (`team_name_overrides`,
  `country_name_overrides`), which `base_apif__coaches` and `base_apif__player_profiles` both cite
  by name as "the seed + left join + coalesce pattern".

  ⛔ **THE EARLIER VERSION OF THIS PARAGRAPH WAS FALSE AND `scope-auditor` FAILED IT (round 1).**
  It claimed "every value is the name the CPO already authored… this changes no name the reader
  currently sees." That was true when written and became false the same session, when the CPO
  ruled and the seed changed. Corrected rather than softened; the auditor was reading the stale
  text and its finding follows from it.

  ⭐ **THE AUTHORITY IS THE WRITTEN RECORD, NOT A QUOTE FROM THE CPO.** An earlier version of this
  section listed four chat quotes as rulings. Three of the four were already documented in the
  repo, and citing him for them was both unnecessary and the failure class
  `feedback_dont_attribute_repo_practice_to_cpo` names. Cited instead:
  · **Corrections belong in base.** `dbt_project/docs/layering.md:13, 52, 186, 227` — base is
    "entity resolution and first logical standardization across sources", and `:227` puts
    cross-source reconciliation there explicitly so core "receives the already-conformed version".
  · **A correction is a seed row justified by an external source of record, never taste.**
    `dbt_project/seeds/schema.yml:472-497` (the `team_name_overrides` doc): *"Add one only where an
    authoritative external source disagrees with the provider, and cite it — never taste, never a
    nickname, never a locale preference."*
    ⛔ **THIS SEED DOES NOT YET MEET THAT BAR, and an earlier version of this line claimed it did**
    (`scope-auditor`, round 4). `team_name_overrides.source` is defined as a URL of an external
    record (`schema.yml:497`); 19 of this seed's 20 rows cite `docs/competition_registry.yml`, an
    internal file — and this seed's own description says so outright: *"source records where a name
    was taken from, not who is authoritative over it."* So the rule is cited as the STANDARD this
    seed must eventually satisfy, not as one it satisfies today. Reaching it is #55's
    external-record pass, and `acceptance_evidence.md` records the same limit.
  · **The site reads a mart, not a config file.** `docs/content_architecture.md:22` — §1
    Principles, rule 2, "One block = one mart" — machine-enforced since **#826**. This is why no
    registry edit is in scope. (Cited as "§2 rule 2" until `analytics-engineer-reviewer` checked
    the locator and found it wrong; the substance was right, the pointer was not.)
  · **This whole task is #55**, which specifies the field, the correction layer, the registry
    dropping its display name, and the external-record discipline (naming #850 as the model).

  ⚠ **TWO THINGS ARE GENUINELY NOT WRITTEN ANYWHERE, and neither is dressed up as if it were.**
  Both came from the CPO in conversation on 2026-09-04 and neither has a home in the repo yet, so
  they are recorded here as unwritten rather than cited as policy:
  · **A season is not part of an entity's name**, and a season-scoped label is composed. `WC`
    therefore carries `FIFA World Cup`, not `FIFA World Cup 2026`. The composition is **#105**,
    filed and not built; #105 is where this becomes written.
  · **Names are standardised, not abbreviated** — the reason the seven `WCQ*` rows spell out
    "World Cup Qualification …" rather than the registry's "WC Qualification …".
    ⛔ An earlier version of this section DELETED this rationale while the seed kept implementing
    it (`scope-auditor`, round 4), leaving the record misleading about why those seven rows read
    as they do. Removing an over-attribution must not remove the reason with it.
  · **BL1 is "Bundesliga"** — ruled 2026-08-10, recorded on **#55**, found only after building.
    The provider already sends exactly that, so BL1 needs no row: one would equal the provider
    value and the STALE branch of `assert_league_name_overrides_are_corrections` would fail it.
    The wrong value for BL1 is the REGISTRY's long form, which reaches the home page through the
    export — #55's export half, not a row here.
    ⛔ **BL2 IS NOT COVERED BY THAT RULING AND MUST NOT RIDE ON IT** (`scope-auditor`, round 2).
    An earlier version of this line said "BL1 and BL2 are therefore NOT in the seed", attributing
    both to a ruling that names only BL1. That is deciding by analogy on a §10 naming class, which
    the working agreement forbids by name. BL2's two sources DISAGREE — registry
    "2. Fußball-Bundesliga" vs provider "2. Bundesliga" — so by this seed's own inclusion test it
    is a candidate, and nothing has ruled which is right. It is therefore left on the provider
    value like the other unverified names and is explicitly inside **#55**'s scope. That is MY
    deferral, not a ruling.

  Measured both directions: 48 competitions, **20 corrected, 28 left on the provider name.**

  THRESHOLD DECLARATIONS: no new mechanism (third use of a documented pattern), no new dependency,
  no recurring cost (a 21-row seed; the nightly's scan does not measurably change). No guard is
  loosened — two singular tests are ADDED.

decisions_reserved:
  - **The wording of any competition's name is the CPO's, permanently.**
    ⚠ One row DID change on my own initiative and has been REVERTED after `scope-auditor` caught
    it: `WCQIP` was written "Play-offs", matching the provider's hyphenation, against the
    registry's "Playoffs". Nobody ruled that. It is "Playoffs" again, and #55's external-record
    pass will settle the spelling like every other row.
  - **Whether the 28 uncorrected names are actually right — BL2 among them, named explicitly.**
    The seed was derived from where the registry and the provider DISAGREE, and that method cannot
    see a name both sources get wrong together — `UECL` is the proven case (UEFA dropped "Europa"
    in 2024; both still carry it), in the seed only because #55 had caught it by hand. **BL2 is
    the opposite case**: its sources DO disagree, so the method flags it, and I still left it
    alone because nothing on record covers it and I will not pick a competition's name. Both belong
    to **#55**, which already states the external-record discipline they need and names #850 as the
    model. ⚠ I filed **#107** for that pass during this task and CLOSED it as a duplicate of #55;
    it was work already tracked, not a new finding.
  - **Retiring `name` from `docs/competition_registry.yml`.** After the follow-up below, no code
    reads it. Whether the authored name should live only in the seed is a single-source question
    for the CPO; leaving two hand-maintained homes is exactly what the single-source rule dislikes.
  - **Whether `stg_apif__standings.league_name` / `stg_apif__fixtures_next.league_name` should be
    dropped or corrected.** No mart reads them today, so they are dormant duplicates rather than
    live defects. Not touched here.

follow_up: >
  **The export still reads the registry for display names** — `_registry_competitions` at
  `export_site_data.py:944, 995, 1078, 1206`, surfacing on competitions.json, the competition
  payloads, the leaderboards payloads and the landing payload. Seeding the override makes the two
  sources AGREE, which removes the symptom; it does not remove the second source. Making the export
  read the warehouse is its own change, because `_competitions_index()` is deliberately
  BigQuery-free today ("registry-only, no BigQuery") and that property would have to go. File it.

done_when:
  - `python scripts/check_registry_var_sync.py` passes (the registry seed is untouched by this
    change; the new seed is separate).
  - `.venv/Scripts/dbt.exe parse` succeeds and `dbt ls --select league_name_overrides+` shows the
    seed reaching `base_apif__leagues`.
  - `python -m sqlfluff lint` from the REPO ROOT passes on both new tests and the changed model.
  - Both singular tests are MUTATION-TESTED RED before being accepted green: break the coalesce
    and `assert_competition_name_is_unique` must fail; point a seed row at a league_code that does
    not exist, and at a name equal to the provider's, and
    `assert_league_name_overrides_are_corrections` must fail on each.
  - `python -m pytest tests/ -q` passes.
  - No two competitions share a `competition_name` in `mart_competition_index`.

amendments: >
  2026-09-04 — `decisions_taken` and `decisions_reserved` REWRITTEN on `scope-auditor`'s round-1
  FAIL. Authority: the CPO's rulings of the same session, now quoted in `decisions_taken` rather
  than paraphrased. No path was added or removed; scope is unchanged. The auditor's finding was
  correct on the facts it could see — the contract asserted the seed introduced no new names while
  the diff changed eight of them — and the fix is to record the rulings, not to soften the claim.
  Content: (a) the false "not new naming" paragraph replaced by the four rulings verbatim;
  (b) the stale "WC / WCQ / BL1 flagged, not decided" bullet replaced by what is genuinely still
  reserved; (c) the unauthorised `Play-offs` spelling reverted in the seed and recorded here;
  (d) **#55** cited as the issue this implements and **#105** as what it defers.

  ⚠ This task's work is the WAREHOUSE HALF OF #55, which specified the identical fix 24 days
  before the branch existed and which I did not find until after building. #106 was filed by me
  during this task and CLOSED as its duplicate.

  2026-09-04 (round 4) — two corrections, both `scope-auditor` findings, both accepted.
  (a) `decisions_taken` claimed this seed satisfies the external-source-of-record rule it cites.
  It does not: 19 of 20 rows cite the registry, an internal file, and this seed's own description
  says `source` is provenance not authority. The citation is now framed as the standard to reach,
  with #55 owning the pass that reaches it.
  (b) The round-3 rewrite, in stripping over-attribution, DELETED the reason the seven `WCQ*` rows
  are spelled out while the seed still spelled them out. Restored as an unwritten rule beside the
  season rule. ⚠ Over-correcting is the same defect as over-claiming: the fix for "cited him
  without a record" is to state the reason plainly, not to delete the reason.
  ⛔ Also caught this round, and worse than either finding: `review_input.patch` was STALE — staged
  without regenerating, so rounds were reviewed against a superseded diff. The documented trap
  (`--review-patch` must be REGENERATED with a redirect after every `git add`). Regenerated.

  2026-09-04 (round 3) — `decisions_taken` REWRITTEN AGAIN, and this time the fix is to stop
  citing the CPO at all. `scope-auditor` FAILed round 3 on "agreed with the CPO as its own pass"
  having no record; the correct response was not to write his words into `escalations.log` but to
  notice that THREE OF THE FOUR "rulings" were already documented in the repo —
  `layering.md:13/52/186/227`, `seeds/schema.yml:472-497`, `content_architecture.md` §2 rule 2 —
  and that the fourth, this whole task, is **#55**. Authority now cites those; the only genuinely
  unwritten rule (a season is not part of an entity's name) is flagged as unwritten and is #105's
  to establish. #107 closed as a duplicate of #55. No code changed.
  ⛔ **This is the same class caught THREE times on one branch** — attribution by prose instead of
  by record. Each time the reviewer found it and I did not.

  2026-09-04 (round 2) — `decisions_taken` and `decisions_reserved` corrected again on
  `scope-auditor`'s second FAIL. Authority: none needed; this REMOVES an attribution rather than
  adding one. The paragraph had said "BL1 and BL2 are therefore NOT in the seed" and credited a
  ruling that names only BL1 — deciding BL2 by analogy on a §10 naming class. BL2 is now stated as
  MY deferral to #55, with its two disagreeing sources quoted. No path, no code and no seed row
  changed; the diff moves only this file. ⚠ Recurrence of the failure class
  `feedback_dont_attribute_repo_practice_to_cpo` records — caught by the reviewer, not by me,
  which is the same way it was caught the previous five times.
