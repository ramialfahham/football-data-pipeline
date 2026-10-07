# Review — feature/177-form-window-values — 2026-10-07

diff_sha256: 2a59b0c3747f2e7af501258edd8fdfca380a1e6db4b2f25206863112960f1296

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every file in the diff is in scope_paths; the season chain and the two test files each carry a dated amendment with the CPO's authority.
- Decision rights: the 15 rows' text (label_en, description, interpretation, direction, tier) is recorded as approved in chat, 2026-10-07; the displayed names (strings.ts) stay reserved for the page build.
- Impact map: the full 51-model dbt ls list is pasted; the measured zero difference on the two existing tables is recorded; the blast radius names the w1 payload growth.
- Rename: passes_share_pct is consistent across seed, map, docs, ymls, generator and both generated blocks.
- Thresholds: no new mechanism; the nightly-bytes measurement is owed before merge.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Formula test: the legs CTE no longer joins player-summed fouls, so fouls resolves to the team line.
- Season chain: the 15 new columns are documented on both season models, with range and non-negative tests.
- Cleaning: free_kicks is covered by the blank-rule test and the base-to-core equality test.
- Generated SQL: each new expression matches its catalogue row, gated by rule R4, ratios sum over sum.
- Layer placement and competition-agnostic: no defect.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Possession: the pass share is passes_share_pct, so possession_pct keeps meaning the provider's time-based value in core.
- Formulas: every numerator is part of its denominator; every count uses an existing leg column.
- Descriptions and interpretations: plain, one sentence, matching the formulas.
- Direction: follows the all-else-equal rule; blocked shots higher_better confirmed with the CPO.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Formula test collision fixed; no other tm.* join collides.
- free_kicks fill and core carry are pinned by tests; a revert fails CI.
- Payload: form_window gains nothing; w1 gains 16 keys, about 1.3 KB per file, disclosed in the contract.
- Generator: idempotent, no duplicate ids, drift test covers a revert.

## escalations
(none)
