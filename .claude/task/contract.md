# Task contract — the team slug loses the provider id (PR B of four)

> Written on a CLEAN tree, branch `feat/team-slug-no-provider-id` off `main` (`9578f4d`).
> PR A (#854, team name corrections) is merged. This PR removes the provider id from the team URL and
> moves slug derivation into the warehouse. Persistence is deliberately NOT here.
>
> This contract is written against the SECOND version of the plan. Two independent experts challenged
> the first version and found six factual errors in it; every one is corrected below and the list is
> in the plan file so they are not repeated.

objective: >
  `slugify(name, id)` in `scripts/export_site_data.py:86` appends the provider id to every team slug
  and recomputes the whole slug from the current name on every export. The CPO ruled the id out:
  "I don't want aston-villa-66 or similar as part of the url. there is no aston-villa-66."

  Derive `team_slug` in the warehouse instead, from the already-settled team name, using a symmetric
  collision ladder that needs no adjudication. Publish it on `dim_team`, carry it through
  `mart_team_profile`, and have the export select it rather than compute it. `/en/teams/aston-villa-66/`
  becomes `/en/teams/aston-villa/`.

  Also settles E3 (transliterate, do not strip): `_kebab`'s NFKD-then-ascii-ignore DELETES any
  character NFKD cannot decompose, so `Preußen Münster` currently yields `preuen-munster`.

refs: >
  #852 (slug engine — this PR is its DERIVED half; the persisted half is PR D) · #850 (the name
  corrections this builds on) · #851 (why the name is identity) · #843 (the URL is derived from an
  unverified mutable field).

  `.claude/task/escalations.log:45` — E2 and E3, PENDING since 2026-06-14, both ruled this session.
  E3 = transliterate (CPO, AskUserQuestion, 2026-07-27). E2 = the warehouse produces slugs, which
  follows from #846 (the export is the consumption layer).

  Domain knowledge gathered BEFORE building, not in review: two independent expert challenges of the
  first plan (an analytics engineer and an SEO/IA expert, both verifying against BigQuery and the
  repo). They corrected the transliteration targets against external convention, found the collision
  ladder was not closed, and found the proposed guard could never fire.

scope_paths:
  - dbt_project/macros/team_name_normalization.sql
  - dbt_project/models/2_base/api_football/base_apif__teams_global.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/dim_team.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/marts.yml
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_team_name_slug_alphabet.sql
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - docs/site_architecture.md
  - .sqlfluff
  - site_v2/src/data/teams/33.json
  - .claude/task/escalations.log
  - .claude/active_work.md

