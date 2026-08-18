# Review — chore/record-top-players-ruling — 2026-08-18

diff_sha256: f8cefd0eebd46ba8a399e30dcb465974d43010d29df6831e396818e6895d4d72

rounds: 5

⚠ **REBOUND, not re-derived**: the hash below was recomputed after `gitlab/main` advanced by one
commit — `ac4231f`, itself the merge of THIS branch's first commit (`6eb1e1b`, round 1's ruling
record, MR !73) — while rounds 2–5 were still being reviewed locally on top of it. The cumulative
diff is base-relative, so the base moving (because part of this work already shipped) changes the
hash with zero change to any reviewed file. Confirmed via `git diff --stat` (empty — nothing
unstaged) and `--staged-hash` stable across repeated calls before rebinding. No content re-review
was needed or performed.

rounds_cap_override: The task's actual objective — record two CPO decisions (one player per
league; the intro-copy rephrase) — was done and confirmed in round 1. Rounds 2 through 5 were a
staleness sweep of `10_home.md` that grew out of round 1 (recording "four boards" made the
document's own uncorrected nine/six-board tables visible as contradictions), and each round a
reviewer found one more instance on a different axis: the board tables (round 2), a removed
board's ranking description plus the closed-questions log (round 3), the "what this needs from the
warehouse" list and a stale seed-column count (round 4's fix batch), and a row-count claim on yet
another axis (round 4's finding, fixed and confirmed in round 5). None of these was a contested
finding ground through by the builder — every one was accepted on sight and fixed. The CPO was
told directly, after round 4, that the pattern (each sweep axis catches its own instances and
misses the next) meant this had become a different, larger task than the branch's own objective,
and ruled: "commit what's here and open the separate task." Round 5 is the narrow confirmation of
the one fix made after that instruction, so the committed hash has a matching review record — not
a continuation of the sweep. The separate task is opened in the same breath as this commit.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 5, narrow: `docs/wireframes/10_home.md` line 185 ("Top 5 entries per board") confirmed struck and replaced with a SUPERSEDED note stating pool 1 renders seven rows. Cross-checked against the approved intro copy (seven leagues named) and the pool-1 membership table (seven leagues) — factually correct.
- The note's new claim "Top teams renders seven too" verified independently rather than trusted: the document's own prior "Open" note already says seven, and `design-mocks/gen_top_teams.py`'s four boards each carry exactly 7 rows.
- Confirmed the fix is confined to one line, within `scope_paths`, and introduces no re-sweep of the rest of the document.
- Earlier rounds, standing: round 1's ruling record verified faithful to the CPO's words and to `mart_leaderboards.sql`; round 2's board-table strikes verified against `gen_top_players.py`/`gen_top_teams.py`; round 3's banner-boundary fix and round 4's GAP-24/25/26/30 and seed-column corrections all verified against `99_gaps_register.md` and the seed file directly, not trusted on assertion.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 5, narrow: the sole change (`10_home.md` line 185) is inside `scope_paths`; it restates the already-ruled design (one row per pool league, seven rows) rather than asserting a new row-count or board-count decision — no new §10 call.
- `decisions_reserved` checked and untouched by this edit: the replacement wording is discharged (recorded in an earlier round's amendment with the delegate→propose→ratify chain named), the mart-vs-page ordering question and all build detail remain reserved.
- Earlier rounds, standing: the GAP-31 withdrawal is a direct, faithful consequence of the CPO's own words plus the factual observation that `mart_leaderboards` already ranks per league — not an independent choice to cancel work. Every sweep-round correction (board tables, the warehouse-needs list, the seed column count) mirrors an already-established fact in `99_gaps_register.md` or the seed file rather than deciding it afresh. No credential-shaped content in any round's diff.

## escalations
(none — the two Top players rulings recorded in this task were escalated by the CPO to the builder as decisions, not raised by a reviewer as a disputed classification; see `escalations.log`)
