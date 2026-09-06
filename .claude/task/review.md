# Review — fix/deserved-points-clamped-to-legal-range — 2026-09-06

diff_sha256: 5e0a4f826b2c4c8acb588c72acacebf7491fbc5f95d8b8200e86a1c0a17addf6

rounds: 5

rounds_cap_override: >
  CPO, 2026-09-06. Round 3 hit the cap with TWO open FAILs and I stopped and brought them, as the
  rule requires. One of them — the `severity: warn` classification — could not be fixed by me at all,
  because `scope-auditor` had correctly identified it as a §10 decision. He was given both options
  with their consequences, told "Say 'warn' and I'll finish. Two smaller things I'll fold in without
  asking further," and answered **"warn"**. Recorded in `escalations.log`, entry
  `2026-09-06 — fix/deserved-points-clamped-to-legal-range — TEST SEVERITY: WARN`.
  ⚠ What the extra rounds were spent on, because the cap exists to test exactly this distinction —
  looping versus fixing. Nothing was re-argued and no reviewer verdict was disputed:
    round 1  FAIL — a metric definition hand-written into a GENERATED file (also caught by the suite)
    round 2  FAIL — the same stale claim left standing in the sibling artifact readers actually see
    round 3  FAIL x2 — a §10 decision I took myself, and a now-false formula sentence
    round 4  FAIL — my own blanket find-and-replace corrupted a citation to the ruling record
    round 5  PASS
  Every round accepted its finding in full. Round 3's pair is what justifies the budget: one was a
  live falsehood about a row in prod, the other was a decision that was never mine.

⚠ **VERDICTS WERE OBTAINED AT TWO HASHES AND THAT IS RECORDED, NOT IMPLIED.**
`analytics-engineer-reviewer` and `football-analytics-expert-reviewer` PASSed at `ed557267…`.
The only change since is `contract.md` prose plus two lines of `acceptance_evidence.md` — the
citation fix `scope-auditor` itself raised — and `scope-auditor`, which is the reviewer that judges
`contract.md`, re-read the whole diff at `5e0a4f82…` afterwards. No code, yml, seed or generated file
differs between the two hashes; `scope-auditor` verified that independently.

## scope-auditor
VERDICT: PASS
risks_checked:
- Both cited escalation-log strings searched VERBATIM against the log: found character for character
  at `escalations.log:8012` and `:8059`. The corrupted variant it had FAILed on
  (`fix/deserved-points-capped-to-legal-range`) has zero hits in either file.
- ⭐ It did not stop at the two citations. It cross-checked EVERY other quoted string in the contract
  — the four verbatim CPO quotes, the `docs/working_agreement.md:322,328` rule references, the test
  names, the file:line refs — against the log and the diff, looking for a second instance of the same
  blanket-replace corruption. None found.
- ⭐ It confirmed the `escalations.log` hunk is APPEND-ONLY past line 8007, ruling out the possibility
  that the citations now match because the log was edited to fit the contract rather than the other
  way round. That is the check that makes the whole attribution mechanism worth having.
- Code diff re-confirmed unchanged from round 4's substance; this round touched contract prose only.
- `scope_paths` unchanged and covering every touched path; nothing smuggled in with the fix.
- The amendment's account of the cause matches what it verified independently and does not overclaim
  — it names both files fixed and claims nothing beyond the citation, branch-name and
  stale-measurement corrections.

