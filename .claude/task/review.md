# Review — feat/player-per90-metrics — 2026-06-23

diff_sha256: 8340f2fe4f747585a5cf1556363ba3758c9619d6a348735d47c6eb365b8e15ea

## scope-auditor
VERDICT: ESCALATE
risks_checked:
- Scope-amendment authority — the amendment adds `int_team_season.yml` (non-negative per-90 DQ test) + `mart_player_profile.sql` (stale-comment touch-up); the scope-auditor held (rounds 1-3) that §2 requires the amendment to record CPO authority, not reviewer-FAIL authority. Put to the CPO (two paths: confirm vs drop to a follow-up). See escalations.
- Scope surgical + no other §10 drift — every staged file is in the (amended) scope_paths; the per-90 reintroduction and the direction classification are both recorded in decisions_taken as CPO rulings; the 2 added files are genuine dependencies of the per-90 work.
CPO ANSWER: (a) confirm the scope amendment — the CPO authorizes adding int_team_season.yml (DQ test) + mart_player_profile.sql (comment) to PR1's scope; authority = the CPO's "good now" approval of the plan that named both fixes (durably recorded in escalations.log, conversation 2026-06-23).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Non-negative test completeness — verified `int_player_season_per90_non_negative` lists all 13 per-90 columns with the `col is null or col >= 0` pattern (no dropped null guard), correctly placed on `int_player_season__metrics` within `int_team_season.yml`.
- Drift-guard coverage — all 13 new int columns (incl. `scorer_points_per90`, `defensive_actions_per90`) resolve verbatim to their `metric_id`s under `assert_no_uncatalogued_season_metric`'s normalisation; the catalogue has exactly those 13 player rows; no orphan column or row; numerators correct (key_passes←passes_key, interceptions←tackles_interceptions, blocks←tackles_blocks, saves←goals_saves); blast radius isolated (named-select consumers unaffected).

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- `duels_won_per90 = neutral` while `duels_won_pct = higher_better` — the volume-vs-rate split is football-correct and matches the team precedent (`duels_per_match` neutral / `duels_won_pct` higher_better); the interpretation flags "the win rate captures efficiency" so no false quality signal.
- `saves_per90 = neutral` + `dribbles_success_per90 = higher_better` — a busy keeper's save volume is workload not quality (interpretation discloses it; the save rate carries quality); a successful take-on is a player-initiated output (defensibly higher_better, unlike involuntary defensive volume). All directions consistent with their team analogs; neutral interpretations carry the "style not quality" signal.

## escalations
- question: PR1's two reviewer-fix files (int_team_season.yml DQ test + mart_player_profile.sql comment) are a scope amendment. §2 requires the amendment to record CPO authority. Confirm the amendment (authorize the two files), or drop them from PR1 to a separate follow-up?
  CPO ANSWER: (a) confirm the scope amendment — the CPO authorizes adding both files to PR1; authority = the CPO's "good now" approval of the plan that named the DQ guard + the comment touch-up (conversation, 2026-06-23). Durably recorded in `.claude/task/escalations.log`.

## post-review delta (transparency)
The analytics-engineer + football-analytics PASS verdicts were returned on staged hash
`661080eabb0586ef44aa9764add97e9deec3105921a59cc356c5c490438f3077`. The only change since is the
re-phrasing of the contract's `amendments`-block authority (and this escalation resolution) — a
contract-text-only delta with zero change to the code, metrics, formulas, classifications, or yml that
those two reviewers judged. Their verdicts therefore bind unchanged to the final hash above. The
scope-auditor's concern was resolved by the CPO ANSWER recorded above and in escalations.log.
