# Review — feat/243-full-coverage

diff_sha256: b3a3507260fcb0923509945d5e46612435ee36e5f7958a809814e34aaaa847a0

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL (the validate-local skill's Tier 1b still described the old check) is closed: the skill is in scope_paths by a clean-tree amendment and states the check as changed; the measured run time is not in it.
- Every changed file is inside scope_paths; the new mechanisms (never-rises test, the --out generator interface, the process pool, the coverage section) and the recurring cost are declared in decisions_taken.
- decisions_reserved is none and the diff decides no product, UX, metric, naming or URL matter; the --out option changes no generator output.
- The bootstrap return in the never-rises test applies only while main's baseline has no coverage section, the case this branch introduces.
- No secrets, no CI, workflow or permission file, no site_v2/src, ingestion, dbt model or export change.
- Open, not a defect: the rendered pins are filled from validate:ui's counts.json in the next commit, which the last done_when line needs before merge.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 findings closed: an end-to-end test runs main() on a temp inventory, site and mock folder and proves a coverage gap and a miss above its pin exit 1 and a pinned run exits 0; the base lookup fetches the base commit in a shallow CI clone with safe.directory set; each failing generator's reason prints.
- Round 2 findings closed: an empty base ref fails the test instead of comparing the baseline with itself; a row matching one file in every language no longer clashes with itself, and two literal rows on one file fail, each pinned by the ownership test.
- Fail-closed: a row matching nothing, a generator writing nothing, a missing site, a missing FI switch and a switch that does not switch are hard failures; comparisons are skipped only on a narrowed run.
- Ownership: a literal URL beats a glob, two globs or two literals on one file fail, and a glob does not cross a path separator.
- Process pool: jobs and results pickle, results come back in viewport order, servers close in finally.
- Generators: imports present, absolute out paths, the stale-file unlink skipped under --out, gen_home's OUT redirected only when run directly.
- Unverified here: the pool's wall time on the Linux runner; measured on the MR pipeline.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL (the intro said every mock page renders in DE) is closed: a built page renders in EN, DE and FI, a mock in EN and, with its FI switch, FI, matching MOCK_LANGS and plan().
- Widths, the four coverage gaps, element misses, the 1px overflow margin, the fifth-of-a-line trim and the never-rises rule match the code.
- The Pages paragraph matches plan(): every file a glob matches is owned, a literal URL wins, a page no row names is rendered and counted; renders of record are not pages.
- Every mock row's Source and URL matches the file its generator writes with --out.
- No decision history, date, issue or MR number or credit in the added text; no site_v2/src or display-contract change.

## escalations
(none)