## analytics-engineer-reviewer
VERDICT: PASS (at `ed557267…`)
risks_checked:
- Rename completeness across SQL alias, final `select`, yml column entry, BOTH test expressions, BOTH
  test names, the seed row and the regenerated markdown. A repo-wide case-insensitive `clamp` grep
  returns only two unrelated hits (a different metric's comment, a CSS property) plus task paperwork
  narrating the rename as history. No orphaned identifier.
- The corrected formula sentence checked AGAINST THE SQL rather than for plausibility, including the
  null case: `GREATEST`/`LEAST` propagate NULL, so both `deserved_points` and
  `deserved_points_was_capped` are NULL for an unfittable league-season, matching the column doc's
  explicit "NULL, not FALSE" claim.
- Seed vs regenerated markdown for both changed rows: identical word for word. Rendered lengths
  ~963 and ~977 against the 1,024 limit — reported as a hand count and explicitly flagged as an
  approximation rather than a certified pass, which is the honest form.
- ⭐ **It ran the inverted sweep I should have run two rounds earlier**, enumerating every prose claim
  about `deserved_points` / `_gap` / `_rank` / `_was_capped` across the SQL docstring, yml, column
  descriptions, test comments, seed and markdown, and reported that it found no third false statement.
- Mutation reasoning re-derived with the new names: `deserved_rank` ranks on the POST-cap value, so no
  wrong-rank mutation survives silently; both error-severity tests read served columns directly.
- Structural checks after the edits: CTE chain resolves, `season_games_played` exists on the model,
  the CSV row still has its 15 fields, no project-level severity default overrides the warn/error split.
- The `DeservedHero.astro:79` rounding confirmed unchanged, out of scope, and correctly deferred to
  #108 rather than re-raised as this diff's defect.

## football-analytics-expert-reviewer
VERDICT: PASS (at `ed557267…`)
risks_checked:
- The renamed column and test read correctly to a football audience and use the word the CPO's own
  ruling used. Checked that the column name, the comment prose and the SQL alias agree.
- The seed states the cap in FOOTBALL terms — "capped into the [0, 3] a match can yield" cites what a
  single match can actually produce (0/1/3), not a statistical "clamped to interval" phrasing.
- The corrected model description checked against the SQL it describes: literally true, not merely
  plausible.
- All FOUR copies of the sums-to-zero claim compared for a consistent story; none asserts an
  unconditional zero-sum that another denies.
- `direction` / `interpretation` / `format` / `lower_is_better` re-derived fresh on all three deserved
  rows rather than assumed settled by its two earlier passes, and cross-checked against the
  catalogue's existing convention for other `neutral` rows.
- ⚠ It named a real tension and correctly declined to fail on it: `format: integer` on a column the
  warehouse stores as a continuous float. That is exactly what GitLab **#108** now carries, disclosed
  in `decisions_reserved` with the CPO's ruling quoted.
- Checked that no composite or fabricated-probability metric is introduced — the cap is a transparent,
  disclosed bound on a described OLS fit.

## escalations
- **RULED: `severity: warn`.** `escalations.log`, entry
  `2026-09-06 — fix/deserved-points-clamped-to-legal-range — TEST SEVERITY: WARN`. Reached the CPO
  because `scope-auditor` FAILed my analogy-based classification under §10, and because the two
  reviewers had reached opposite conclusions on the same question.
- **RULED EARLIER, and it overturned a decision of mine that had already passed review:**
  *"Rounding is business logic."* Consequence filed as GitLab **#108**; not fixed here.

## ⛔ WHAT THIS BRANCH SHOULD BE REMEMBERED FOR

**1. Every defect came from the blinded review or the test suite. None came from a gate.** At round 1,
`dbt parse`, SQLFluff, `check_description_hygiene.py`, `check_layer_contract.py` and
`check_registry_var_sync.py` all exited 0 over a hand-edited GENERATED file that would have broken
`validate:governance` in CI.

**2. Two sweeps missed by the same method, and the method is the fault.** Grepping the phrase a
reviewer named finds instances of that phrase. It does not find the other statements the change
falsified. Sweeping INVERTED — enumerate every claim about the quantity, ask whether each is still
true — found what two reviewer-named sweeps had left, including one defect no reviewer reached
(`DeservedHero.astro:97`, corrected in the impact map).

**3. A blanket find-and-replace edits quoted strings too.** Twice on this branch: once corrupting
meaning I had to strike, once corrupting the citation to the ruling record itself.

**4. A wrong decision of mine passed two blinded reviewers and was caught only by the CPO.** I wrote
"the integer domain is a display property, and stays one" while pointing at a frontend defect as the
evidence for it. Reviewers check the diff against the contract; they do not check whether the
contract's own premise is right.
