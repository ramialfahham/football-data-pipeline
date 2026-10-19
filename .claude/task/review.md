# Review — feat/221-shared-fold — 2026-10-19

diff_sha256: 61aa66a131307a5b41821048cd25b4974dd9c5840521ffc25fcdfb039c9fb5e2

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Checked every file in the diff against scope_paths; the contract has no amendments and needs none.
- Checked the five acceptance criteria against #221's What exactly: control under the shown rows, the two labels and chevron states, no script, the rows joining a two-column grid.
- Checked the doc edits stay inside the approved plan: the Fold row, Fold in Home's Pages row, the 10_home.md fold sentence; no fxmore, details or summary wording left in docs/.
- Checked §10: the copy, the checkbox toggle as the site's existing scriptless pattern and its find-in-page effect are in decisions_taken; no new mechanism, no recurring cost, the Teams page untouched.
- Checked approved_design home: #127 and matches: #130 cover the three pages that render the fold, and no other page renders Fold.astro.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Checked the built EN/DE/FI labels: "Show all 5 / Show less", "Alle 5 anzeigen / Weniger anzeigen", "Näytä kaikki 5 / Näytä vähemmän"; homeShowLess in all three locales and in the three specs.
- Checked the dividers against the built DOM: the last shown row keeps its line above the control, the last folded row keeps it when open, a date heading opening the fold carries the line above it and none below.
- Checked accessibility: the hidden checkbox stays in the tab order, the label's accessible name is the one visible text, the focus ring draws on the label.
- Checked the Matches page filters hide whole groups by attribute and are unaffected; fold ids are unique per page and collide with no filter or day id.
- Checked the frontend computes nothing new: n is the served row count and the three shown rows are the existing presentation constant.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Checked the code pin 727 to 726 against the one removed comment line carrying an issue number in gen_matches_hub.py; PINNED_FILES stays correct.
- Checked the docs pin for block_standard.md 51 to 50 against the one removed Ruled-on cell; no other pin moved and no ceiling was loosened.
- Checked the mock generators' format strings and check_home.py's splits match the markup they emit, and no mock carries fold CSS of its own.
- Checked no dependency, lockfile, workflow, hook or credential change.

## escalations
(none)
