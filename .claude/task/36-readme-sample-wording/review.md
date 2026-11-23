# Review — claude/36-readme-sample-wording — 2026-11-23

diff_sha256: 588dc4a815800bf0a88a042c5fc4f2bc931d98475c951bae9429885c2ccce954

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- The only file outside the task folder is site_v2/src/data/README.md, which is in scope_paths; no page, payload or script changes.
- The new text restates what check-built-pages.mjs already enforces (a board row that is not a link is an issue); decisions_reserved is none and no rule, mechanism or cost is added.
- approved_design none holds because no page output moves.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- The sentence that check-built-pages fails a board row that is not a link matches checkRankingsPage; the plain-text wording is gone.
- The claim that --sample must cover the board players matches linked_player_ids and the cut of the page players in export_all; the 74 players, 74 pages and --sample 74 agree.
- Rendered evidence is not required for a text-only change.

## escalations
(none)

The reviewers read the diff before the last edit of recipe step 6, which they pointed out contradicted itself (`--out <the same folder>` against a folder holding only the landing file and the Bundesliga payload). Step 6 now says `--out <a second scratch folder>` holding only those two files copied from step 1. It is wording only, in the same file.