impact_map: >
  writers: `base_apif__teams_global` (a VIEW) is written only by dbt from `base_apif__teams`, deduped
    to grain `team_api_id`. It already applies the PR A name-override join. The new `team_slug` is
    derived here, after the name is settled — a slug computed from an uncorrected name would be wrong.

  downstream: EVIDENCE (grep over the real tree; `dbt ls` cannot run — dbt CLI is broken locally per
    the handover, so `ci-data-build` is authoritative):

      $ grep -rl "base_apif__teams_global" dbt_project/models/
      2_base/api_football/base.yml · 3_core/core.yml · 3_core/dim_team.sql   <- only .sql child

      $ grep -rl "dim_team" dbt_project/models/5_marts/ | wc -l   -> 17
      $ grep -rl "ref('dim_team')" dbt_project/models/ | wc -l    -> 21

    `mart_team_profile.sql` imports `dim_team` at line 35 and projects identity columns explicitly at
    lines 65-72 (`t.team_name`, `t.team_code`, `t.team_country`, ...). `fetch_team_payloads`
    (`export_site_data.py:664`) reads ONLY that mart, so `team_slug` is unreachable in the export
    without adding the column there. The first plan version missed this and would not have worked.

  layer_rules: `check_layer_contract.py::check_base_layer` requires every `2_base` model to be a VIEW —
    unchanged, this adds columns to an existing view. Its purity rules (no join, no distinct) are
    scoped to `STAGING_API_DIR` and do not apply to base; `BASE_FORBIDDEN_UPWARD_REF` matches only
    `ref('dim_|fct_|int_|mart_')`, so the macro and the seed are fine. `layering.md` §2_base allows
    "standardized keys and attributes that downstream layers can rely on", which is what a slug is.
    The model ALREADY uses a window (`qualify row_number()`), so the collision window is the existing
    house pattern rather than a novelty. `engineering_standards.md` line 26 requires an import CTE per
    `ref()`; §1.3 sanctions a macro for "an expression that must sit inside other queries".

  deploy_order: `base_apif__teams_global` is a view and `dim_team` / `mart_team_profile` are
    full-refresh tables, so all three rebuild from scratch on the next run — no migration, no
    incremental backfill. NOT touched: `fct_fixture` (which is `materialized='table'`, contrary to what
    the first plan asserted) and the three genuinely incremental facts. Safe around the 04:00 nightly:
    a pre-merge run produces today's id-suffixed slugs, exactly as now.
    WARNING: CI and prod share dbt datasets only in the sense that `generate_schema_name` prefixes
    non-prod targets (`ci_core` etc.), so a PR build cannot touch prod — but no local `dbt build` will
    be run regardless.

  blast_radius: every team slug changes — 3,249 of 3,249 rows. NO numeric value changes anywhere: this
    adds one string column and alters one string column's derivation. `team_sk` / `team_api_id` are
    untouched, so every relationship test is unaffected.
    URL fallout is near zero because the internal link graph barely exists: `grep -rn "href" site_v2/src`
    returns only `SiteHeader`, `SiteFooter`, the fixture `Breadcrumb`, `index.astro`'s locale links and
    the team page's Home crumb. No team or player deep link exists in the built site.
    ⚠ `site_v2/src/data/teams/33.json` is a COMMITTED sample carrying `"slug": "manchester-united-33"`,
    and `[team].astro:37` feeds `team.slug` into `getStaticPaths`. It must be regenerated in this PR or
    the CI-built site serves a URL the export no longer emits.
    ⚠ Fixture URLs still derive from team NAMES via `fixture_slug()` and are NOT changed here, so a
    fixture URL and a team URL can disagree for the 7 transliteration-affected clubs until that follows.
    Measured churn from PR A's 14 renames: 259 of 58,647 fixtures. Recorded, not fixed.

decisions_taken: >
  - The provider id leaves the team URL. Direct CPO ruling, quoted in objective.
  - E3 = TRANSLITERATE, not strip. CPO ruling via AskUserQuestion, 2026-07-27, logged in
    escalations.log by this PR. The RULE (validated by both expert challenges, and what `unidecode` and
    Transfermarkt do): fold to the base letter where one exists, expand only where none does. So
    `ü→u` (`bayern-munchen`) and `ß→ss` (`rot-weiss-essen`) are ONE rule, not an inconsistency.
  - E2 = the warehouse produces slugs. Follows from #846: assigning identity is derivation, and the
    export is the consumption layer.
  - The collision ladder is SYMMETRIC — a contested name goes to nobody, all contenders take the
    country anchor. No ranking, no importance ordering, no per-collision adjudication. CPO: "i can't
    answer them out of my head and i don't know if i shall always do the babysitting."
  - Two transliteration targets corrected against external sources before building: `ə → a` (the club
    is Sabail FK; `sebail` exists nowhere) and `đ → dj` (Đoković → Djokovic).

