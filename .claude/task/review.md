# Review — refactor/seed-prose-on-goal — 2026-09-01

diff_sha256: f5ac2829b70b649bd3bbdf28666660179a080050a0d49d3935fbbbf2e62d8626

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Recomputed §3's blocker table against the seed directly, not from the contract's prose: all 9
  blocking-phrase sites across the 7 named split rows verified — «on-target shots» ×4,
  «on-target threat» ×3, «on-target dominance» ×1, «on target for − against» ×1. Every site matches
  the seed's actual text; no phantom and no missing site.
- Verified "deciding the first three frees 6 of 7": six rows are blocked only by phrases in the
  first three categories; `shots_on_goal_difference_per_match` additionally needs the fourth in its
  own description. True as stated.
- Verified `deserved_points` is correctly EXCLUDED from the 7 (its `label_en` carries no phrase at
  all, so nothing in the row disagrees) and correctly grouped with `saves_pct` and
  `deserved_points_gap` as held-but-not-split. Checked all three field-by-field: every field that
  mentions the phrase agrees on "on target", and each row pairs a movable noun phrase with an
  immovable bare modifier — which is exactly why §2 holds them rather than partly converting.
- Verified the two "blocked in DESCRIPTION, not interpretation" rows against the seed — both carry
  "on-target shots" in `.desc`, confirming the correction to round 2's wrong claim.
- Cross-checked the diff against the seed: exactly 5 occurrences change across exactly 4 rows, and
  `metric_columns.md` regenerates only for the two whose `description` changed (the generator
  renders `description` only — confirmed by reading the unaffected `saves_player` /
  `saves_player_pct` doc blocks), so there is no doc-sync gap.
- Verified both cited rulings in `escalations.log` BY CONTENT: RULING 2 ("…should be Ø Shots on goal
  (apply everywhere where applicable)", scope "in the catalogue") and the "Both columns
  (recommended)" steer are present verbatim as quoted; the `check_copy_gate.py` quote matches that
  script's actual docstring.
- Scope and protected columns: the diff touches only the four files in `scope_paths`;
  `metric_id`, `label_en`, `label_i18n_key` and every other protected column are byte-identical —
  spot-checked that `shots_on_goal_per_match.label_i18n_key` still reads
  `metrics.shots_on_target_per_match.label`.
- ROUNDS 1–2 (both FAIL, superseded): round 1 caught the per-cell rule splitting `shots_on_goal_pct`
  against itself — the state the CPO's two-column steer existed to prevent. Round 2 caught the
  reserved-decision list being written from memory: it claimed four phrases freed all 7 rows, put
  every blocker in the `interpretation`, and included `deserved_points`, which is not split at all.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Confirmed the seed and generated-doc hunks in `review_input.patch` are unchanged from the round-2
  PASS — same 4 rows / 5 field edits, no new or moved data hunk; `escalations.log` appends only
  (offset 7378+), no retroactive edits to prior log content.
- Independently re-derived §3's blocker table from the live seed rather than trusting the prose: all
  four buckets and every site match — «on-target shots» ×4 (`finishing_efficiency_pct`.desc,
  `finishing_efficiency_player_pct`.desc, `shots_on_goal_against_player`.interp,
  `shots_on_goal_difference_per_match`.interp), «on-target threat» ×3, «on-target dominance» ×1,
  «on target for − against» ×1. "Deciding the first three frees 6 of 7" checks out — only
  `shots_on_goal_difference_per_match` needs the fourth, being blocked in both fields.
- Verified the 3 rows named held-but-NOT-split (`saves_pct`, `deserved_points`,
  `deserved_points_gap`) — each spells the phrase consistently across every field that carries it,
  so "not split" is factually correct and distinct from "held" under §2.
- Verified §1a's detector counts against the file: exactly 3 `on_target`/`OnTarget` identifier
  occurrences exist, all in `label_i18n_key` (rows 13, 34, 65), matching "permissive 3 → prose-only
  0"; and `deserved_points`' description does quote `shots_on_goal_difference_per_match` verbatim,
  confirming the `on[ _-]?goal` false positive.
- No acceptance criterion reads as weakened relative to round 2.
- ROUND 2 (PASS, superseded): reconstructed main-vs-head per row from the patch — 2 genuine fixes,
  2 no-conflict moves, **0 newly split**; recounted 34 remaining occurrences and 3 protected
  directly over the seed; confirmed `finishing_efficiency_pct` the sole pre-existing mixed cell;
  confirmed the generator keys off `description` only, so interpretation-only rows correctly produce
  no doc diff; confirmed the consumer inventory is exactly the three the contract claims.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Confirmed the catalogue diff against the live seed: the 4 changed rows
  (`shots_on_goal_pct`, `saves_player`, `saves_player_pct`, `shots_on_goal_per90`) carry the same
  5 substitutions as round 2 and no other row differs from main — a delta review, not a full one.
- Re-derived the 7 still-split rows directly from the seed rather than trusting the contract:
  `shots_on_goal_per_match` (13), `finishing_efficiency_pct` (14), `finishing_efficiency_player_pct`
  (15), `shots_on_goal_player` (34), `shots_on_goal_against_player` (53),
  `shots_on_goal_difference_per_match` (75), `shots_on_goal_against_per_match` (76). Matches §3
  exactly; the memory-written list's three errors are gone.
- Verified the two DESCRIPTION-side blockers by reading raw text: rows 14 and 15 both block on
  "…not finishing the team's/player's own on-target shots" in `description`, not `interpretation`.
- Verified `shots_on_goal_difference_per_match` carries two INDEPENDENT blockers in two fields —
  description "(on target for − against)" and interpretation "On-target dominance" — so §3's
  separate listing is not double-counting.
- Checked the §2 row rule against `shots_on_goal_against_player`: its description phrase is
  individually movable but correctly held, because the row's interpretation stays blocked.
- Football-validity of the two new contract claims: "on-goal threat" is not idiomatic football
  English (real usage is "on-target threat" or plain "goal threat"), and there is no "off-goal"
  counterpart to "off-target". Both hold as language claims, not cover for skipping a fix.
- Confirmed the wording decision is correctly reserved to the CPO under `check_copy_gate.py`'s
  stated scope — sentence-level phrasing, not a metric-definition or direction change.
- ROUND 2 (PASS, superseded by the above): judged the new predicate-position substitution
  "Share of shots that were on goal" natural football English, parallel to "on frame"/"on net", and
  distinct from the idiom "in on goal"; verified all 4 substitutions against formula, denominator,
  null condition and `direction` with no drift; confirmed no natural on-goal phrasing was missed on
  any of the 7 held rows.

## escalations
(none — the bare-modifier wording is RESERVED to the CPO in `decisions_reserved`, not escalated as
a blocking question. The MR ships without it; see `contract.md` §3 for the derived blocker table.)
