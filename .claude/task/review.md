# Review — handover write-out after #62 step 1 — 2026-08-14

diff_sha256: 6807fb418a1408896c476dd0be06f27388ec30f1a4c10d9ae3c04ed54cd440b1

rounds: 3

Routing for this path set yields one reviewer: **scope-auditor** (always-on). No other reviewer is
routed, because no code, model, script or test is touched.

Round 1: **FAIL**. Round 2: **FAIL**. Round 3: **PASS**. Both failures were the same defect class,
and both were mine.

⚠ **I ARGUED FOR SKIPPING THE REVIEW ENTIRELY AND WAS WRONG TWICE OVER.** The first draft of this
file said `rounds: 0` and "NO REVIEW ROUND WAS RUN, and that is a decision rather than an omission",
reasoning that adversarial review of a status document is what `feedback_review_cost_discipline`
warns against. The commit gate refused it — `rounds` must be a positive integer — so the round ran.
The gate was right: cost discipline is about not OVER-reviewing, not about opting out of the
mechanism. It then earned its keep immediately, twice.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 3 confirmed both prior findings closed: it grepped all three artifacts plus the patch for
  `NOT RUN` / `rounds: 0` / `NO REVIEW ROUND` and found every surviving hit to be past-tense
  narrative describing the superseded draft, with no live assertion left; and it cross-checked that
  `contract.md`, this file and `active_work.md` now tell the same story.
- ⚠ **ROUND 1 FAIL:** `contract.md`'s `decisions_taken` 1 still asserted "NO REVIEW ROUND IS RUN"
  after the gate had refused exactly that and forced the round. A superseded argument left standing
  as though true — which is the "a correction REPLACES, never accumulates" rule stated in the very
  handover being written. FIXED: the item now opens with the correction, records the original
  argument, records that the gate refused it, and states plainly that the gate was right.
- ⚠ **ROUND 2 FAIL, and the same class one file over:** the round-1 fix corrected `contract.md` and
  left THIS file still declaring `rounds: 0` and `VERDICT: NOT RUN`. The reviewer's words, kept
  because they are the lesson: the correction landed in the narrative but not in "the one file
  positioned as ground truth for what happened in review". FIXED by this rewrite.
- Ruled that an in-place correction to `decisions_taken` is the right instrument here rather than an
  `amendments:` entry, because it corrects the contract's own prior reasoning about review
  mechanics, not a `scope_paths` grant needing recorded CPO authority.
- Every changed path appears in `scope_paths`; nothing undeclared. `active_work.md` is absent from
  the patch by `review_exclude_paths`, not because it was untouched.
- The handover's factual claims verified against the tree rather than read: "nothing in flight",
  `!27` appearing only as merged, and main pinned at `10fa570` — checked against the `gitlab/main`
  ref, which is the CI authority (the local `main` ref differs and is not the comparator).
- Content deleted to fit the 16,000-character cap checked for loss against the 2026-08-14
  `escalations.log` entries: no standing CPO ruling is contradicted by what is now missing.
- No §10 decision smuggled in: "replace rather than append" and "keep the rebase-tax paragraph" are
  formatting calls about a handover file, not product, metric, naming or mechanism rulings.

## Verification (mechanical, because these claims are checkable rather than arguable)

- **15,994 characters**, under the 16,000 cap, measured with Python `len()` — never `wc -c`, which
  counts BYTES and over-reports by ~220 on this file.
- NEXT numbering unique (0-7); zero conflict markers.
- Every MR and issue number checked against `glab mr list` / `glab issue list` rather than recalled:
  no open MRs, main `10fa570`, #69 and #70 both exist.
- Swept all three artifacts for the superseded "no review round" claim after fixing it, rather than
  fixing the one file the reviewer named. That sweep is the round-2 lesson made mechanical.

## What the handover change does, and why

- **The header and CURRENT section are REPLACED, not appended to.** They described `!27` as in
  flight; `!27`, `!37`, `!39` and `!40` have all merged. A handover that describes finished work as
  pending is worse than none, because `handover_in.py` injects it into every new session — it is the
  one document a fresh chat is guaranteed to read and act on.
- **#62 is now a five-step thread with steps 1-2 done**, so the next session starts at step 3
  instead of re-deriving the plan.
- **The `country` ruling sits at the top**, because the pull to add that column is real: this task's
  own first design proposed it, and the field sits right there in the registry.
- **Three lessons kept because they cost real time:** the escalations union is NOT always
  `main + (mine − base)`; a probe returning False is not proof of loss; and never restore
  uncommitted work with `git checkout --` in a verification probe.
- **Two stale facts corrected in passing**, neither of which this task went looking for: the 04:00
  nightly is failing and merging `!39` did NOT fix it (the image still needs deploying), and the
  08-03 cost baseline predates both fixes to its own top-ranked item.