decisions_reserved:
  - Persistence. The slug stays DERIVED so the warehouse remains rebuildable from raw. Making it an
    append-only registry with `--full-refresh` blocked would be the first non-reproducible object in
    this warehouse — a §10 NEW-mechanism trade to bring explicitly at launch (PR D / #852), together
    with the `firebase.json` redirects #843 needs. Not decided here.
  - Whether records failing an identity check may hold a slug at all. Two phantom records will silently
    take a canonical bare slug: #3045 (`Dragon`, France, no venue, no founded year — suspected
    duplicate of #21310 AS Dragon) takes `/teams/dragon/`, and #4207 (`Warriors`, Hong-Kong, identity
    unresolved) takes `/teams/warriors/`. Neither collides, so neither produces any signal. Which
    records are duplicates is #850's OPEN alias decision. Shipped as-is with the table in the PR body so
    the choice is explicit rather than silent.
  - Deleting the dead `team_name_key` macro (zero callers, verified repo-wide). Unrelated to this PR;
    needs an explicit yes, so it is NOT touched here.
  - Player and coach slugs. `slugify()` STAYS for players (`export_site_data.py:475`); deleting it
    would be a `NameError`. The player map has 95 unmapped residual characters including Cyrillic
    homoglyphs and bidi marks, so the map is settled for TEAMS only.
  - Whether `slug_map.json` should be keyed by `(type, slug)` rather than the bare slug string.
    Measured collisions today: team↔player 20, player↔coach 90 — harmless only while ids are present.
    Recorded for #844; not changed here.

done_when:
  - A `slugify()` macro exists with the 9-entry lowercase transliteration map (which covers all 17
    affected characters because `lower()` folds the uppercase halves), format characters DELETED rather
    than hyphenated, and the fold-vs-expand rule stated in a comment.
  - `base_apif__teams_global` derives `team_slug` with the CLOSED ladder: each level's candidate tested
    against the whole assigned set, not just its own group, plus an empty-candidate fallback to the id.
  - `dim_team` publishes `team_slug` with `unique` + `not_null`; `mart_team_profile` carries it; the
    export selects it and no longer computes a team slug.
  - `assert_team_name_slug_alphabet.sql` fails on any source name containing a letter that is neither
    ASCII-after-NFKD nor in the map. The guard is on the INPUT — an output-shape guard cannot fire,
    because the final `[^a-z0-9]+ → -` step guarantees the output alphabet.
  - `site_v2/src/data/teams/33.json` regenerated to `manchester-united`.
  - `.sqlfluff` carries `load_macros_from_path` so a model calling the macro can be linted locally.
  - Verified against BigQuery: 3,249 distinct slugs, 0 empty, the id fallback firing EXACTLY twice
    (the Nyasa pair), no level-2 candidate equal to another team's level-1 slug (the live Ararat /
    Ararat-Armenia case), and `sabail` / `preussen-munster` / `rot-weiss-essen` among the outputs.
  - `pytest tests/ -q`, `python scripts/check_layer_contract.py`, and a FULL-rule-set sqlfluff lint all
    pass. A `--rules` subset missed ST06 on PR A; do not use one.
  - ONE commit. `--staged-hash` equals CI's recomputed `main...HEAD` only when the branch is a single
    commit; that cost a round on PR A.
  - Required reviewers for these paths: scope-auditor (always), analytics-engineer-reviewer
    (`dbt_project/**`), cto-reviewer (`scripts/**`, `.sqlfluff` is not routed but `scripts/**` is).
    NOTE: `seo-expert-reviewer` is merged but still absent from `review_routing.json`, so the PR that
    changes every team URL gets NO SEO review. Routing it is a protected-file governance ask and
    remains the CPO's.

amendments:
  - 2026-07-28: + site_v2/src/data/teams/33.json — authority: the CPO-approved plan for this PR
    already names it ("site_v2/src/data/teams/33.json regenerated to manchester-united") and
    done_when requires it; it was omitted from scope_paths by mistake, not by intent. No scope
    widening: the file is the single committed team sample and its `slug` field is exactly the
    string this PR changes. Leaving it stale would make the CI-built site serve
    /en/teams/manchester-united-33/ while the export emits manchester-united, because
    [team].astro feeds `team.slug` straight into getStaticPaths.
  - 2026-07-28: NOT amended, deliberately — `dbt_project/.sqlfluff`. A nested config exists and
    is the one that applies when linting from dbt_project/, so it would also benefit from the
    jinja macro path. But the root `.sqlfluff` (in scope) is enough to lint from the repo root,
    which is what this PR's verification uses, so adding the nested one would be convenience-
    driven scope creep. Recorded as a follow-up instead.
