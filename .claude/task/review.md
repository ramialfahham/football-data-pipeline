# Review — chore/115-step8-sweep-dbt — 2026-09-11

diff_sha256: ac65b75f4d78738b46dad99a19416651b55efba1b977b1035b4494fe2867b4f7

rounds: 2

analytics-engineer-reviewer: PASS at round 1 (`fcd4ffe5…`), PASS at round 2 (delta).
platform-reviewer: PASS at round 1 (routed by the pin in `tests/test_no_decision_history_in_code.py`);
  the round-2 delta is one wrapped comment line in a dbt model, outside its territory — carried.
scope-auditor: PASS at round 1, PASS at round 2 (delta).

Round 2: CI's SQLFluff (`LT05`, dbt templater) failed one comment line I had made 132 characters
long in `int_legs__team_match.sql`; wrapped onto two lines, same words. All 56 touched SQL files
re-linted for `LT05` locally: zero (only the documented `dbt_utils` templater noise). The
comment-stripping proof re-run on the delta: identical.

### analytics-engineer-reviewer — round 2 (delta)
VERDICT: PASS
- The only change since `fcd4ffe5…` is the one `--` line split into two `--` lines, same words;
  the `events` CTE beneath is untouched; nothing else in the file or the branch changed.

### scope-auditor — round 2 (delta)
VERDICT: PASS
- Delta located on disk and in the patch; no re-introduced marker; both lines remain comments;
  the full 65-file patch re-read — no hunk differs from the reviewed pattern; scope unchanged.

## analytics-engineer-reviewer
VERDICT: PASS (round 1)
risks_checked:
- Full patch read hunk by hunk: exactly 65 `dbt_project/` files (56 `.sql`, 9 `.yml`); no
  `dbt_project.yml`, seed CSV or script in the diff.
- Every comment syntax checked for code leakage — Jinja `{# #}` blocks open and close before code;
  inline `--` beside `case`/`select` leaves the code lines byte-identical; YAML `#` comments leave
  indentation, lists and keys intact.
- `stg_apif__coaches.sql`: deviation, cost (~120 coaches), analogy, downstream contract and the
  `layering.md` pointer survive; only "CPO-ruled this session" and the dated log pointer went.
- Both stale-fact corrections verified against the repo: `scripts/check_raw_freshness.py` reads
  `sources.yml`'s thresholds; `.gitlab-ci.yml` `data:build:mr` runs `dbt seed` before a `dbt test`
  that carries no `--favor-state`.
- `assert_no_event_loss_since_cutoff.sql`: the cutoff-relative wording checked against
  `dbt_project.yml`'s `event_loss_detector_from`; counts and the reproducibility argument intact.
- Every dropped ruling label ("Option A", "floor B2/B3") sits beside the definition it labelled;
  no rewritten sentence claims something the SQL or test does not do.

## platform-reviewer
VERDICT: PASS (round 1)
risks_checked:
- The pin: no Bash in the session, so checked statically — zero marker hits under
  `dbt_project/` for the guard's extensions; 65 files counted by hand in the diff; 850−137=713,
  174−65=109 self-consistent with the evidence's measured (713, 109).
- The two-sided pin test would fail at 850 against a 713 tree, so the pin change is proven
  necessary; a revert of the sweep with the pin at 713 fails the ceiling assert.
- Guard paths untouched (`.claude/hooks/**`, `.gitlab-ci.yml`, workflows absent from the patch).
- ~20 of the 65 files spot-checked: only comment lines change; every test predicate and column
  list byte-identical.
- The stripping method's one blind class named — a change to text after an in-literal `--` on the
  same line — and checked: no such line in this diff.
- `dbt parse` with a scratchpad-only `dev_scratch` profile and no connection is consistent with
  CLAUDE.md's rules.

## scope-auditor
VERDICT: PASS (round 1)
risks_checked:
- Scope exact: 65 dbt files, the test constant, the contract.
- Ten-plus rewrites sampled line by line: rule, number and mechanism retained; only name, date,
  log pointer or round label dropped; nothing softened or hardened.
- Both corrections verified true against the repo and declared in the evidence.
- Evidence quotes the method's actual output (56 + 9 = 65, differing: []); the pin arithmetic
  matches the test file; the `impact_map` claim is evidenced by that output plus `dbt parse` and
  `check_layer_contract.py`.
- No mechanism, cost, credential; `decisions_reserved` untouched — only the five markers swept.
- Editorial note, not a defect: `assert_mart_team_leaderboards_one_leader_per_league.sql` dropped
  a GitLab pointer where a sibling kept one — per-file judgement assigned to the analytics engineer.

## escalations
- None.

## Found and NOT fixed, all disclosed in the contract
- The remaining 713 lines — three more sweeps (tests + hooks + scripts; `site_v2`; ingestion +
  design-mocks).
- The stripping method's in-literal `--` blind spot: not exploitable here; the method stays a
  proof for comment-only diffs, not a general equivalence check.
