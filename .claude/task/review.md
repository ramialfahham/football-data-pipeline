# Review — feat/846-featured-season-from-mart — 2026-08-02

branch: feat/846-featured-season-from-mart
diff_sha256: b85aa3ff20a527d058e40af2f9f918b0e422a11a9a3aa4e76b1b4ae4abc4b511
rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is covered by `scope_paths`, including the Astro dynamic route, which only
  matches through `site_v2/src/pages/*/teams/*.astro` because fnmatch reads `[lang]`/`[team]` as
  character classes.
- The §10 classification (the pipeline picks the opening season, not the page) is recorded in
  `decisions_taken` with the CPO's 2026-08-02 wording, and the matching entry exists in
  `escalations.log`. Checked that the cited ruling is real rather than asserted.
- The five acceptance criteria are unchanged from the approved set and remain locked.
- All three amendments cite real authority: criteria 4, 5 and 2 for the first two, a routed
  reviewer's finding for the third. Verified the third by ordering, not by claim: the artifact was
  rewritten after the amendment was recorded. The contract states one root cause for all three,
  which matches the pattern of each.
- Threshold declarations checked against the diff: no new mechanism (a boolean column on an existing
  mart is not a new warehouse object class) and no recurring cost (no new run, API call or reviewer).
- Appendix A anti-patterns: logic moves OUT of the frontend and the export INTO the warehouse, which
  is the opposite of A5; the `impact_map` pastes `dbt ls` output rather than asserting lineage (A6).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- `row_number() over (partition by ...) = 1` in both marts: BigQuery assigns exactly one rank-1 row
  per non-empty partition regardless of NULLs in the ORDER BY, so "two flagged" is unreachable by
  construction and "none" only if the entity has no row in the mart at all.
- Fan-out from the two new joins in `mart_player_profile`: `competition_registry.league_code` and
  `competition_types.competition_type` are both `unique` + `not_null` in `seeds/schema.yml`, so
  neither join can multiply rows and the `(player_sk, season_sk)` grain holds.
- `'domestic_league'` and `'club'` are taxonomy values from the registry and the seed, applied
  uniformly for every `league_code`, not hardcoded competition identifiers.
- `assert_one_featured_season_per_entity.sql` is valid BigQuery and catches both zero and two for
  any entity present in the mart.
- `_featured_season_row` in the export selects on a served flag and raises rather than deriving a
  fallback, which stays inside the consumption-layer contract.
- `entity_type` reaches NULL two ways, not one: an absent league_code, and a registry entry PRESENT
  with a blank `competition_type`, which `sync_dbt_vars.py`, `check_competition_type_seed.py` and
  `check_registry_var_sync.py` all skip on the same `if code and ctype` condition. Verified against
  the scripts. `not_null` on the mart column converts that from a silent mis-scoping into a failing
  dbt test; the registry-side silence is outside this task's `scope_paths` and is filed as #883.
  Counted `docs/competition_registry.yml`: 45 entries, every one carries a `competition_type`.
- `impact_map`'s leaf-mart and sole-consumer claims verified independently by grep over
  `dbt_project/models/`.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- `is_featured_season` traces from both marts through `_featured_season_row` and `_strip_identity`
  into the served payload and the `TeamSeason` type. No field is drawn that the data does not carry.
- The committed sample `site_v2/src/data/teams/33.json` has exactly one `is_featured_season: true`
  (`PL` / `2025`), and that is the row the old `.find((s) => s.competition_type === "domestic_league")`
  would have returned, so acceptance criterion 2 is not contradicted by the sample itself.
- Widening `TeamSeason.is_featured_season` to a required field breaks no other consumer: no other
  committed sample carries a `seasons` array and no component constructs a bare `TeamSeason` literal.
- The non-null assertion at `[team].astro:56` fails at BUILD time, not in a visitor's browser.
  Confirmed against `astro.config.mjs` (`output: "static"`, no adapter), and confirmed empirically in
  `rendered_page_evidence.md` by flipping the sample's flag and observing exit 127.
- The rendered-page artifact is specific to this branch and measures rather than asserts: built HTML
  byte-identical across de, en and fi, before and after. For "nothing a visitor sees changes" that is
  stricter than a screenshot, since identical bytes fix every viewport and every string at once.
  Cross-checked its claims against the repo rather than taking them on faith; nothing contradicts it.

## platform-reviewer
VERDICT: PASS
risks_checked:
- `_mark_featured` mutates fixture dicts in place, but every call site builds its own literal list
  inside its own test function; no module-level or shared fixture object exists in the file, so there
  is no cross-test coupling.
- The helper's default reproduces the removed `_latest_season_row` exactly, including tie-breaking,
  so the unchanged assertions really do prove the payload did not move rather than masking it.
- Both new tests pin the changed behaviour: reverting to recency flips `position` from `"D"` to
  `"M"`, and reverting the raise makes both `pytest.raises` blocks fail.
- Traced the `ValueError` through the call graph and the workflows. `dbt-scheduled.yml` never calls
  the export; the only caller is `deploy-site-v2.yml`, which is `workflow_dispatch`-only. So a bad
  row fails a manual, non-public deploy loudly rather than taking down a live nightly. Fail-closed is
  the correct direction for a data-validity gate.
- The new singular test is covered by CI: `ci-data-build.yml` runs `dbt test --select
  test_type:singular` on PR and on main, and `dbt-scheduled.yml`'s nightly `dbt build` runs it too.
  `dbt_project/models/**` and `dbt_project/tests/**` both trigger that workflow, ruling out a
  deploy-order race where the export meets a mart without the column.
- No dependency, workflow or build-config file is touched, so pinning does not apply.
- `import pytest` inside a test function is a style inconsistency, not a defect; recorded, not raised
  as a FAIL, because it cannot fail.

## escalations
(none)
