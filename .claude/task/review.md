# Review — feat/243-full-coverage

diff_sha256: 27b448d7a1b78b7ce8214f089c5fed134ab542166ef4f413ddb545e95dae8f81

rounds: 4

rounds_cap_override: a fourth round to speed the check up and pin the counts CI measured, approved in chat, 2026-11-02

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL (the validate-local skill's Tier 1b still described the old check) is closed: the skill is in scope_paths by a clean-tree amendment and states the check as changed; the measured run time is not in it.
- Every changed file is inside scope_paths; the new mechanisms (never-rises test, the --out generator interface, the process pool, the coverage section) and the recurring cost are declared in decisions_taken.
- decisions_reserved is none and the diff decides no product, UX, metric, naming or URL matter; the --out option changes no generator output.
- The bootstrap return in the never-rises test applies only while main's baseline has no coverage section, the case this branch introduces.
- No secrets, no CI, workflow or permission file, no site_v2/src, ingestion, dbt model or export change.
- Round 4: the hover and press checks move the mouse to the element's centre instead of waiting on Playwright's hover; the element, the property and the comparison are unchanged, and the change lowers the declared recurring cost.
- Round 4: the rendered pins are filled from validate:ui's counts.json on the MR pipeline, closing the last done_when line.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 findings closed: an end-to-end test runs main() on a temp inventory, site and mock folder and proves a coverage gap and a miss above its pin exit 1 and a pinned run exits 0; the base lookup fetches the base commit in a shallow CI clone with safe.directory set; each failing generator's reason prints.
- Round 2 findings closed: an empty base ref fails the test instead of comparing the baseline with itself; a row matching one file in every language no longer clashes with itself, and two literal rows on one file fail, each pinned by the ownership test.
- Fail-closed: a row matching nothing, a generator writing nothing, a missing site, a missing FI switch and a switch that does not switch are hard failures; comparisons are skipped only on a narrowed run.
- Ownership: a literal URL beats a glob, two globs or two literals on one file fail, and a glob does not cross a path separator.
- Process pool: jobs and results pickle, results come back in viewport order, servers close in finally.
- Generators: imports present, absolute out paths, the stale-file unlink skipped under --out, gen_home's OUT redirected only when run directly.
- Round 4: POINTER_JS selects the same element as the old bounding_box() test, the index addresses the element the mouse went to, and with reduced motion the style read right after the move is the final hover value; an obscured element now reads as a miss instead of hanging the run.
- Round 4: a full local run gives identical counts before and after the pointer change; the next linux pipeline is the first check of the new path against the linux pins.
- Unverified here: the job's time against the runner's job timeout; measured on the MR pipeline.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL (the intro said every mock page renders in DE) is closed: a built page renders in EN, DE and FI, a mock in EN and, with its FI switch, FI, matching MOCK_LANGS and plan().
- Widths, the four coverage gaps, element misses, the 1px overflow margin, the fifth-of-a-line trim and the never-rises rule match the code.
- The Pages paragraph matches plan(): every file a glob matches is owned, a literal URL wins, a page no row names is rendered and counted; renders of record are not pages.
- Every mock row's Source and URL matches the file its generator writes with --out.
- No decision history, date, issue or MR number or credit in the added text; no site_v2/src or display-contract change.
- Round 4: the pointer change and the pins change no doc claim; the Measured-as text still describes the pointer resting on, or pressing, the first visible match.

## escalations
(none)
