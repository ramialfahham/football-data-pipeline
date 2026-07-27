# Task contract — team name corrections (PR A of four)

> Written on a CLEAN tree, branch `feat/team-name-corrections` off `main` (`92474bc`).
> This is the FIRST of four PRs split out of a plan that two independent reviewers judged
> over-scoped. It is deliberately the smallest piece: a seed of externally verified name
> corrections and its base-layer join. No slug work, no new model class, no export change.

objective: >
  `dim_team` is a passive pass-through of the provider's `/teams` endpoint, which returns a short
  display label of unverified quality. That single field drives the fixture card, the team page H1,
  the `<title>`, the meta description and the URL slug, so 18 teams in 9 groups are currently
  indistinguishable from each other ("Rangers" vs "Rangers", "Lokomotiv" vs "Lokomotiv"). This adds
  a CPO-owned seed of 14 externally verified corrections and joins it in the base layer, so every
  downstream surface inherits one corrected name from one place.

  Independently valuable and NOT a slug change: it is what makes `<title>` uniqueness across the
  generated set achievable, which is #844's binding requirement.

refs: >
  #850 (the verified table with per-row sources) · #851 (why one field is display AND identity) ·
  #844 (the SEO build gate this enables).

  Two independent assessments, 2026-07-27, both concluded the slug-assignment engine (#852) does NOT
  block #844 and should be deferred; the name corrections are the half with a real claim to gating
  it. #852 is downgraded to PR D accordingly.

  Domain knowledge gathered before building (working_agreement norm): every corrected name was
  verified against an external source one club at a time, per
  [[feedback-verify-real-world-identity]], after an earlier draft asserted "Glasgow Rangers" from
  memory and was corrected by the CPO ("the actual name is rangers fc / do your homework").
  Wikipedia: the club "is often referred to as Glasgow Rangers, though this has never been its
  official name."

scope_paths:
  - dbt_project/seeds/team_name_overrides.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/2_base/api_football/base_apif__teams_global.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/tests/assert_team_name_overrides_still_needed.sql
  - .claude/active_work.md

impact_map: >
  writers: `base_apif__teams_global` is written only by dbt, from `base_apif__teams`
    (grain league_code x team_api_id) deduped to grain team_api_id via
    `qualify row_number() over (partition by team_api_id order by raw_ingested_at desc) = 1`.
    The new seed `team_name_overrides` is written by `dbt seed`.

  downstream: EVIDENCE (grep over the real tree — `dbt ls` cannot be run, dbt CLI is broken locally
    per the handover's Operational notes, so `ci-data-build` is the authoritative check):

      $ grep -rl "base_apif__teams_global" dbt_project/models/
      dbt_project/models/2_base/api_football/base.yml
      dbt_project/models/3_core/core.yml
      dbt_project/models/3_core/dim_team.sql          <- the ONLY .sql child

      $ grep -rl "dim_team" dbt_project/models/5_marts/ | wc -l    -> 17
      $ grep -rl "ref('dim_team')" dbt_project/models/ | wc -l     -> 21

    So: ONE direct child (`dim_team`, a pure projection), 17 mart models downstream of it, 21 models
    in total. Plus `scripts/export_site_data.py`, which joins `dim_team` for the fixture payload's
    `home_team_name` / `away_team_name` at lines 850-851 — `fct_fixture` carries no team name of its
    own. The corrected name therefore reaches every surface.

    CORRECTION: an earlier draft of this contract asserted "27 mart models" from memory. Counted, it
    is 17 marts / 21 models. scope-auditor flagged it as an Appendix A6 assert-before-measure defect;
    fixed here by running the command and pasting the output rather than by arguing the number.

  layer_rules: `check_layer_contract.py::check_base_layer` requires every `2_base` model to
    materialise as a VIEW — this change adds a join to an existing view and does not alter its
    materialisation. `layering.md` places "first logical transformations so the warehouse agrees on
    what a team is" in base, which is exactly this. The CPO ruled the placement explicitly
    (2026-07-27): "the single source of truth for these dimensions... should be in the core layer in
    dim tables that propagate downstream. Base is the right layer to do these preparations."
    `engineering_standards.md` line 26 requires an explicit import CTE per `ref()`; line 82 requires
    `unique`/`not_null` on grain columns.

  deploy_order: `dim_team` is a full-refresh table and `base_apif__teams_global` is a view, so both
    rebuild from scratch on the next run — no migration, no incremental backfill, no
    `--full-refresh` needed. The seed must be loaded before the base model compiles, which
    `dbt build` orders automatically via `ref()`. Safe around the 04:00 nightly: worst case the
    nightly runs pre-merge and produces today's (uncorrected) names, exactly as now.
    WARNING: this project shares dbt datasets between CI and prod
    (`project_dbt_shared_ci_prod_datasets`), so a stray local build can clobber prod — no local
    `dbt build` will be run.

  blast_radius: 14 rows change `team_name` in `dim_team` out of 3,249. Every mart and the export
    inherit the new string. NO numeric value changes anywhere — this touches a display/identity
    string only, no metric, no key, no join column. `team_sk` and `team_api_id` are untouched, so
    every relationship test is unaffected.
    KNOWN and deliberate: `fct_fixture_event.team_name_snapshot` is written on insert and never
    revisited, so it keeps the pre-correction string for historical rows. That is the
    `reference_incremental_rename_full_refresh` trap. Handled by documenting the column as
    deliberately historical rather than by a self-heal branch — a self-heal is a separate change to
    an incremental fact and out of scope here.

decisions_taken: >
  - The seed exists and is CPO-owned. Same class as the existing `fixture_event_team_overrides.csv`
    (#526). Authority: the CPO asked "Correct the name -> how?" and, on the answer, "yes write it
    down. this is very important work. we can't allow ambiguity here."
  - The join goes in BASE, not in `dim_team`. Direct CPO ruling, quoted in layer_rules above; an
    earlier draft that put the `coalesce` in `dim_team` was corrected on exactly this point.
  - A row may only be added where an AUTHORITATIVE EXTERNAL SOURCE disagrees with the provider, and
    the source URL is recorded in the row. Never taste.
  - `Bayern München` is NOT corrected to `Bayern Munich`. The CPO ruled one locale-independent slug:
    "It should be bayern-munchen and not bayern-munich because then we should discuss french spanish
    or whatever language versions."

decisions_reserved:
  - Which provider id is canonical in each duplicate pair (Nyasa Big Bullets #4596/#4599, Dragon
    #3045/#21310). NOT decided here and NOT in scope — those are alias rows for
    `fixture_event_team_overrides.csv`, and the Dragon pair is "near-certain, not proven". A §10
    identity call, and per [[feedback-verify-real-world-identity]] it needs external ground truth,
    not an inference from our own tables.
  - The identity of "Warriors" #4207 (Hong Kong). Its ground is shared by three other clubs and no
    standalone HK club of that name was found. Left UNCORRECTED rather than guessed.
  - Whether the ~15 abbreviation/nickname cases (`Sheffield Utd`, `West Brom`) are corrections or
    the names the site should use. Not touched here; they are display preference, not a provider
    error, so adding them would breach the "external source disagrees" rule this contract sets.
  - The country-coalesce defect in this same file (22 of 39 null-country teams DO have a country in
    `stg_apif__teams`; `qualify row_number()` takes one league's row whole and discards it).
    Verified during review and recorded on #853. Deliberately OUT of scope per
    [[feedback-scope-discipline]] — it is a separate data-quality fix in a file I happen to be
    editing, and bundling it is exactly the unauthorized addition that rule forbids.

done_when:
  - `dbt_project/seeds/team_name_overrides.csv` holds exactly the 14 rows from #850, each with its
    source URL, and no row for #4207, #4596, #4599 or #3045.
  - `base_apif__teams_global.sql` has an explicit import CTE per `ref()` (standards line 26), joins
    on `team_api_id`, and `coalesce`s the override over the provider name. Materialisation still
    view.
  - `seeds/schema.yml` declares `unique` + `not_null` on `team_api_id` (standards line 82) — without
    it a duplicated seed row fans out `dim_team` and multiplies every team.
  - A singular test asserts no override row equals the provider's current name, so a row the
    provider has since fixed fails rather than rotting. NOTE (scope-auditor, round 1): that test uses
    an INNER join, so it cannot flag an override whose `team_api_id` has vanished from the provider.
    That case is covered instead by the seed's `relationships` test to `ref('dim_team')`, which fails
    when the id no longer exists — the two together are bidirectional, and no code change is needed.
  - `python scripts/check_layer_contract.py` passes.
  - `python -m pytest tests/ -q` passes (governance hooks + export tests).
  - SQL lint and `dbt parse`/build are verified by CI, NOT locally — dbt CLI and SQLFluff are both
    broken in this environment and a local build would write to the shared prod dataset.
  - Required reviewers per `review_routing.json` for these paths: scope-auditor (always),
    analytics-engineer-reviewer (`dbt_project/**`). NOTE: `seo-expert-reviewer` is merged but absent
    from routing, so it fires on nothing — routing it remains an open governance ask.

amendments: (none)
