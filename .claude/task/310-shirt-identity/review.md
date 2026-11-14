# Review — feat/310-shirt-identity — 2026-11-14

diff_sha256: b859b9ddbd8f7920e2f9855c24961a3f89260362f5d7eb356ef6da887106725d

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every staged file is in scope_paths; the CPO approval on #310 is named with its date; the guards (one candidate per shirt, per sheet id and per stats id; match-wide stats-line and sheet checks; hand-overridden and researched sheets not paired; substitution events take the pair) are engineering inside the approved rule.
- Round 3: the card and goal correction exclusion was escalated and is now recorded as the CPO's approval of 2026-11-14 (hand data stays as entered), on its own amendment line; the blast_radius is refreshed with every guard (14,607 rows, 8,587 sheets, 7,173 matches, 43 competitions).
- No new mechanism or recurring cost; no page surface; base.yml states the rule, the override precedence and the correction precedence.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 and 2 findings closed: the test excludes hand-overridden ids on both sides and reads only the fetch base read; base.yml documents the rule; shirt_pairs is unique per shirt, per sheet id and per stats id, so the parsed and substitution joins cannot fan out.
- Round 3: own_line and named are match-wide (the CIT 1489093 sheet id 86, whose stats line sits under the other team, is never paired); hand_corrected reads the card and goal correction seeds with their int64 columns and leaves those sheet ids unpaired; the test mirrors both.
- Layer placement in base, seeds as leaf refs, no cycle, no competition identifier, no metric change; the grain tests still cover the model. Residual noted: the answer-key seeds key on player_id and data:build:mr is the arbiter for them.

## escalations
- question: Does "hand overrides keep precedence" on #310 also cover the hand-entered card and goal correction seeds, so a sheet id they name keeps its own id in that match?
  CPO ANSWER: yes, approved in chat 2026-11-14 (Path A).
