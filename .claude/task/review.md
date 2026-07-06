# Review — chore/655-campaign-is-season-note — 2026-07-06

> G3 Lock artifact. #655: remove the stale "multi-season national qualifier campaigns are a separate follow-up"
> deferral notes from the two season-record model docstrings (int_team_season_record + int_player_season_record),
> replacing them with a one-line statement that a qualifying campaign is one season_api_year already cumulated by
> the (league_code, season_api_year) partition. CPO ruling (#655): "the campaign is the season" — confirmed in the
> data (each WCQ campaign carries one season_api_year). Comment/doc-only; compiled SQL byte-identical.
> Required set (routing): scope-auditor (always) + analytics-engineer-reviewer (dbt_project/**).
> (Redone in the primary tree off main @ 81eb1ed after a concurrent session cleared; earlier PASS runs on the
> byte-identical model edits are superseded by these fresh verdicts bound to the current hash.)

diff_sha256: 7cade53e73c1be33bb67c787b7fc9bda45ee417061ac5d51302b5474fa701239

## scope-auditor
VERDICT: PASS
risks_checked:
- **Docstring truthfulness under temporal edge cases.** Verified "this partition already cumulates the full
  campaign" is a factual statement about the partition's SCOPE (all rows with that season_api_year), not an
  implicit coverage-completeness claim — it correctly allows mid-campaign gaps / API lags (permitted by soft
  ingest gates); the cumulation is mechanical and holds regardless of lag/gap patterns. No overclaim.
- **"Matching the momentum qualifiers window" — outcome vs mechanism.** Confirmed the team docstring uses
  outcome-parity language ("matching"), not mechanism identity; the parenthetical ("the provider stamps a whole
  campaign with a single season_api_year") signals the different mechanism (partition key) while justifying the
  same outcome, and the §4 reference is verifiable. Scope (contract.md is now the #655 one; both models ⊆
  scope_paths; nothing smuggled), §10 (record-only, no new decision), and Appendix A (A1–A6 clean) all hold.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- **Comment-only scope.** Read both full model files end-to-end; the diff hunks fall entirely within the `{# #}`
  blocks and every subsequent line (CTEs, select columns, both window clauses w/w_seq, config, refs) is unchanged;
  `int_season_record.yml` needed no update (no test encoded the removed "separate follow-up" language).
- **Substantive correctness.** Verified against competition_registry.yml (all seven WCQ* entries carry exactly one
  `current_season` scalar, season_type calendar_year) and the model bodies (no competition_type/entity_type filter
  or extra branching beyond the stated (…, league_code, season_api_year) partition), consistent with
  metrics_context_model §4's qualifying-campaign row — the "single season_api_year cumulates the whole campaign"
  claim is structurally true, not merely asserted.
- **Mechanism-vs-outcome.** Read int_team_momentum_window.sql in full; its qualifier window is parent-competition-
  keyed and explicitly uncapped/cross-season (no season_api_year partition), structurally different from the
  season-record single-partition cumulation — so the docstring's "matching" phrasing supports OUTCOME parity only,
  no mechanism-identity overclaim.

## escalations
- None open. No ESCALATE verdict raised. Record-only: removes a stale note per the CPO's #655 ruling; the corrected
  wording states behavior the data + §4 already imply. The WCQEU date example is a session data check (registry
  corroborates the single-season structural claim); no CPO-class decision taken.
