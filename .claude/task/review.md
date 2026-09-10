# Review — chore/authority-map-in-claude-md — 2026-09-10

diff_sha256: 25ff73d6eb800ead98bb60de97e16e2c6d8dae1f7037ef2b027d4e8e96030738

rounds: 2

Round 1: `scope-auditor` FAIL; `bi-analyst-reviewer` FAIL.
Round 2: both PASS.

⭐ **BOTH ROUND-1 FAILS WERE THIS BRANCH DOING THE THING IT WAS WRITTEN TO PREVENT.** The task was
"write the map of which document owns what". One FAIL was me rewriting a rule while claiming to only
add; the other was me getting a row of the map wrong. Neither is machine-detectable, and no gate on
this branch would have caught either.

## scope-auditor
VERDICT: PASS (round 2)
risks_checked:
- ⛔ Round 1 FAIL (a) — A §10 RULE EXTENSION DISGUISED AS TIDYING. `00_overview.md` said
  **"Conflicts escalate to the CPO."**, absolute. I replaced it with "a CPO ruling beats every
  document here; below that, the more specific and more recent wins, and anything still unresolved
  escalates". That invents an auto-resolution and narrows when the CPO is consulted — a decision
  about who decides, in a sentence that reads like formatting. Reverted; the rule is restored in
  force with no tie-breaker.
- Round 1 FAIL (b) — the contract said "NOTHING IS DELETED" while (a) deleted a rule. Corrected to
  name the deletion and the revert.
- Round 1 FAIL (c) — the contract cited "the context-engineering plan the CPO asked for" with no
  `escalations.log` entry. THIRD BRANCH RUNNING for this defect, and it noted the new disguise:
  citing a plan and a sibling-MR reviewer correction rather than a ruling. Logged as
  `2026-09-10 chore/authority-map-in-claude-md`.
- Round 2 — verified the restored rule is absolute IN FORCE and not merely reworded to sound so;
  grepped for the auto-resolution language and got zero; checked the log entry quotes the CPO
  without inflating "go" into approval of the steps' content, and that it discloses being written
  after the FAIL.
- Verified `CLAUDE.md` grew +5 lines and that the precedence rule is not restated there
  (grep for the rule's phrasing returns 0), so the branch does not create the two-place precedence
  it exists to prevent.

## bi-analyst-reviewer
VERDICT: PASS (round 2)
risks_checked:
- ⛔ Round 1 FAIL — THE MAP HAD A WRONG ROW, which is the worst possible defect in a map. I filed
  `docs/ui_design_brief.md` as look-and-feel. Its **§6 is a per-screen FIELD contract** — "Per-screen
  data contract (what a mockup MAY show)", "if a stat is not listed below, we do not have it — do
  not draw it" — which the brief itself calls "the single most important rule in this document".
  ⭐ AND IT NAMED THE CONCRETE COST rather than the principle: `04_competition_hub.md` does not
  exist, so §6.5 is the ONLY live field contract for the competition hub, and a table calling the
  brief look-and-feel walks a reader straight past it.
- Round 1 also established what is NOT wrong, which is what made the finding usable: it read
  `site_architecture.md` and `content_architecture.md` in full and confirmed their rows are
  accurate, and it checked `metrics_display.md`'s LOCKED status against `escalations.log` to
  confirm the new conflict rule does not demote it.
- Round 2 — re-derived the supersession pattern from the documents rather than the claim: verified
  §6.3 carries the marker and points at `10_home.md` §0, and that §6.1/§6.2/§6.4 carry none, by
  grepping the brief itself. Confirmed the branch STOPS at describing that pattern and defers
  marking the three to the CPO, in both `00_overview.md` and `decisions_reserved`.
- Round 2 — verified the diff does NOT touch `docs/ui_design_brief.md`, so no silent marking snuck
  in outside the declared scope.
- Round 2 — re-checked what it had cleared in round 1, since the file had changed underneath:
  the conflict rule against the pre-round-1 original verbatim, the LOCKED declarations, and the
  "different axis" claim.
- Verified both quoted phrases from the brief are verbatim and correctly attributed.

## escalations

`2026-09-10 chore/authority-map-in-claude-md` — the CPO's instruction to fix the context
engineering, quoted; his "go" on the six-step plan; and the six steps in dependency order, with the
note that step 5 depends on step 4 and that getting that backwards was the first plan's error.
Explicitly NOT a ruling on any step's content.

## Open, carried to the CPO rather than decided

`ui_design_brief.md` §6.1 (Fixture), §6.2 (Team profile) and §6.4 (Player profile) have wireframes
and carry no supersession marker; §6.3 has one. Marking three sections superseded decides which
document binds a screen. In `decisions_reserved`.

## What this branch does NOT do

Nothing here is enforced. No gate can detect a page rebuilt without reading its design — which is
the failure it addresses. The only evidence that will count is the next page being built from its
issue and wireframe without being told to.
