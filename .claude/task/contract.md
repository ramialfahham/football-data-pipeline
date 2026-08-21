# Task contract — #82 MR1: object-level description coverage

objective: >
  Close the object-level half of #82: every model, every seed and every SOURCE TABLE must carry a
  description, and a gate must keep it that way. Twelve things have none today — 11 of 11 source
  tables, and `int_team__market_value_latest`.

  This is the unambiguous half, deliberately taken first. There is no judgement call in "does this
  object have a description at all", so it ships without waiting on the column work, which is
  hundreds of definitions and several more MRs.

  `check_description_hygiene.py` checks the CONTENT of descriptions that exist. Anything with NO
  description passes it silently. Presence has never been checked at all.

refs: >
  Authority: `.claude/task/escalations.log`, the 2026-08-21 `feat/description-coverage-objects`
  entry — four CPO rulings plus a correction of this file BY the CPO. Plan file:
  `C:\Users\Rami\.claude\plans\cozy-orbiting-quail.md`. GitLab #82.
  Standard: `dbt_project/docs/engineering_standards.md` §2, whose Coverage section already
  requires exactly this and has never been enforced.
  Branched from main `e6c1819`, no open MRs.

impact_map: >
  Small blast radius, and deliberately so. This MR adds PROSE to a source file and one model's
  yml, plus one rule to an existing offline gate. It changes no SQL, no config, no materialisation
  and no CI job.

  1. THE GATE gains an object-level presence rule and therefore a new way for a turn and a pipeline
     to go red: adding a model, seed or source table without a description now fails. That is the
     point. It runs in `validate:governance` and in `stop_gate.py`'s FAST_GATES, both of which
     already invoke this script, so NO new wiring and NO protected-path edit is needed.
  2. GREEN ON DAY ONE is required, the `check_copy_gate.py` precedent: the twelve findings are
     fixed in this same MR, and the gate is run repo-wide before it is trusted.
  3. SOURCE DESCRIPTIONS ARE NOT PUSHED TO BIGQUERY. dbt does not create sources, so `persist_docs`
     never touches them and no BigQuery length limit applies. The gate's own limits still do.
  4. `int_team__market_value_latest` is a VIEW over `fct_team_market_value_snapshot`, which holds
     0 rows in production. Describing it changes nothing about what it returns.

scope_paths:
  - dbt_project/models/1_staging/api_football/sources.yml
  - dbt_project/models/4_intermediate/shared/team/int_team_market_value.yml
  - scripts/check_description_hygiene.py
  - tests/test_description_hygiene.py
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/active_work.md

decisions_taken: >
  CPO, 2026-08-21, "every column, no exception" — the coverage rule takes no exemption list.
  Object level is the unambiguous subset of that and is what this MR enforces.
  CPO, 2026-08-21, "thin fillers should not happen ... starting in core we are applying our
  definitions alongside what the provider gives us as descriptions, information upstream so we use
  it downstream where applicable." The twelve descriptions here are written from what the staging
  models and `docs/data_contract.md` already establish about each raw table, not invented.

