# Review — fix/transfers-drop-bl1-hardcode — 2026-06-13

> Issue #420 (audit F1/F2): remove the hardcoded `league_code = 'BL1'` filter from the
> 2_base model base_apif__transfers (competition-agnostic violation); update the stale
> "BL1 only for now" comment in base_apif__players. REAL behaviour change (surfaces all
> leagues' transfers). Required reviewers for dbt_project/**: scope-auditor +
> analytics-engineer-reviewer. Both PASS first iteration against the hash below.

diff_sha256: 2e86fb5ff7c75adc12ee6e7d8ce5f846f4910ae81cd7811ee44378c2777462c7

## scope-auditor
VERDICT: PASS
risks_checked:
- §10 meta-rule (rule enforcement vs reinterpretation): verified CLAUDE.md §8 +
  working_agreement.md §8 prohibit hardcoded competition identifiers in absolute terms
  ("never"), and the contract rests on a recorded CPO "file" ruling (audit 2026-06-12) —
  so removing the hardcode is codified-correct enforcement, not an agent-taken §10 scope
  decision. stg_apif__transfers already handles all leagues, confirming the BL1 filter was
  not a data-quality gate being silently removed.
- Lockstep / scope discipline: confirmed base_apif__players.transfers_src already reads
  ALL of base_apif__transfers (only `player_id is not null`), so fct_transfer and the
  dim_player fallback stay in lockstep across leagues; the diff touches only the two
  declared models + contract (no .yml test edited, no test severity changed, no protected
  path), so no DQ guard is downgraded or hidden. The ERROR-severity player_sk relationship
  in ci-data-build is the authoritative gate.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- player_sk → dim_player lockstep across all leagues: fct_transfer.player_sk =
  cast(player_id as int64) and dim_player.player_sk = cast(player_api_id as int64) both
  derive from the SAME base_apif__transfers (fct directly; dim via transfers_src →
  base_apif__players_global). Any player_id passing the base filter is injected into both,
  so the ERROR-severity relationships test (no where guard, no warn) holds by construction.
- from/to_team_sk → dim_team: both tests are severity:warn + where "...is not null";
  fct_transfer nulls unresolved foreign-league team SKs (CASE WHEN), excluding them from
  the predicate — more leagues = more warns, zero new ERROR failures. transfer_date_sk →
  dim_date is safe (dim_date spans 1900–2101). base not_null/grain tests hold (staging
  guards transfer_date, base guards player_id, qualify guarantees the grain).
- Layer + idempotency + blast radius: base stays a view reading ref('stg_apif__transfers')
  with league_code flowing through; zero hardcoded league_code remains in 2_base (grep).
  fct_transfer is a leaf fact — no mart/intermediate/export/UI consumer (grep), so no
  BL1-assuming downstream silently changes. View re-computes; fct rebuilds idempotently.

## escalations
(none — both reviewers PASS first iteration. DQ proof for the player_sk relationship across
all leagues runs in ci-data-build, the authoritative gate for this behaviour change.)
