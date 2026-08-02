# Review — feat/846-featured-season-from-mart — 2026-08-02

branch: feat/846-featured-season-from-mart
diff_sha256: 9cf5ad7b56af1b22a3808cc77335a98d26ee78024c3ebf7a72f854b61426a1bd
# ⚠ This is the CUMULATIVE `origin/main...HEAD` hash, NOT `--staged-hash`. The two are identical on a
# one-commit branch and diverge the moment a branch has two, because `--staged-hash` covers only the
# increment being committed while CI recomputes over the whole branch (F11). This branch has two
# commits, so the staged value (51b556f6…) would have bound the review to the second commit alone and
# CI correctly refused it. Take this number from `python scripts/check_task_artifacts.py --base
# origin/main`, which is the same code CI runs.

rounds: 5
rounds_cap_override: >
  CPO, 2026-08-02, **"do 1 now"**. Rounds 1-3 were the ordinary loop and closed under the cap.
  Rounds 4 and 5 exist because CI failed AFTER the reviewed commit and the CPO ruled on the fix:
  the DQ test ships one PR later (#886) because the PR-time singular-test step resolves every model
  reference to prod, which has no such column until main-push (#887). Round 4 is that removal, round
  5 is the stale reference it left in `shared.yml` that `analytics-engineer-reviewer` caught. Every
  round found a real defect; none was spent on the review's own paperwork.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed path is covered by `scope_paths`, including the Astro dynamic route, which only
  matches through `site_v2/src/pages/*/teams/*.astro` because fnmatch reads `[lang]`/`[team]` as
  character classes.
- The §10 classification (the pipeline picks the opening season, not the page) is recorded in
  `decisions_taken` with the CPO's 2026-08-02 wording, and the matching entry exists in
  `escalations.log`. Checked the cited ruling is real rather than asserted.
- Acceptance criterion 4's TEXT is unchanged and still locked. What moved is the implementation
  timing, not the criterion: the CPO's "do 1 now" is recorded in `escalations.log` and says what the
  contract says it says.
- Four amendments, all tracing to one honest root cause: `scope_paths` was drafted from the change in
  mind rather than the whole chain it travels. The fourth keeps the deleted test's path IN scope,
  which is correct, because the diff has to be authorised to touch a file in order to delete it.
- Threshold declarations checked against the diff: no new mechanism and no recurring cost.
- Appendix A: logic moves OUT of the frontend and the export INTO the warehouse, the opposite of A5;
  the `impact_map` pastes `dbt ls` output rather than asserting lineage (A6).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- `row_number() over (partition by ...) = 1` in both marts: BigQuery assigns exactly one rank-1 row
  per non-empty partition regardless of NULLs in the ORDER BY, so "two flagged" is unreachable by
  construction. Verified the `shared.yml` comments now claim exactly that and no more: they name the
  construction, and they state plainly that the "never none" case is uncovered until #886.
- No reference to the deleted test survives anywhere in the repo outside the task artifacts, where it
  is the deletion's authority trail rather than a claim of live coverage.
- Fan-out from the two new joins in `mart_player_profile`: `competition_registry.league_code` and
  `competition_types.competition_type` are both `unique` + `not_null` in `seeds/schema.yml`, so
  neither join can multiply rows and the `(player_sk, season_sk)` grain holds.
- `'domestic_league'` and `'club'` are taxonomy values from the registry and the seed, applied for
  every `league_code`, not hardcoded competition identifiers.
- `_featured_season_row` in the export selects on a served flag and raises rather than deriving a
  fallback, which stays inside the consumption-layer contract.
- `entity_type` reaches NULL two ways: an absent league_code, and a registry entry PRESENT with a
  blank `competition_type`, which `sync_dbt_vars.py`, `check_competition_type_seed.py` and
  `check_registry_var_sync.py` all skip on the same `if code and ctype` condition. Verified against
  the scripts. `not_null` on the mart column turns that from a silent mis-scoping into a failing dbt
  test; the registry-side silence is outside `scope_paths` and is filed as #883. Counted
  `docs/competition_registry.yml`: 45 entries, every one carries a `competition_type`.
- `impact_map`'s leaf-mart and sole-consumer claims verified independently by grep.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- `is_featured_season` traces from both marts through `_featured_season_row` and `_strip_identity`
  into the served payload and the `TeamSeason` type. No field is drawn that the data does not carry.
- The committed sample has exactly one `is_featured_season: true` (`PL` / `2025`), and that is the
  row the old `.find((s) => s.competition_type === "domestic_league")` would have returned, so
  acceptance criterion 2 is not contradicted by the sample itself.
- Widening `TeamSeason.is_featured_season` to a required field breaks no other consumer: no other
  committed sample carries a `seasons` array and no component builds a bare `TeamSeason` literal.
- The non-null assertion at `[team].astro:56` fails at BUILD time, not in a visitor's browser.
  Confirmed against `astro.config.mjs` (`output: "static"`, no adapter) and empirically by flipping
  the sample's flag and observing exit 127.
- The rendered-page artifact measures rather than asserts: built HTML byte-identical across de, en
  and fi, before and after. Cross-checked its claims against the repo; nothing contradicts it.

## platform-reviewer
VERDICT: PASS
risks_checked:
- `_mark_featured` mutates fixture dicts in place, but every call site builds its own literal list
  inside its own test function, so there is no cross-test coupling.
- The helper's default reproduces the removed `_latest_season_row` exactly, including tie-breaking,
  so the unchanged assertions prove the payload did not move rather than masking it.
- Both new tests pin the changed behaviour: reverting to recency flips `position` from `"D"` to
  `"M"`, and reverting the raise makes both `pytest.raises` blocks fail.
- Traced the `ValueError` through the call graph and the workflows. `dbt-scheduled.yml` never calls
  the export; the only caller is `deploy-site-v2.yml`, which is `workflow_dispatch`-only, so a bad
  row fails a manual, non-public deploy loudly rather than taking down a live nightly.
- No dependency, workflow or build-config file is touched, so pinning does not apply.
- `import pytest` inside a test function is a style inconsistency, not a defect.

## escalations
- question: The DQ test required by acceptance criterion 4 passes against the branch's rebuilt marts
  but fails the PR-time singular-test step, which runs `--defer --favor-state` and therefore resolves
  every model reference to prod, where the column does not exist until main-push. Two paths were put
  to the CPO: ship the guard one PR later, or fix the CI dataset isolation first. A third option,
  dropping `--favor-state`, was proposed and then withdrawn as a trade rather than a fix, because it
  would let a stale `ci_` table from an unrelated PR feed the DQ gate.
  CPO ANSWER (2026-08-02): **"do 1 now"** — ship the guard one PR later. Criterion 4 stays locked and
  unchanged; its automated half lands in #886 once prod carries the column, and the CI gap is #887.