decisions_reserved:
  - COLUMN coverage is NOT enforced here. It is 1,236 columns across four later MRs, and turning
    the rule on before the content exists would put main red — the inverse of the
    `check_copy_gate.py` precedent this repo already set.
  - The append-only declaration script (plan MR2) is not built here and is not approved by this
    contract.
  - Whether a model with no populating process should exist at all is the CPO's.
    `int_team__market_value_latest` is DESCRIBED here, not deleted and not defended; its emptiness
    is stated as a known limit and the question is raised in `escalations.log`.
    ⚠ THREE FACTS FOUND WHILE DESCRIBING IT, none of them fixed here.
    (a) It is declared in NO yml at all — that is WHY it has no description — so this MR creates
        `int_team_market_value.yml`. The path follows the existing subdirectory precedent
        (`domestic_league/matchday/int_matchday.yml`), not a new convention.
    (b) It therefore has NO schema test either, which §3 requires of every model. NOT fixed here:
        the table has 0 rows, so any test added today would pass vacuously by construction, and
        this repo has already shipped vacuous tests once. It needs data first, or a deliberate
        decision that the model goes.
    (c) The emptiness is not contained: `mart_team_market_value.sql` reads this model, so an empty
        fact reaches a MART. Raised, not chased.
  - ⚠ A FLAG OF MINE THAT WAS FALSE, WITHDRAWN. An earlier version of this bullet claimed
    `RAW_APIF_LEAGUES` is "absent from the raw table inventory in `docs/data_contract.md`", the
    same shape as the recorded gap for COACHES and INJURIES. IT IS NOT ABSENT.
    `docs/data_contract.md:65` carries "Additional smaller table: `RAW_APIF_LEAGUES` (same append
    schema, no `fixture_id`)", and it appears twice more in the endpoint tables. That file even
    explains at lines 39-42 why it sits outside the main grain table, and records the history of
    the ambiguity.
    HOW I GOT IT WRONG, because the method matters more than the fact: I grepped only the ROWS of
    the grain table, saw no match, and reported an absence as a gap. That is trap 1 of the
    handover, a too-narrow grep reported as a clean sweep, committed inside the MR whose subject
    is claims nobody checked. Surfaced by scope-auditor and verified before withdrawing.

done_when:
  - All 11 source tables carry a description stating what the payload holds, its grain (what ONE
    row is), and its known limits. Measured from the manifest, not counted by eye.
  - `int_team__market_value_latest` carries a description that states its emptiness as a limit.
  - The gate fails when a model, seed or source table has no description, and the rule is SEEN RED
    on a realistic omission before it is trusted (#904). A passing gate proves nothing.
  - The gate is green repo-wide BEFORE the rule is relied on, so main never goes red.
  - `dbt parse` clean; `python -m pytest tests/` at its measured baseline plus the new tests.
  - The five offline gates pass, read from their OUTPUT and not their exit code.
  - Handover updated in the SAME commit as the code.

amendments:
  - >
    1. TWO FALSE CLAIMS OF MINE, BOTH CORRECTED, and both found by review rather than by me.
    Recorded here rather than quietly fixed, because this MR's entire subject is descriptions that
    asserted something nobody had checked, and I produced two of them while writing it.

    (a) THE SERIOUS ONE, caught by analytics-engineer-reviewer's round-1 FAIL. The
    `raw_apif_fixture_details` description I wrote ended "several rows can describe the same
    fixture and the newest is the fullest". That is FALSE and actively dangerous: a stranger would
    take the newest row per fixture and silently lose data. `docs/data_contract.md:134` states the
    opposite — "Both versions are kept deliberately, and base picks per entity ... a retry chasing
    late statistics can come back richer in one section and poorer in another" — with fixture
    1564795 yielding 27 events of which indices 17-26 come from the payload the retry would have
    replaced. `base_apif__fixture_events.sql:25` confirms it in code, deduping per
    `(league_code, fixture_id, event_index)` rather than newest-row-wins, which only makes sense
    BECAUSE the newest row is not the fullest. The description now says no single row is reliably
    fullest, that versions must be resolved per entity, and that `fixture_id` is not unique here.
    ⚠ THE LESSON IS NOT "check harder". I wrote that sentence by compressing a staging model's
    description without reading the section of the data contract that governs it. Inheriting text
    from upstream, which is exactly what the CPO's "information upstream so we use it downstream"
    ruling asks for, carries an INHERITED-ERROR risk that inventing text does not. Reuse still
    needs verification at the point of reuse.

    (b) `RAW_APIF_LEAGUES` — see `decisions_reserved`. A flag raised from a too-narrow grep and
    withdrawn.
  - >
    2. ONE REVIEWER NOTE ADOPTED, from platform-reviewer's PASS. The gate's success line globbed
    the model and seed trees a THIRD time for its printed counts and omitted the `dbt_packages/`
    exclusion the enforcement path uses. Cosmetic today, since nothing nests there, but it is two
    definitions of "which files count" that can drift — the same shape as the duplication this
    programme exists to remove. Replaced with one `_on_disk()` helper used by both the check and
    the census, so the number printed cannot diverge from the number enforced.
