# Review — feat/143-home-approved-design — 2026-09-13

diff_sha256: 4c02be902423766df9216cebeeb7af3a756aadf6758d0df2c798f7c857cf14ed

rounds: 3

Rounds are per reviewer. Round 1: four reviewers on the round-in-the-export design; three PASS,
analytics-engineer-reviewer FAIL (the round selection in the export's SQL is window selection in
the consumption layer; GAP-32 had left the classification unsettled). Escalated blinded to the CPO
with two paths; he ruled "Path A" (2026-09-13, in chat): the warehouse serves the next matchday.
Round 2: `mart_next_matchday` + singular test + export read + doc corrections; all four re-run;
three PASS, analytics-engineer-reviewer FAIL on one stale line (`10_home.md` GAP-register summary
still said the export selects the matchday). Round 3: that line struck, class swept (no other
live "export decides" claim in docs/, dbt_project/docs, scripts, site_v2/src);
analytics-engineer-reviewer PASS. The patch and hash were regenerated before every round.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 2 (full re-run on the Path A diff): every changed file is in `scope_paths`; the three
  files new since round 1 (`mart_next_matchday.sql`, its singular test, `FixtureRow.astro`) carry
  dated amendments with their authority. The mart computes exactly what Path A ruled and no
  wider (no cap, no ordering, no extra columns). The mart's name is disclosed as the builder's
  proposal in the contract and the MR head, not silently taken. Doc-sync: `layering.md`,
  `site_architecture.md`, `99_gaps_register.md`, `10_home.md`, `00_overview.md` all updated in
  the branch. Impact map evidenced (`dbt ls` outputs, two-sided `>= 3` sweep 2/6, prod counts,
  mutation-tested singular test). Paperwork (`acceptance_evidence.md`, `rendered_page_evidence.md`,
  `active_work.md`) describes the round-2 design, no round-1 framing left. No credential-shaped
  content. A new shared mart on the layer default materialisation is ordinary consumption-layer
  work under the no-new-model rule (per-competition files), no new recurring job — no threshold
  crossing.
- Round 1 (round-in-the-export design): PASS on the same checks; superseded by round 2.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 3: `10_home.md:1102-1105` GAP-32 bullet struck and replaced with the CLOSED note; swept
  docs/, dbt_project/docs/, scripts/, site_v2/src/ for any live claim that the export selects,
  decides or chooses the matchday — none besides the struck line and the artifact-only tracker
  snapshot; `mart_next_matchday.sql` holds the round selection; `export_site_data.py:1477-1485`
  is a plain select with no `min(fixture_date)` or round logic; `99_gaps_register.md` GAP-32
  consistent with the wireframe.
- Round 2: layer placement — a mart composing `fct_fixture` with a `qualify row_number()` window
  is the established pattern (`mart_team_fixtures`, `mart_player_season_record`,
  `mart_team_season_record`, `mart_fixture_standing_context`, `mart_matchday_insights`, the two
  leaderboard marts); grain and tests adequate (`fixture_sk` unique/not_null/relationship,
  not_null on round, date, league, season); the singular test re-derives the expected round from
  `fct_fixture` independently of the mart's CTEs and checks one round, the earliest, complete,
  every league present — catches a drifted rewrite, not a tautology; `current_date()` in a
  nightly table is an established pattern; the export read is a plain select pinned by the unit
  test; no new ratio, metric or per-competition literal. Verdict then: FAIL (resolved at round 3)
  on the one stale GAP-32 line.
- Round 1: `mart_team_leaderboards` gate `>= 3` → `>= 1` with the yml test and descriptions
  moved together, a guard narrowed not deleted; two-sided sweep confirmed — the six benchmark /
  deserved-vs-actual gates untouched; leaf mart per the `dbt ls` output. Verdict then: FAIL
  (resolved at round 2) — the round selection in the export's SQL, a materially larger
  computation than the `min()` GAP-32 had registered, with the classification unsettled.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 2: the export read uses `{GCP_PROJECT}.{MARTS_DATASET}.mart_next_matchday`, identical to
  every other mart read in the file; the rewritten unit test fails against the pre-branch export
  (no captured SQL names the mart → `StopIteration` in the call phase, a failure) and its
  substring check has no false-positive risk against the actual column and table names; the
  test's shape assertions match `group_upcoming_fixtures` and the kickoff sort; the mock
  generator and checker are unchanged since round 1. Noted the mart as re-run safe (a
  deterministic function of `fct_fixture` and `current_date()`); ⚠ the reviewer called it a
  view — it is a TABLE on the marts layer default, which changes nothing about the safety claim.
- Round 1: the round-1 export query traced (row_number one row per league, 1:N join, no
  fan-out); the round-1 test discriminating against `main`; `gen_home.py`/`check_home.py` counts
  trace to the hard-coded `FIXTURES` literal (deterministic regeneration), UTF-8 declared on every
  read/write, `home_mock.html` gitignored; code comments carry bare issue numbers only; evidence
  claims consistent with the diff; no dependency, credential, CI-guard or hosting file touched.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 2: binding chain end to end — `10_home.md` §3 and §5(1) bind `upcoming[]` to
  `mart_next_matchday`; `site_architecture.md`'s landing row agrees; the export selects every
  field `group_upcoming_fixtures` consumes and the mart carries them all; `types.ts` shapes match
  the payload and are unchanged; the only remaining `core.fct_fixture` read in the export is the
  unrelated fixture-page payload; the three `fct_fixture` mentions left in `10_home.md` are struck
  or labelled historical; GAP-32's closure claim matches the code; `metrics_display.md` (LOCKED)
  has zero hits in the patch; the mart's "table" entry in `layering.md` matches the project
  default with no per-model override.
- Round 1: every field `FixtureRow.astro` renders exists on `LandingFixture`; `round` is served but
  deliberately not rendered (the "NO ROUND" passage, #866, still true); the 3-row cut is
  presentation of a served, kickoff-ordered, uncut list; `homeShowAll` present in EN/DE/FI with
  `{n}` matching `t()`'s substitution; the wireframe corrections are targeted strikes, no
  leftover passage asserting the one-day window or the `>= 3` team gate; rendered evidence read
  and used (31/232, max 3 outside `<details>`, 18 folds, translated summaries, geometry, script
  count, production build with the sample).

## escalations
- question: who decides which round is a competition's "next matchday" — the warehouse, or the
  export script that builds the page data? Path A: a small new mart, nightly, tested, the export
  only filters (closes GAP-32); Path B: extend the 2026-08-18 "ship as is, register the gap"
  ruling to this shape. Recommendation given: A.
  CPO ANSWER: "Path A" (in chat, 2026-09-13). Recorded on #143 (note) and in the contract's
  amendments; #127's block-1 data line updated.
