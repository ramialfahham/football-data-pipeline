# Review — chore/115-step5-decision-record — 2026-09-11

diff_sha256: 6a4307d3d935d8cc3f0523b7a0bd5fc54c2c319d805e1ac1702c557185f149c4

rounds: 4

cto-reviewer: FAIL ×3 (rounds 1-3), PASS at round 4.
scope-auditor: PASS at round 1, PASS at round 2 (delta), FAIL at round 3 (delta), PASS at round 4.

Hashes: round 1 `30c4b05fa0efb03fc5247c8b0e111ad59fbd37ad563c59bcba2d321eebea0bb6`; round 2
`f627ebfdb0167c266f0946bc44786fa4be4c63cd3af3259373f6e6e55953c9e5`; round 3
`a06d123f9c64e80243860a012cf75162dbb06cdc10d602aa66bdf3e8eb3a74ec`; round 4 above.

WHAT THE ROUNDS WERE ABOUT. No round found a defect in the rule itself — the freeze, the issue as
the requirement, the MR head, the merge as approval were accepted from round 1 (cto-reviewer:
"a disclosed, internally consistent tradeoff"). Every FAIL was about the second copy of a
locked-file approval: round 1 there was none; round 2 it was a hand-set line, a promise; round 3
it was a paraphrase called verbatim. The rule this branch writes — two copies, the CPO compares —
was defended into existence by the reviewers, and the last defect was the exact one it exists to
catch, made by the builder while writing it.

rounds_cap_override: The CPO directed that the context cleanup finish before product work resumes
(his words, quoted in the frozen log's entry `2026-09-10 chore/dead-issue-references`), and the
commit gate refuses a standing FAIL. Round 4 clears round 3's FAIL BY REVIEW rather than shipping
past it, as `!172` and `!173` recorded the same override. ⚠ RECORDED PRECISELY: he did not rule
on the cap itself, and this override does not claim he did.

## cto-reviewer
VERDICT: PASS (round 4)
risks_checked:
- Round 4 PASS: reconstructed both approval spans from `in chat on` to the closing parenthesis
  (contract 25-26; evidence 11-15) and grepped both files for `"Explain like I am twelve" ×3` —
  byte-identical including the `×` and the quote style; round 3 closed. Evidence scopes its claim
  to the Python equality and discloses what stays unverifiable until the commit exists. The
  round-3 amendment names the prior defect without softening it. `rounds_cap_override` worded
  precisely, not used to ship past a FAIL. Full diff re-swept: nine hunks, no hook, script, CI,
  routing, dependency or credential change.
- Round 1 FAIL: (1) rules keep the owning doc and requirements keep the issue as a second copy,
  but a `protected_override` would have had only the contract — and the second copy is what caught
  the misattributions on `!173`. Taken: the MR head's `Locked files` line repeats the quote.
  (2) "typo/refactor gets no issue" was unsourced rule text. Taken: it is the CPO's "some small
  exceptions", quoted in §1. Also corrected: the review prompt wrongly said the contract cites
  `fix/merge-guard-covers-the-api`.
- Round 2 FAIL: the second copy was a template line set by hand after the hook opens the MR — a
  promise, never in a tracked file. Taken: the commit message carries `Closes #N` and the
  `Locked files` line with the quote; `glab mr create --fill` puts it on the MR automatically and
  `git log` keeps it. The reviewer accepted the structure ("tracked, automatic, immutable under
  the no-amend policy") and the ordering constraint that a commit cannot precede its review.
- Round 3 FAIL: the evidence called two strings "verbatim" that were a paraphrase of each other.
  Taken: the commit message carries the contract's span character-for-character; the evidence
  records a Python equality (`IDENTICAL`) on the two spans.
- Held by this reviewer in every round: `protected_override` and `impact_map` present and real;
  fail-open unchanged (no hook touched); routing `.claude/agents/**` → cto-reviewer confirmed from
  the file; no dependency, cost, CI, routing or credential change; the seven other reviewer
  briefs' "carries authority" sentence describes patch composition and is rightly left alone.

## scope-auditor
VERDICT: PASS (round 4)
risks_checked:
- Round 4 PASS (delta): compared the two spans character-for-character — identical from `in chat
  on` to the closing parenthesis, matching the narrow claim now made, not the round-3 overclaim;
  the evidence's quote of `protected_override` matches the live contract via grep; the round-3
  amendment is an admission, not a rewrite; the residual ("until the commit exists") is stated;
  delta confined to the commit-message plan, evidence bullet 2 and the amendments block — scope,
  bullet count and thresholds unchanged.
- Round 1 PASS: scope exact (13 files); `protected_override` + `impact_map` present; the log's
  final entry exists at the cited line and marks the CPO's words apart from narrative; the two
  deleted "appended to `escalations.log`" sentences return zero hits; no instruction to write to
  the log survives in the diff or the wider repo; seven other briefs counted; five evidence bullets
  for five criteria; no secrets; #116 unverifiable from its toolset (no shell), flagged not failed.
- Round 2 PASS (delta): both cto findings addressed consistently across template, §11 table and
  the auditor's own sentence; the "small exceptions" quote dated and placed; amendment honest.
- Round 3 FAIL (delta): the same paraphrase-as-verbatim the cto-reviewer found, read side by side
  as the brief asked. Taken as above.

## bi-analyst-reviewer
VERDICT: PASS (round 4)
risks_checked:
- Routed by `docs/wireframes/00_overview.md`. The six-document reading-order table (file lines
  12-19) and "On conflict: escalate to the CPO … deliberately absolute" (21-23) are unchanged;
  only the paragraph saying where an already-made decision is looked up was rewritten, and it is
  consistent with the document's own mock/issue-axis model (51-54, 56-57) and with "the
  surface's GitLab issue" as the chain's terminal link (table line 19; `CLAUDE.md` row unchanged).
- `metrics_display.md`, `site_v2/src/**`, `site/i18n/` untouched — nine `diff --git` headers,
  none in that territory; no field, layout, metric row, format or i18n string changes, so no
  `rendered_page_evidence.md` applies. The log's banner and final entry match what
  `00_overview.md` and the contract describe: a closed append, no prior entry rewritten.
- ⚠ Not run in rounds 1-3: the routing to this reviewer was missed until the commit gate named
  it. The file it reviews did not change between rounds 1 and 4.

## escalations
- None raised. The one §10 question in the branch — freeze rather than split, against #115's
  "every step ships a mechanism" — was put to the CPO plainly before building and he chose; it is
  recorded in #116 and the contract, not asserted as a ruling.

## Found and NOT fixed, all disclosed in the contract
- Nothing verifies the quote is his — nobody can but him. The two copies make a divergence visible
  to him at merge; that is the whole guarantee.
- The ticked checklist with links is a hand step after the hook opens the MR; if skipped, the MR
  shows the commit message and no checklist, which he sees.
- The seven other reviewer briefs still say the log "carries authority" — patch composition,
  unchanged, left alone.
