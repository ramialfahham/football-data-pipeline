# Review — chore/dead-issue-references — 2026-09-10

diff_sha256: 65236da1bb6b6176005e850515a530cc6c3d29be2de030b750c35e4f27cb3990

rounds: 2

Round 1: `platform-reviewer` PASS; `scope-auditor` FAIL.
Round 2: `scope-auditor` PASS.

## scope-auditor
VERDICT: PASS (round 2)
risks_checked:
- ⛔ ROUND 1 FAIL — THE SHARPEST CATCH ON THIS BRANCH, AND A HARDER DEFECT THAN AN INVENTED RULING.
  The contract said "Step 3 of that plan" and cited a REAL `escalations.log` entry
  (`2026-09-10 chore/authority-map-in-claude-md`) — whose step 3 is **"split `escalations.log`"**,
  not dead references. The CPO's redirect was genuine ("do as recommended but before we get back to
  product work…") but unlogged, so the citation pointed at a true record for a sequence it does not
  contain. An invented ruling has nothing behind it; this one had a real entry a reviewer might
  accept on sight. It was caught by READING the entry rather than trusting the citation.
  Two related findings: the direction itself was unlogged, and `decisions_reserved` said "steps 4-8"
  of a plan with six steps.
- Round 2 — checked the new entry the way it asked to be checked, since an entry that SUPERSEDES
  another is where a rewrite of history would hide: verified it quotes the CPO verbatim (noting it
  preserves his uncorrected typo rather than tidying the quote), discloses being written only after
  the FAIL, and that the nine-step renumbering is consistent with the six it supersedes — old 3→4,
  4→7, 5→8, with the "8 depends on 7" dependency preserved from the old "5 depends on 4".
- Round 2 — matched `decisions_reserved`'s steps 4-9 one-to-one against the log's list: no invented
  step, none dropped.
- Round 1 — checked each removed reference for FACT LOSS: `#361`, `#377`, `#547`, `#526`. Every
  surrounding sentence still carries its dates, figures and substance; only the dead pointer went.
- Round 1 — confirmed the decision NOT to sweep the 292 `docs/` references is stated and reasoned
  (provenance vs instruction; a ~25-file unreadable diff) rather than quietly glossed.
- Scope, threshold and credential sweeps clean in both rounds.

## platform-reviewer
VERDICT: PASS (round 1)
risks_checked:
- ⭐ SPLIT A CONCERN I HAD CONFLATED. I flagged `FIRST_DEAD = 115` as a hardcoded boundary that goes
  wrong when GitLab reaches issue 115. It separated the two halves: raising the constant to 116 at
  that point is a LEGITIMATE adjustment and `test_the_boundary_is_not_vacuous` does not block it —
  but until someone raises it, a genuinely live `#115` would be flagged as dead. That second half is
  a real gap; it confirmed it is disclosed in the evidence rather than hidden.
- CHECKED THE FALSE-POSITIVE SURFACE I HAD NOT. Grepped both target files for markdown anchors
  (`](#`), hex-colour-shaped tokens and GitHub `#L` line references — none present, so `#(\d+)` has
  no live false positive. Noted it WOULD fire on a numeric-only markdown anchor if one were added.
- Verified the guard by tracing every `#<num>` in both files by hand rather than trusting the
  claimed counts: all below 115, matching the "0 dead refs" claim.
- CI wiring: `.gitlab-ci.yml` `test:python` runs `pytest tests/ -v` with no path filter, no
  `pytest.ini`/`pyproject.toml` restricting discovery and no root `conftest.py`, so the new file is
  collected. Fail-closed, which is correct for a CI test rather than a `.claude/hooks` guardrail.
- Runtime isolation: `REPO` resolves from `__file__`, so the test is CWD-independent, with no
  network, BigQuery or credential access.

## escalations

`2026-09-10 chore/dead-issue-references` — the CPO's direction that the context cleanup finishes
before product work resumes and that dead references go first, quoted; plus the REVISED nine-step
plan, which supersedes the six-step list in the preceding entry. Two steps are new, both surfaced by
the player-page investigation: dead references, and where parked work lives (10 stashes, one holding
the built player Overview tab).

## What this branch does NOT do

767 dead references exist; this fixes 6. The 292 in `docs/` and 470 in memory are untouched, and
whether they are worth a sweep is reserved. What is guarded is the two files where a dead reference
INSTRUCTS rather than merely records — which is where it did real damage: `CLAUDE.md` told every
session its next work was "player insights chain (#153 → #156)", and a memory file named #753 as the
player page's design authority. Neither number exists.
