# Review — chore/record-top-players-ruling — 2026-08-18

diff_sha256: bb9f4f0884f7158707eef3644df7b598aa4178d028497ee05a4d4e2d0ce27b2c

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: diff touches only `.claude/task/contract.md`, `.claude/task/escalations.log`, `docs/wireframes/10_home.md`, `docs/wireframes/99_gaps_register.md` — all inside `scope_paths`. No executable, model, script or site file touched, matching `impact_map` (writers: none).
- §10, GAP-31 withdrawal: verified it is a faithful consequence of the CPO's own words ("One per league… it's not a leaderboard in the defined pool") plus the factual observation that `mart_leaderboards` already partitions by `(league_code, season_api_year)` — not a builder's independent choice to cancel registered work. The withdrawal preserves the struck original and states the question "returns for any future block that genuinely ranks across competitions", so the underlying question is not quietly retired.
- §10 inverse check: grepped the diff for any proposed replacement copy — none. Both the log and `10_home.md` flag "NOT WRITTEN HERE — copy is §10" and leave only the factual content requirement. The mart-vs-page ordering question stays in `decisions_reserved`, decided nowhere in the diff.
- GAP-04 convention: read GAP-04's row and confirmed GAP-31's new row uses the identical pattern (strikethrough on gap + disposition, bold status with CPO date and quote, "not resolved" caveat) rather than an invented format.
- Cause-narrative honesty: the log's claim that the mock's invented data obscured the design is supported by quoted evidence, and it does NOT launder a spec error into a purely mock-caused one — `10_home.md`'s own pre-existing "pooled across the leagues of one pool" line is shown unedited as the superseded text, so both sources are named.
- Secrets sweep of the new hunks: nothing credential-shaped.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Ruling fidelity: compared `contract.md` and the new `escalations.log` entry against each other — both carry the identical CPO quotes ("One per league -> yes, it's not a leaderboard in the defined pool." / "we just need to rephrase"), and neither inflates the ruling into a decision on the replacement words or on where seven-winner ordering lives; both mark those NOT DECIDED / reserved.
- GAP-31's technical claim verified against source rather than trusted: `mart_leaderboards.sql` lines 117-120 compute `dense_rank() over (partition by league_code, season_api_year order by … desc)`, confirming the mart already ranks per league, so one-per-league genuinely needs no new pooled rank.
- GAP-30 re-verified against the same file: `count_boards` contains goals, scorer_points, shots_on_goal, dribbles_success, passes_total, passes_key, duels_won, defensive_actions, cards_total — `assists` is absent, so it has no rank-1 to take, exactly as the register states. GAP-27/28/30 rows are byte-unchanged in the diff, so they remain correctly live and untouched by the ruling.
- Swept `10_home.md` for every remaining "pool"/"pooled ranking"/"ranked across" occurrence: the scope-rule paragraph now carries the caveat that the cross-`league_code` rule stays dormant for this block; the closed-questions bullet is struck and superseded; the one remaining unstruck mention discusses a hypothetical single-league Pool 4, an unrelated case. No surface still presents the withdrawn pooled design as current.
- Scope: matches the "documentation only" framing; no export, mart or site file touched.

## escalations
(none)
