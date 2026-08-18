# Review — fix/74-nightly-image-tracks-main — 2026-08-18

diff_sha256: 1be7681ba88abf2e9d711e8f79c51c995116e7fdc479d095002be059cc7f1bf3

> Rebind-only follow-up to merge commit ade5a30. The merge moved its own base again — `gitlab/main`
> now already contains the `chore/record-top-players-ruling` follow-up too, so the real delta CI
> checks shrinks back to this branch's own 11 #74 files. Required-reviewer check against
> `gitlab/main...HEAD` confirms only scope-auditor, platform-reviewer and cto-reviewer are needed —
> all three already hold PASS verdicts below against this exact content; no re-review, only the
> hash moves.

rounds: 6
rounds_cap_override: CPO, 2026-08-18 — "Go ahead, main keeps moving faster than the review cycle."
(applies again this round for the same reason: main advanced a fourth time while this MR sat open,
forcing a fourth merge-conflict cycle. No open finding is being carried past the cap — every prior
round closed clean, and this round's two required reviewers both gave fresh PASS below.)

> Round 6 (fourth merge round). `main` moved again — a follow-up merge commit (fa8118e) on the
> SAME source branch as round 5, `chore/record-top-players-ruling` — a documentation staleness
> sweep of `docs/wireframes/10_home.md` only (correcting stale nine/six-board tables and gap
> cross-references left over from an earlier board-count reduction), still no code/model/page per
> that branch's own contract. Nothing in this branch's own #74 CI/deploy work changed.
> `contract.md`'s `acceptance_criteria` gained a fourth merge-inherited-batch note; `amendments`
> records it. Only the two reviewers whose remit the new content touches (scope-auditor,
> bi-analyst-reviewer) gave FRESH verdicts against the current diff below; `analytics-engineer-
> reviewer`, `platform-reviewer` and `cto-reviewer` verdicts are carried forward unchanged since
> none of their territory moved this round.

## scope-auditor
VERDICT: PASS
risks_checked:
- `docs/wireframes/10_home.md`'s diff checked line-by-line against the claim of pure documentation
  correction — no `.astro`/`.mjs`/`.py`/`.sql` touched; content is broader than the amendment's
  one-line summary (also registers GAP-30/32 and records CPO-approved intro copy) but stays within
  the file's established convention of transcribing already-made chat rulings, not deciding new
  ones, and the amendment explicitly disclaims it as inherited, not #74's own authorship.
- `acceptance_criteria`'s fourth merge-inherited batch traces to the same standing authority used
  for the three prior batches — not a new or escalated claim.
- Scope check: every file outside `docs/wireframes/10_home.md`/task artifacts (`.gitlab-ci.yml`,
  `Dockerfile`, `.dockerignore`, `.gcloudignore`, `deploy/nightly/README.md`,
  `tests/test_governance_hooks.py`) matches `scope_paths`; no out-of-scope code/model file touched.
- `decisions_reserved: none` holds — the one product/naming/permanence-shaped content in the diff
  (Top players intro copy, GAP registrations) is attributed to the separate
  `chore/record-top-players-ruling` branch's own CPO rulings, not decided by #74.
- Swept every changed file for credential-shaped strings — only filenames/patterns as exclusion
  entries, no literal secret values; no new mechanism or recurring cost beyond what prior rounds
  already declare with cited authority.

## analytics-engineer-reviewer
VERDICT: PASS (carried forward, round 4 — no `dbt_project/**` or export content moved this round)
risks_checked:
- `scripts/export_site_data.py`'s `fetch_landing_payload` region_rank query checked against
  `mart_competition_index.sql` (unmodified) — served fact, selected plain, matches layering's
  select/filter/group/rename allowance.
- Matchday-selection SQL embedded in the export: known layer-placement question, CPO ruled "ship
  as-is, register the gap" (GAP-32) per §11 escalation — arrives as a closed, authorized decision.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Gap-status cross-references in the corrected summary (GAP-24/25/26 VOID, GAP-27/28/29/30 LIVE,
  GAP-31 WITHDRAWN, GAP-32 registered) checked verbatim against `99_gaps_register.md`'s live
  entries — exact match, no drift introduced.
- GAP-27's citation ("`grep -c team_sk` on the mart = 0") checked directly against
  `mart_leaderboards.sql` — confirmed, `team_sk` absent throughout.
- GAP-30's claim ("`assists` is not a ranked board") checked against the mart's `count_boards`
  list — `assists` is selected as a plain column but absent from `count_boards`, confirmed; the
  corrected rule-example pairing (first board now ranks on `goals`) also checked and accurate.
- GAP-28's "8-column seed" claim checked against `competition_registry.csv`'s header — confirmed.
- The newly-approved Top players intro copy checked against its own three stated constraints (no
  "leader", states the mechanic, names no metric) — all three hold on direct reading; the
  `check_copy_gate.py` guardrails cited for future DE/FI copy (no byte-identical values, no em
  dashes) confirmed present in the script.
- Weakest citation in the diff flagged but not FAIL-worthy: "Top teams renders seven too" draws on
  an out-of-repo mock file and a self-referential note rather than a teams-specific CPO quote;
  judged consistent with the rest of §0 (written generically for "the block") and already flagged
  in-document as caught late ("it took a fourth review round"), not a fresh miss.

## platform-reviewer
VERDICT: PASS (carried forward, round 4 — `.gitlab-ci.yml` and all platform-territory files
unchanged this round)
risks_checked:
- `.gitlab-ci.yml` confirmed byte-identical to the round-4 reviewed state; no drift through this
  round's merge.
- `.claude/active_work.md` last measured under the 16,000-character cap; unchanged this round.

## cto-reviewer
VERDICT: PASS (carried forward, round 3 — `.gitlab-ci.yml` unchanged across rounds 4, 5 and 6)
risks_checked:
- `.gitlab-ci.yml`'s merged state carries exactly the two hunks already reviewed across three
  earlier rounds, both pure additions — confirmed unchanged again by platform-reviewer above.
- IAM footprint verified against `escalations.log`'s additions-only diff: final state matches the
  revocation entries; nothing re-widened by any of the four merges.
- Guard invariants hold: both new jobs fail closed; no other guard-path file in the diff.

## escalations
(none new this round — the `chore/record-top-players-ruling` decisions were made and recorded on
their own branch's session, not this one; this review only verifies they arrived intact via the
merge.)
