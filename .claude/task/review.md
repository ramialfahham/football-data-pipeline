# Review — chore/design-mocks-into-the-repo — 2026-09-10

diff_sha256: 736789570e243b3db9e234edaf6ed6cf3014139e9f3a5ecc6837c57650d3e946

rounds: 2

Round 1: `platform-reviewer` PASS; `scope-auditor` FAIL; `bi-analyst-reviewer` FAIL.
Round 2: `scope-auditor` PASS; `bi-analyst-reviewer` PASS.

Both round-1 FAILs were the same class the previous MR was FAILed for, which is why they are worth
recording rather than just fixing: **sweeping the part I was working in instead of the whole
source.** One was a missing ruling record, the other a missing ruling transcription.

## scope-auditor
VERDICT: PASS (round 2)
risks_checked:
- Round 1 FAIL — `contract.md` and `design-mocks/README.md` both asserted CPO authority for two
  decisions taken this session (bring the generators in; one value column) with NO entry in
  `escalations.log`. It grepped for the branch name and for the two topics and got nothing, and
  noted the aggravating detail: the previous version of this same contract cited a logged
  2026-09-09 entry, so the branch's own convention was to log first. ⚠ WORSE THAN THE !168
  INSTANCE, and it said so: one of the two citations was in `design-mocks/README.md`, a permanent
  checked-in file that states a ruling as settled fact to every future reader, not a task contract
  that the next task overwrites.
- Round 2 — checked the new `2026-09-10 chore/design-mocks-into-the-repo` entry records what he
  actually said ("1. yes 2. fix it") without inflating a one-word answer, and that it discloses
  having been written only after the FAIL rather than at the time. Confirmed the README now cites
  the log entry instead of asserting the ruling.
- Verified the "not in the repo, and deliberately so" self-correction is honest: the contract
  attributes that claim to the builder, not the CPO, and the phrase is gone from the shipped README.
- Every changed file inside `scope_paths`; impact_map claims checked against the diff (no
  `.gitlab-ci.yml`, no `dbt_project/models/**`, no `site_v2/src/**`); credential sweep clean.
- Swept for OTHER unlogged CPO attributions across the 27 incoming files: the "per the CPO"
  citations in `gen_competitions.py`, `gen_home.py` and `check_teams.py` are pre-existing rulings
  from the GitLab design issues carried in with the tooling, not new claims.

## platform-reviewer
VERDICT: PASS (round 1)
risks_checked:
- ⭐ CORRECTED MY REASONING ON THE `noqa` CHOICE. I treated `# noqa: E402` as a fallback because
  `.ruff-ci.toml` documents a per-file table as the preferred form. It grepped the repo and found
  scattered `noqa: E402` is already the established pattern — in `tests/`, `.claude/hooks/`,
  `scripts/diagnostics/`, and two `scripts/*.py` files that are NOT in the table. So the choice
  matches practice rather than dodging a guarded config, and `tests/test_lint_config.py` only
  asserts each table entry is `["E402"]` and that CI passes `--config`, never a cap on exempt files.
- CI surface, checked file by file: `test:python` runs `pytest tests/`, so the 27 new files are
  never collected; `lint:python` runs `ruff check .` with an exclude list that does not cover
  `design-mocks/`, so **the new directory IS under CI lint** — which is the coupling this MR is for.
  The local pre-commit hook's `files:` regex does not match it, the same "local misses, CI catches"
  shape the repo already relies on for `.claude/hooks/`.
- `REPO = Path(__file__).resolve().parent.parent` verified in every generator; the only remaining
  mentions of `D:/Projects/fdp-product` are prose describing what was fixed.
- `.gitignore` diff is `design-mocks/*.html` + `__pycache__/` only — a single-level glob matching a
  flat directory, no interaction with `site_v2/dist` or the site build.
- Re-run safety: each generator writes one self-named, gitignored file it owns; a crash mid-write
  leaves a regenerable local artifact and no shared state.
- `check_description_hygiene.py` globs `dbt_project/seeds` only and `check_copy_gate.py` has no
  doc-tree sweep, so neither picks up the two new `*.proposed.csv` files.

## bi-analyst-reviewer
VERDICT: PASS (round 2)
risks_checked:
- Round 1 FAIL — THREE CPO 2026-08-10 rulings present in the generator docstrings were absent from
  `10_home.md`, against this task's own acceptance criterion ("EVERY 2026-08-10 ruling"): the crest
  being the CLUB badge on player rows as well as team rows; every board ranking descending without
  exception, with its conditional reason; and per-board stacking ("they all stack together or not").
  ⭐ It also proved they were MISSED rather than routed elsewhere, by confirming the sigil-expansion
  ruling from the same docstrings genuinely does live in `metrics_display.md` under that file's
  charter. That is the difference between an omission and a placement decision, and it did the work
  to tell them apart.
- The fix was re-done as a SWEEP rather than a patch of the three named: `grep "CPO 2026"` across
  both generators, 15 attributed lines reducing to EIGHT distinct rulings. A FOURTH omission
  surfaced that way — "one metric per board → no column-header row → ONE value column", which is
  the very contradiction the CPO ruled on in this session and which existed only in a docstring.
- Round 2 — re-derived the full ruling set ITSELF rather than taking the count, reading both files
  in full instead of trusting grep, and traced all eight to their destinations. It reports 17
  line-hits against my 15 and explains the difference (two lines reference the date without the
  literal "CPO" and restate rulings 1-3), concluding the discrepancy changes nothing about which
  rulings exist or where they belong. Its count is the better one.
- Independently verified the "one value column" claim from the generator source rather than the
  evidence file, and spot-checked that `check_teams.py` mechanically asserts the 28-row /
  one-value-cell structure instead of the prose asserting it.
- Confirmed `00_overview.md`'s precedence is not contradicted: it governs field binding, a
  different axis from design-mock authority, and the README's "the issues are the authority, these
  scripts are the rendering" does not usurp it.

## escalations

`2026-09-10 chore/design-mocks-into-the-repo` — two CPO rulings, asked as two numbered questions
and answered "1. yes 2. fix it": the generators and checks come into the repo (the rendered HTML
does not), and the team boards have ONE value column. The entry records that it was written only
after `scope-auditor` FAILed the branch for its absence, and separately corrects a misattribution:
"not in the repo, and deliberately so" was the builder's decision, cited back to the CPO as his.

## Found and deliberately NOT fixed

- `gen_competitions.py` still fails. Its own guard fires because `intercontinental_super_cup` is in
  the shipped `competition_types.csv` and missing from the mock's `competition_types.proposed.csv`.
  That guard exists precisely so a mock cannot be designed against a taxonomy that is not real, so
  it is working. Syncing a file whose whole purpose is to PROPOSE a different taxonomy is a
  judgement, not a mechanical fix, and the competitions index (#54) is in `decisions_reserved`.
- The four Finnish player labels still render as unapproved probes. The renderer discards the probe
  flag and hardcodes the class, so un-dotting them changes what the mock shows — a design change to
  an artifact the CPO reviewed. The stale claim is corrected in the data and flagged at the line.
