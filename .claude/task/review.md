# Review — feat/competition-group — 2026-09-02

diff_sha256: 612a7b0ee12586b2023fcf8dd2cfbce200bd51cff10131a7a98ebb3b62b63142

rounds: 5

rounds_cap_override: CPO, verbatim — **"round 4"**, then **"round 5"**. TWO overrides, each appended
  to `escalations.log` as a dated entry and each verified there by `scope-auditor`.
  Round 3 FAILed on two live NUMBERED-pool references in `10_home.md`; round 4 FAILed on SIX live
  GENERIC ones. All pre-existing, none introduced here — but this MR retires the vocabulary, so they
  are in scope by the discriminator it set itself. I stopped at the cap each time and brought the
  findings rather than fixing them unauthorised.
  ⭐ **The round-4 FAIL identified the real defect that four of my rounds had missed: FILE ORDER, not
  wording.** The identical sentence is fine at `:387` and broken at `:225` purely because the reading
  rule sat at `:268`. **A reading rule that arrives after what it governs governs nothing.** The
  round-5 fix is ONE relocation — the banner now opens §0 — closing the class at a stroke. Measured
  after: **0** live "pool" uses precede it, down from six.
  ⚠ My own round-3 sweep found only one of the two numbered refs: the regex was `pool ?[0-9]` and
  the other is HYPHENATED — the sixth separator-class miss across two MRs.

## scope-auditor
VERDICT: PASS
risks_checked:
- ROUND 5: confirmed the `10_home.md` delta is a PURE RELOCATION — the banner moved, not reworded
  into something broader, and no other passage altered under cover of the move. Confirmed the
  "round 5" override is recorded verbatim, and the warehouse untouched.
- ⭐ Verified my self-report is NOT self-serving: grepped the whole log for both phrases I admitted
  misstating ("exactly three matches remain", "PASSed rounds 2 and 3") and found each exactly once,
  inside the self-critical entry — so the false count was genuinely never written into the log, and
  my correction of `bi-analyst`'s finding 2 is legitimate rather than spin.
- ROUND 4 (PASS): ran its own span-aware all-separator sweep rather than checking my list; verified
  both replacements are FACTUALLY true (elite = 7 rows; BL1=2024 while the other six read 2025);
  re-derived all 19 group assignments; confirmed seed/registry fidelity and scope.
- ROUND 3 (FAIL, superseded): `10_home.md:203` still asserting "pool 1" as live, before the banner.
- ROUND 2 (FAIL, superseded): "Pool 4 exists" still present-tense under my own retirement banner,
  and my "only pool NAMES are stale" caveat shown to be the convenient reading.
- ROUND 1 (FAIL, superseded): the contract attributed the name `calendar` to the CPO when he had
  only rejected `summer` — a name that lands as a permanent enum across five files.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- ⭐ ROUND 5: ran its own case-insensitive **substring** sweep for `pool` — deliberately not a
  separator-class pattern, so hyphen/underscore/space variants are caught by construction. **Zero**
  live generic uses precede the relocated banner. Then checked every live occurrence AFTER it
  against the banner's stated coverage, and grepped `ACTIVE POOL` specifically — only the banner's
  own reference remains; the two prior live ones are rewritten to "SHOWN GROUP" with GAP-33 pointers.
- Verified the banner's counts against the registry YAML directly (7/3/2/6/1 = 19); checked for a
  dangling pointer at the banner's old location (none); swept the rest of `docs/wireframes/`.
- Binding rule: grepped `export_site_data.py` for `competition_group` — zero matches; confirmed
  `10_home.md` never lists it as a §5 payload key, and that GAP-27/29/30 still read LIVE beside
  GAP-28 SHIPPED, so nothing implies the blocks are feedable.
- Confirmed the round-4 correction is actually IN the log, not merely claimed.
- ⭐ ROUND 4 (FAIL, superseded — and the finding that unlocked this MR): six live generic "pool"
  uses before the reading rule, plus the diagnosis that the identical sentence is fine at `:387` and
  broken at `:225` **purely because of file order**. ⚠ Its second finding — that the false count was
  recorded in `escalations.log` — was itself wrong; the claim lived in my prompt and `review.md`.
  Right on substance, wrong on location, and both traced to my loose framing.
