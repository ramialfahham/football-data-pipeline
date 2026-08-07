# Review — docs/19-compile-dont-append — 2026-08-07

diff_sha256: 2a52a4513de464925e652e6061378fc4ef4fd651501b2f1094c7f8e7b925a4dd

rounds: 6

rounds_cap_override: >
  The cap WORKED and was not bypassed. Round 3 was the cap, and the builder STOPPED there and took
  the open findings to the CPO rather than patching a fourth time, which is what §2 requires. The
  CPO resolved them by WITHDRAWING the narrative test and shipping the compression alone. Rounds 4
  and 5 exist because that decision CHANGED THE DIFF — the test was reverted, `tests/` left
  `scope_paths`, and `contract.md`'s NEW MECHANISM declaration inverted — and an unreviewed diff
  cannot merge on a verdict given against a different one. Round 4 FAILed (the second amendment
  claimed CPO authority with nothing in `escalations.log`), round 5 PASSed after that record was
  written. Authority: `.claude/task/escalations.log`, `⭐ CPO RULING: THE NARRATIVE TEST IS
  WITHDRAWN`.

  ROUND 6 was opened by the BUILDER, not by a reviewer finding. The suite reported 645 where
  `done_when` predicted 646, so the contract carried a false factual claim about the code —
  #904's class, a prediction never re-checked against the finished tree. Five rounds had missed
  it; the measurement caught it. Corrected, re-reviewed, PASS. The three character-count figures
  the reviewer then flagged as unverified-by-review were measured afterwards and are exact:
  §2 = 14,448 of 26,374 (54.8%), 6.07x the next largest section, 12.2% compression. No further
  round was opened, because nothing was found to be wrong.

## scope-auditor
VERDICT: PASS
risks_checked:
- The `done_when` test-count correction (round 6, 645 not 646): re-derived the arithmetic
  independently from the withdrawn test's actual definition — a single-element `parametrize` tuple
  adds exactly one case — rather than accepting the restated number, and confirmed the correction
  states plainly that it was wrong instead of erasing the history.
- Swept `contract.md` for other unverified factual claims: found three character-count figures
  outside `done_when` and flagged them as unverified rather than treating "not contradicted" as
  checked. Measured afterwards by the builder and exact; recorded under `rounds_cap_override`.
- Second amendment's CPO authority (the round-4 finding): `escalations.log` now carries a
  `⭐ CPO RULING: THE NARRATIVE TEST IS WITHDRAWN` block naming all six marker/rule collisions with
  the rule sentence each would have rejected, the root cause, both paths as put, the corrected
  recommendation and the CPO's answer; `contract.md` cites it by name as AUTHORITY. Confirmed
  present and adequate, matching the standard applied to the first amendment in round 2.
- First amendment's CPO authority (the round-1 finding): fixed in round 2 and re-confirmed. The
  cited `escalations.log` block states the actual fork put to the CPO and his answer to it, rather
  than recording that something happened.
- §2 rule preservation across all eleven touched passages, traced against the pre-change file. No
  rule lost; only narrative trimmed or relocated. Eight compressed passages each had a located
  counterpart in `escalations.log` or `review_routing.json`'s `_doc`; three moved passages were
  each verified counterpart-ABSENT before being moved, and are present verbatim in substance in
  the log.
- Clean withdrawal of the narrative test: `test_rule_documents_carry_no_narrative`,
  `NARRATIVE_MARKERS` and `RULE_DOCUMENTS` are absent from the tree, and the remaining tests in
  `tests/test_governance_doc_parity.py` are GitLab #1's pre-existing suite. Verified rather than
  accepted from the contract.
- The surviving reference at `docs/working_agreement.md:157` ("`tests/test_governance_doc_parity.py`
  now checks both claims mechanically") is HONEST: it sits directly after the doc/row-mismatch and
  guard-path-count rules, which are exactly what `test_the_guard_path_counts_are_what_the_docs_claim`
  and `test_every_prose_count_matches_the_derived_value` check, and both still exist on `main`. No
  stranded reference to the withdrawn test.
- Scope: every changed file is in `scope_paths`; no protected path touched; `tests/` correctly
  removed from scope once the test was withdrawn.
- `decisions_taken` thresholds against the final diff: NEW MECHANISM inverted to NO and now true,
  since the diff is prose plus task artifacts only. No recurring cost, no external surface, no
  guard invariant changed.

## escalations
- question: Three passages of RECORD had no counterpart anywhere, so under the approved method they
  would stay in §2, leaving the rule document as the only copy of three incidents. Move them into
  `escalations.log` and cite them, or leave them?
  CPO ANSWER: "go ahead as recommended" (conversation, 2026-08-07) — move them. Recorded in
  `escalations.log` under `⭐ CPO RULING: AUTHORITY FOR THE METHOD CHANGE`.
- question: The narrative test was FAILed by `platform-reviewer` in three consecutive rounds, each
  time with a legitimate RULE sentence it would wrongly reject. Round 3 hit the cap. Ship it with
  the two contested markers dropped, or withdraw it and ship the compression alone?
  CPO ANSWER: "B" (conversation, 2026-08-07) — withdraw it. Recorded in `escalations.log` under
  `⭐ CPO RULING: THE NARRATIVE TEST IS WITHDRAWN`. Filed as GitLab #26.

## Note on `platform-reviewer`, stated rather than left to inference
It reviewed rounds 1-3, when `tests/**` was in the diff, and FAILed all three — every finding
correct, and its round-2 observation that the round-1 fix had patched named instances rather than
the class is what eventually surfaced the design flaw. Those findings are why the test was
withdrawn. It carries NO verdict section here because it is no longer a REQUIRED reviewer: `tests/`
left the diff with the test, and `docs/working_agreement.md` confers no routing row. Its full
finding history is in `escalations.log` and in GitLab #26, not discarded.
