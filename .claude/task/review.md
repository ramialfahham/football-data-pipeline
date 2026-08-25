# Review — feat/82-mr4b2-promote-shared-definitions — 2026-08-25

diff_sha256: 12729abf2a09b53ecb8e375059d6b5a0987f42371f354d98c7bf777f1121396c

rounds: 4

rounds_cap_override: CPO, 2026-08-25: "one more review". Asked in plain terms after round 3 —
the work is fine, my paperwork is not, ship it or check again — with my recommendation to SHIP,
on the grounds that the outstanding fix was two marker sentences and I had by then built a
mechanical check for the class. He chose the review. It PASSed, and it found nothing further.

⚠ SIX NAMES WERE PULLED FROM THIS MR ACROSS TWO ROUNDS, every one a real defect I had approved,
and I found none of them. The MR shipped to review at 37 names and merges at 31.

⚠ THE SAME PAPERWORK CLASS FAILED THREE ROUNDS RUNNING — the fifth instance across two MRs. It
stopped when I replaced the prose rule with a search that cannot forget: extract every integer
from the artifacts and check each, rather than sweeping for the ones I remember changing.

## analytics-engineer-reviewer
VERDICT: PASS (round 3)
risks_checked:
- ROUND 1 FAIL: `is_home`'s promoted sentence says "the home side of the UPCOMING fixture" and was
  newly wired to `mart_team_fixture_stats`, `mart_player_fixture_stats`, `mart_player_match_log`
  and `mart_team_fixtures` — all grained on a finished or arbitrary fixture. Established from each
  model's SQL, not its YAML.
- NAMED THE HOLE IN MY PROOF rather than only the instance: the machine check compares a block with
  the text it REPLACED, so it is silent about the blank sites the block is then pointed at.
- ROUND 2 FAIL: a sixth name, `result`, in one my own sweep had marked safe. Its sentence claims
  the value comes from `int_legs__team_match`; `mart_player_match_log` never references that model
  and recomputes it at lines 136-140.
- ROUND 3: verified `result`'s removal site by site, then SQL-TRACED every remaining block making a
  provenance claim — `last_kickoff_at`, `latest_rank`, `latest_form`,
  `standings_group_description`, `round_order` — through every model each reaches. No mismatch.
- Traced `team_slug` through `base_apif__teams_global.sql` → `dim_team.sql` → `mart_team_profile.sql`
  and confirmed its "derived in base" claim holds wherever the value flows.
- NAMED ITS OWN COVERAGE GAP: it did not open the SQL for the flatly generic names that assert no
  provenance, and said so rather than implying full coverage.
- Verified the folded-scalar hand edits lost nothing, and the staging/base layer-scope claim
  against `check_description_hygiene.py`'s own code.

## platform-reviewer
VERDICT: PASS (rounds 2 and 3)
⚠ DISCLOSED IN EVERY ROUND that it had no execution tools and traced the code by hand instead.
risks_checked:
- ROUND 1 FAIL, found by READING: the `all()` in the narrowed replace guard was untested. Every
  test replaced ONE isolated line, where `all` and `any` are identical, so a mutation weakening it
  survived the whole suite — and the structural check could not catch it either, being blind to a
  reformat. Traced difflib's opcode merging to prove the gap was real rather than theoretical.
- Confirmed the guard is narrowed and not loosened: an empty planned set restores the original
  append-only rule exactly, and a replace one line off is still refused.
- Ran its own mutation in round 1 (deleting the already-has-a-description filter) and found it
  caught by `_verify`'s structural check rather than the content assertion it first expected.
- Recomputed the deletion accounting independently by grepping `^-\s+description:` rather than
  trusting the contract's arithmetic, in two separate rounds as the figures moved.
- Caught its own tool returning a stale read in an earlier MR and re-checked three ways; carried
  the same scepticism here.
- Flagged a stale figure in a CODE COMMENT as non-blocking rather than failing on it, and named it
  as belonging to scope-auditor's class.
- Confirmed the atomic write, line-ending preservation and `_write_files` reuse are genuinely
  shared with the other modes rather than reimplemented.

## scope-auditor
VERDICT: PASS (round 4, CPO-approved over the cap)
risks_checked:
- ROUNDS 1, 2 AND 3 FAIL, the same class each time. Round 1: the script's own docstring still said
  "APPEND-ONLY, AND THAT IS THE WHOLE POINT ... the acceptance test is simply that the diff has zero
  deleted lines", in the MR adding a replacing mode — I had flagged the tension in the contract and
  fixed it only there. Rounds 2 and 3: stale figures left standing in a document I had said was
  swept, the last one a single line in the evidence after I had swept the contract and the code.
- Verified each fix by ITS OWN search rather than my list, every round.
- ROUND 4: extracted every numeric token from both artifacts by grep, read each in its surrounding
  sentence rather than its line, and judged marker adjacency rather than accepting that a marker
  exists somewhere in the passage.
- Judged the seven numbers my audit deliberately excludes and confirmed none is a live claim about
  this MR's size being wrongly suppressed.
- Re-derived the block count from the diff itself (`grep -c '^\+{% docs '` → 31) rather than
  trusting the contract, and confirmed all six pulled names have zero references anywhere.
- Reconciled the 508 → 422 arithmetic including a step I had not written down: 6 of the filled
  sites are in staging and base, which sit outside the in-scope count.
- Judged the staging/base inclusion against `check_description_hygiene.py` and confirmed it is
  forced by the gate having no layer filter rather than a coverage decision of mine.
- Judged the three builder's calls against §10, including changing a guard's stated contract, and
  found each traceable to a standing precedent rather than a fresh silent decision.
- Confirmed nothing in `decisions_reserved` is touched, and swept for credential-shaped content
  every round.

## escalations
- question: after three rounds, all three of scope-auditor's FAILs were the same paperwork class
  and the outstanding fix was two marker sentences. Ship, or review again? Put to the CPO plainly,
  with the recommendation to ship and the note that a mechanical check for the class now exists.
  CPO ANSWER, verbatim: "one more review". Round 4 returned PASS with nothing further found.