- ROUND 3 (FAIL, superseded): `:203` and `:360` numbered-pool references, one of which my own sweep
  missed.
- ROUND 2 (FAIL, superseded): the retired pool table sits in §0, the section the file calls its
  current authority — which overturned my reservation of the file; and the new open question lived
  only in task paperwork, now GAP-33.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- ROUND 5: confirmed the five warehouse files unchanged; recomputed the banner's counts
  independently from BOTH the CSV and the registry YAML; verified no "pool" token appears in lines
  1–35, so the relocation's own claim holds.
- `grep -r competition_group dbt_project` → only the seed and its schema doc. No model reads it,
  confirming `impact_map`.
- ROUND 4 (PASS): swept the contract for any surviving claim that a dbt test exists — all four hits
  now say none; ran its own separator-tolerant sweep of `10_home.md`; traced `select *` consumers
  and confirmed their outer SELECTs are column-explicit so the column cannot silently propagate.
- ROUND 3 (PASS): character-counted the description at ≈991 against the 1,024 cap; gave a fresh
  judgement that `accepted_values` does NOT belong, `tier` being genuinely Python-only. Raised the
  `protected_override` dbt-test contradiction, since fixed.
- ROUND 2 (PASS): walked Finland, BL2 and Argentina through the rewritten description by hand.
  ⚠ Could not execute the hygiene gate and SAID SO rather than claiming it.
- ROUND 1 (FAIL, superseded): the published description called `europe` "the remaining European top
  flights" — false, Finland being one and sitting in `calendar`.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- ROUND 5: confirmed its four territory files unchanged, and **re-judged the relocated banner now
  that it is more prominent** — it states counts only, carries no `league_code`s, and explicitly
  names `docs/competition_registry.yml` as authority, so it is not a second source. Recounted
  7/3/2/6/1 from the CSV to check.
- ⚠ Flagged one residual, recorded not fixed: the banner's COUNTS would go stale on a future
  onboarding if `10_home.md` is not touched. A property of any aggregate restated in prose.
- ROUND 4/3/2 (PASS): walked the onboarding skill end-to-end as a first-time follower; cross-checked
  the field's four descriptions (registry header, `schema.yml`, `SKILL.md`, the test's enum) for
  drift; swept for any other onboarding walkthrough that could omit the field — `SKILL.md` is the
  only one.
- ROUND 1 (FAIL, superseded): the `onboard-competition` skill — the procedure someone actually
  follows — listed every other registry field but not this one, so following it exactly produced a
  league that fails CI with no explanation.

## platform-reviewer
VERDICT: PASS
risks_checked:
- ROUND 5: confirmed the machinery unchanged, and verified I recorded its own round-4 generalisation
  faithfully — "correct attribution, correct reasoning, correct replacement framing, no invented
  claim."
- ⭐⭐ ROUND 4: generalised my recorded rule and was right to. *"Never pipe a search's stderr to
  /dev/null"* is **narrower than the defect**: that failure and the repo's existing gate-piping trap
  are the SAME mistake — **inferring success from the ABSENCE of output instead of reading the exit
  code.** A command can exit non-zero, print on stdout, and still read as clean. **The general rule,
  replacing both: never infer pass/fail from output or its absence; read `$?` explicitly.** It
  warned that two narrow instance-rules in one family is how this project's documented
  `fix_the_class_not_the_instance` pattern regenerates.
- ROUND 3 (PASS): answered the mid-round-desync question — the gap is real, and the dangerous
  direction is the untested one: a stale FAIL announces itself, a stale PASS does not, and the hash
  could match by coincidence. A process defect worth its own issue.
- ROUND 2 (PASS): verified the corrected `impact_map` against `.gitlab-ci.yml`; confirmed the length
  gate is ONE shared script used by both the Stop gate and `validate:governance`.
- ROUND 1 (PASS): traced both new tests to confirm they go red on a reverted column, and named the
  known hole — a valid-but-wrong group passes both, structurally.

## escalations
(none — GAP-33 registers the open group-selection question in `99_gaps_register.md` and GitLab #101,
on the CPO's explicit "file it, should not block us here". Nothing is escalated as blocking.)
