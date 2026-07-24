# Review — feat/team-squad-tab — 2026-07-24

diff_sha256: 024b6f7e300844262898bfa183d7de3514136649d70fd8cf67de61f5c2151d20

rounds: 5

rounds_cap_override: CPO authorised closing the doc-reconciliation sweep and shipping — AskUserQuestion
2026-07-24, "Fix the 3 lines, then ship". The rounds past 3 were NOT code churn: the Squad-tab code
(export join, frontend, sample, tests, absent-state) passed early and is unchanged; rounds 2-5 were
the bi-analyst finding the stale "identity-only squad" doc claim in successively more files
(wireframes -> gaps register -> design brief -> the wireframe status index -> content_architecture ->
three dbt mart docs -> the component-census rows), i.e. one prose class swept to completion.

> PR-B: the team page Squad tab (mock f6348775). Export joins mart_player_career onto each roster
> member (selection only); TeamSquad.astro renders position groups (GK->DEF->MID->FWD->Other), rows
> by appearances desc, monogram avatars, a two-line stat readout; 33.json re-exported (real output);
> types + i18n (de/en/fi); absent-state split (no-roster vs nobody-played). Plus a tree-wide doc
> reconciliation of the now-superseded "identity-only squad" framing.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is within the (thrice-amended) scope_paths; all three amendments are recorded
  with authority (reviewer findings + the CPO ship ruling). No undeclared file; no warehouse/seed/logic
  change smuggled into the doc reconciliation.
- No unilateral §10 decision: position->group mapping, build-time age, and "show >= 1 appearance, N of
  M caption" all implement the CPO-approved mock; no new metric (minutes_per_appearance was catalogued
  in the prior PR); the doc edits are reconciliation to shipped behaviour, not new product decisions.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Export is SELECTION/JOIN only: career stats read from mart_player_career via career_by_key keyed
  (league_code, season_api_year, player_sk) — unique because career_rows are pre-scoped to one team_sk
  in the fetch; verified against the mart's (player_sk, team_sk, season_sk) grain and the new test that
  plants a decoy prior-season row and asserts no leak. mins/app read from the mart column, never divided.
- The re-exported 33.json is genuine output (both null-safety edge cases faithfully present;
  full-float-precision values; unrelated scatter/benchmark drift consistent with a real re-run) — the
  #805 binding rule holds.
- The dbt doc/comment reconciliation (layering.md, mart_roster.sql, shared.yml) is prose only: no SQL,
  schema, test, materialization, or grain change; mart_roster's SELECT is verified stat-column-free, so
  "no per-club stat columns of its own" is accurate.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Binding rule: every field TeamSquad renders (appearances, minutes_per_appearance, goals, assists,
  name, position, nationality, birth_date) exists in the committed 33.json squad members — nothing
  drawn that the data does not supply. Age is a build-time display derivation (pre-endorsed pattern,
  mart_roster schema), null-safe.
- Formatting/i18n: singular/plural correct (1 goal vs 2 goals; 1 app vs apps) in all three locales;
  position group headers plural + localized; the two-line `.pstat` scoped to `.squad` so the fixture
  PlayerRow is untouched; absent-state split (squadUnavailable vs squadEmpty) present in de/en/fi.
- No live description anywhere presents the Squad tab / squad row as identity-only or stats-deferred:
  a tree-wide substance sweep (docs/ + dbt_project/ + scripts + site_v2) found only dated/struck
  historical annotations; the /players/squads RAW-ingestion mentions and the mart-accurate "no stat
  columns" statements are a different layer, correctly left.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Nothing in the platform/build/tooling surface changed since the earlier PASS: no guard/CI/dependency/
  workflow path in the diff (enumerated all changed files); scripts/export logic unchanged (only three
  stale comments reworded); TeamSquad.astro/system.css/tests match the contract's done_when.
- TS/template soundness + scoped CSS confirmed earlier and unaffected; the JS-free tab still resolves
  for the swapped Squad panel; astro build clean across de/en/fi; the delta since is documentation only.

## escalations
- question: reconcile the design docs now, or take the plan's "doc follow-up" deferral?
  CPO ANSWER: finish the Squad tab first, reconcile now (AskUserQuestion 2026-07-24, "Finish Squad tab
  first").
- question: only stale wording in dbt mart docs remains and the review round cap (3) is hit; how to
  proceed? CPO ANSWER: "Fix the 3 lines, then ship" (AskUserQuestion 2026-07-24) — authorises the
  round-cap override recorded above.

## follow-ups (non-blocking, recorded so they are not lost)
- content_architecture.md:83 cites "GAP-22" for the squad-stats resolution; GAP-22 is the Player
  Career screen's gap — the squad-stats resolution is under GAP-20's ruling. A wrong internal
  cross-reference (not fan-facing); fix in the deferred doc cleanup.
- The whole-site em-dash / AI-tell display-text sweep is a separate CPO must (spawned task) — not this PR.
