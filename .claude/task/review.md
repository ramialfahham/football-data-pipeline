# Review — feat/82-mr4b-generate-and-promote — 2026-08-25

diff_sha256: 19a8b38c24ad8d4290e62c7ebd2cb18e1943a0e77f511f948742e0f9a042f5ad

rounds: 4

rounds_cap_override: CPO, 2026-08-25: "run one more check". Asked in behaviour terms after the
three-round pattern was put to him plainly — a reviewer has caught the same mistake in my paperwork
three times, I have fixed the third one and nobody has checked it, one more check or ship? The
reason for granting it, in my framing that he accepted: scope-auditor had found something real in
every round, which argues against the cap rather than for it. Round 4 PASSed.

⚠ FOUR ROUNDS, SIX REAL DEFECTS, AND I FOUND ONE OF THEM. The one I found is the reason this MR
exists — reading the composed output showed a fifth of the derived names taking a player's
definition onto a team column. The other five were found by reviewers. The count is the finding
and it is recorded in `escalations.log` rather than softened here.

⚠ ONE REVIEWER WAS ROUTED BY JUDGEMENT, NOT BY PATH, AND IT FOUND TWO OF THE SIX.
`football-analytics-expert-reviewer`'s trigger is `metric_catalogue.csv`, which this MR never
touches. The trigger names a file; the risk it exists to catch was in composed prose reaching 130
warehouse columns.

## analytics-engineer-reviewer
VERDICT: PASS (round 3)
risks_checked:
- ROUND 1 FAIL: `clean_sheets_sum_season__team` composed the catalogue's RATIO definition, display
  convention and all ("shown as a count of games played, e.g. 3/5"), with "Totalled over the
  season". One fluent sentence asserting the value is both a small fraction and a season total.
  Established from the SQL that the column is `clean_sheet_games` alone while the metric is
  `safe_divide(clean_sheet_games, games_played)`. Found by reading it; no guard could see it.
- Independently enumerated all 16 `_sum_season` stems rather than accepting "exactly one name
  affected", and checked each against the catalogue.
- Ruled on whether `_delta_yoy` on a ratio is the same defect: it is not, because a delta of two
  ratio values is well defined while a total of ratios is not, and only `clean_sheets` carries a
  display-format clause.
- Verified the `MODEL_ENTITY` table entry by entry against the models' own SQL headers, including
  the three whose names do not state their entity.
- Judged the entity-suffix decision and the 48 blank columns: sound, and reserved rather than cut.
- Information loss at the three kept-sentence sites judged individually; confirmed the one dropped
  clause is banned by the standard as a downstream-consumer claim.
- ROUND 3: re-read every block it had flagged for content drift from the rewrap — only line-break
  positions moved, no wording changed — and confirmed the new cup/tournament clause is traceable
  to `mart_player_profile.sql`'s join rather than merely plausible.

## platform-reviewer
VERDICT: PASS (rounds 1, 2 and 3)
⚠ DISCLOSED IN ALL THREE ROUNDS that it had no execution tools and had traced the code
symbolically rather than running it. Recorded as it asked: judged on what was actually done.
risks_checked:
- Re-derived the `!98` line-ending fix from `_same()` and the parametrised endings tests rather
  than believing the evidence; confirmed `.gitattributes` carries no `eol` rule for these types.
- Traced all three round-2 mutations by hand and ran a fourth of its own (deleting the
  already-has-a-description filter), finding it caught by `_verify`'s structural check rather than
  the content assertion it first expected.
- Hand-traced the round-3 synthetic hyphen test: a 122-character single token against width 95 has
  no legal break point except the hyphen, so the mutation has nowhere to hide.
- NAMED A REAL LIMIT IN ONE OF MY TESTS: `test_the_real_file_breaks_no_hyphenated_word` inspects
  the shipped file without regenerating, so alone it could not tell "the code is correct" from
  "the file happens to be clean" — then established that the pre-existing byte-comparison test
  closes that gap, so the suite as a whole is not fooled.
- Caught its OWN tool returning a stale read of the generated file and re-checked three ways
  rather than reporting a repository defect.
- Confirmed the refusal-reporting plumbing has no accidental `None` on the production path, the
  `rated` set handles whitespace-only fields, and both reverted yml sites are genuinely blank
  rather than carrying an empty description key.
- Confirmed `_write_files` is genuinely reused by the new wiring mode rather than reimplemented.

## football-analytics-expert-reviewer
VERDICT: PASS (round 3)
risks_checked:
- ROUND 1 FAIL: the `_delta_yoy` phrase claimed NULL could arise from "a gap in statistical
  coverage" — true for a team, IMPOSSIBLE for a player, because a player's null per-match stat
  means ZERO, so a running sum never goes null for coverage. Established from
  `int_player_profile__yoy.sql`'s own statement and the project's player-null convention, not from
  the neighbouring prose.
- ROUND 2 FAIL: the fix removed a TRUE cause with the false one. The block is reused at
  `mart_player_profile`, which carries every competition-season, so a cup or tournament row is NULL
  for a reason the sentence no longer named. Named the general rule: a shared block is only as true
  as its widest call site.
- Traced every affix phrase to the SQL: the games-played and appearance alignments, the
  domestic-league scope, and that `_prev_season_full` is never differenced.
- Judged the entity-neutral wording of "matches played" honest rather than evasive, given the model
  descriptions carry the precise rule.
- Sampled the totalling affixes against rate metrics to check none got a nonsensical "totalled".
- Confirmed the seven player-only metrics describe genuinely different quantities from their team
  namesakes, so this is a catalogue gap for the CPO and not a misnaming — the read his decision
  rests on.
- ROUND 3: verified the new clause at BOTH call sites, swept the generated file for any residual
  hyphen break, and raised as NON-BLOCKING that "a cup or an international tournament" does not
  naturally cover a QUALIFYING campaign, of which six are active. Taken anyway.

## scope-auditor
VERDICT: PASS (round 4, CPO-approved over the cap)
risks_checked:
- ROUNDS 1, 2 AND 3 FAIL, the same class each time: a stale claim corrected exactly where named and
  left standing elsewhere in the same document. The objective; then the blast_radius and two
  done_when bullets; then the blast_radius again, because the round-3 hyphen fix changes text
  outside this MR's scope while the section still said "ONE intended effect" and "ONLY FIVE SITES".
- Verified each fix by its OWN search rather than my list, grepping the whole contract for every
  stale marker from prior rounds and cross-checking each hit against the diff.
- Confirmed all three named rewrap blocks genuinely change in the diff and that no fourth was
  missed or over-claimed.
- Searched the whole diff for the superseded "a cup or an international tournament" phrasing to
  confirm the fix propagated from its single source point.
- Judged the scope-down to its own MR, the 48-column reservation and the three builder's calls:
  each traced to a standing precedent rather than a fresh silent §10 decision.
- Judged whether fixing three pre-existing hyphen breaks is drift: defensible, mechanical,
  meaning-preserving, disclosed with reasoning, and confined to files already in scope.
- Read amendment 8 for softening and found none, including its self-correction of my own miscount.
- NOTED WITHOUT FAILING that `acceptance_evidence.md` was itself stale. Corrected rather than left,
  because that is precisely the class it had already failed three times.

## escalations
- question: scope-auditor had FAILed three consecutive rounds on one defect class, correctly each
  time, and the fix for its third finding was unreviewed at the cap of 3. Run a fourth round, or
  ship and log the pattern? Put to the CPO in behaviour terms, with the recommendation to run one
  more because the reviewer had found something real in every round.
  CPO ANSWER, verbatim: "run one more check". Round 4 returned PASS.
