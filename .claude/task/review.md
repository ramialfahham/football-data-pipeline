# Review — feat/82-metric-docs-blocks-generated — 2026-08-24

diff_sha256: d23515c6861581981955f6391a85fa10ecb1357e1e7fa54bb947398262c569c2

rounds: 2

⚠ ALL FOUR REVIEWERS FAILED ROUND 1, on four different defects, none of which I found myself.
Recorded here because the count is the useful part: this MR was built across a session boundary
after a crash, and every one of the four findings was a claim I had asserted rather than tested.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- ROUND 1 WAS A FAIL and it was the sharpest of the four. `finishing_efficiency` (team) still said
  "window" three times — "over a fully shot-covered window", "numerator and denominator share the
  window", "when the window is not fully shot-covered" — after the 35-row sweep. The generator's
  guard enumerated three phrasings and matched none of them, and this MR's own `done_when`
  verified window-freeness with THAT SAME PATTERN, so the check could only ever agree with the
  guard. It also established why this mattered rather than being cosmetic: the block is wired to
  `int_team_season__metrics_cumulative` as well as a form-window model.
- ROUND 2: re-read the reworded row against the four things it had to preserve — the same-coverage
  constraint, the [0,1] bound, the exclusion reasoning and the null policy — and confirmed all four
  survive with the word gone.
- Grepped the seed AND the generated file itself for "window": zero hits in the generated file.
  Noted the remaining CSV hits are all in the `interpretation` column, which the generator never
  reads.
- Confirmed the guard and its test no longer share the narrow definition that made the miss
  possible, the test now carrying three phrasings the old list was proven to miss.
- All ~35 window removals checked individually: every one a bare deletion with the substantive
  null or coverage caveat retained.
- `pass_accuracy_pct`'s "summed rather than averaged" checked against that row's own
  `numerator_expr`/`denominator_expr` — correct, both sides are summed before dividing.
- `penalty_committed`'s expansion checked against the yml text this MR deletes — content preserved,
  and `lower_is_better`/`direction` still football-correct.
- The four entity-split metrics judged individually: `duels_won_pct`, `finishing_efficiency` and
  `goals_open_play` are genuinely different metrics per entity (different provenance, different
  formulas for real attribution reasons), correctly two blocks each.
- Field-by-field re-diff: no `numerator_expr`, `denominator_expr`, `direction`, `lower_is_better`,
  `format`, `metric_group` or `importance_tier` changed anywhere in the diff. Only `description`.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- ROUND 1 WAS A FAIL. A third seed edit — `contribution_share`, with "CPO-accepted" removed — was
  undisclosed, and `acceptance_evidence.md` claimed to have accounted for every content change and
  found exactly two. That claim was false: it audited the 23 yml sites and never the seed's own
  diff. Its own framing is the accurate one — the drift this programme exists to prevent,
  reproduced one layer up in the seed itself.
- ROUND 2: verified the edit is byte-identical to round 1, now disclosed in both `contract.md`'s
  amendments and the evidence, and verified the "forced by the gate" claim against
  `check_description_hygiene.py`'s actual regex, which includes `\bCPO\b`.
- Swept the rest of the seed diff for any further undisclosed non-window content edit — none.
- Re-swept all four split-metric names across the working tree, not just the diff hunks: 0 blank,
  0 inline, no fourth site.
- Layer placement: the blocks attach via `{{ doc() }}`, a compile-time substitution into
  `persist_docs` metadata, creating no `ref()`/`source()` and no DAG edge, so a seed-sourced
  description on a core column is documentation rather than a data-flow violation.
- Information loss across all 23 replaced sites judged individually, including
  `pass_accuracy_pct`'s lost "Range-tested at model level" — confirmed the range test still exists
  in the same file's model-level tests, so the fact is not lost from the codebase.
- No `.sql` in the diff, so `depends_on` cannot have moved.

## platform-reviewer
VERDICT: PASS
risks_checked:
- ROUND 1 WAS A FAIL. `_describe_drift` names added, removed and changed blocks, and only "changed"
  was tested. It hand-ran the mutation — deleting the add/remove branches — and confirmed nothing
  went red, because the exit code comes from the byte comparison in `main()`. The two most likely
  real drift events for a catalogue had zero coverage.
- ROUND 2: confirmed each of the four branches now has a test whose assertion targets that
  branch's specific message text rather than a generic substring any branch could satisfy.
- Confirmed the `WINDOW_PHRASING` widening is real and effective by checking the generated file
  itself, which it correctly calls the definitive proof since that file is produced exclusively
  from the field the guard polices.
- Judged the non-atomic `write_bytes` acceptable, with better reasoning than the contract had: the
  file is git-tracked, so a truncated write is recoverable by `git checkout` without rerunning the
  generator, and a rerun self-heals because garbled content cannot byte-match `expected`. A
  materially different risk shape from `declare_missing_columns.py`, which edits hand-authored
  content across many files.
- Judged the unwired `--check`: what ships is not broken, it is inert. Named the residual gap
  precisely — `check_description_hygiene.py` catches a blank or restated column immediately but has
  no notion of "does the block match the seed", so seed-edited-without-regenerate is the one
  scenario that stays open until wiring lands. Ruled the sequencing call not its own.
- Independently recomputed the block arithmetic: 80 seed rows to 80 blocks, 76 ids with 4 split.
- CRLF, floors, re-run safety, dependency hygiene, credentials, guard-path touches: all checked,
  no defect.

## scope-auditor
VERDICT: PASS
risks_checked:
- ROUND 1 WAS A FAIL. Two edits to `metric_catalogue.csv` — `penalty_committed` and
  `pass_accuracy_pct` — were mine, not the CPO's, in a file the decision-rights table reserves to
  him, and the contract's `decisions_taken` authorised only the window-phrasing correction.
  Flagging them in the evidence was not the same as asking.
- ROUND 2: judged whether the amendment records an answer or wraps reasoning around one — the
  question put to it. Found the CPO's answer recorded minimally as "approve all three", each edit
  named with its own before and after, and the self-critical framing attributed to me rather than
  to him. Checked that separation against the diff.
- Ruled the fourth edit (`finishing_efficiency` and the regex widening) sits INSIDE the original
  window-phrasing authority rather than needing fresh sign-off, because it enforces an instruction
  already given more completely rather than making a new decision.
- Confirmed `acceptance_evidence.md`'s false claim is corrected at the site of the claim rather
  than contradicted below it, matching the precedent this log already set.
- Confirmed GitLab #88 is filed and explicitly left undecided rather than smuggled in.
- Scope: same 18 files as round 1, all within `scope_paths`; `.gitlab-ci.yml` and
  `stop_gate.py` absent, consistent with `decisions_reserved`; no credential-shaped strings.
- Verified the three pre-crash CPO decisions in `decisions_taken` are recorded as options chosen.

## escalations
(none — the one CPO question this round was answered before the round closed and is recorded in
`contract.md`'s `amendments:`, not here.)
