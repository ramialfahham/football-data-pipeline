# Review — fix/i18n-copy-gate-defects — 2026-08-06

branch: fix/i18n-copy-gate-defects
diff_sha256: fb1fe69bb436062a8de93bc03956e97a29c656ce42350c968c59fe82163158df

rounds: 3

> PR 1 of 2. Clears every defect `scripts/check_copy_gate.py` reports on `main` — 16 findings,
> 14 of them em dashes across all three locales — so PR 2 can wire the gate into `.gitlab-ci.yml`
> without turning the default branch red.
>
> ROUND 1 FOUND A REAL DEFECT. `bi-analyst-reviewer` FAILed the German restructure: splitting
> `"Jede Kennzahl … zur Vorsaison — kommt mit dem nächsten Release."` at the em dash tore the
> subject away from its only finite verb, leaving `"Kommt mit dem nächsten Release."` — a
> subjectless finite verb, which German reads as an imperative. EN `"Landing…"` and FI
> `"Tulossa…"` are non-finite fragments and split safely; German was the one locale where the
> dash separated a real subject from a real verb. Fixed in round 2 by deleting the dash.
>
> The reviewer's OWN suggested alternative was not taken: it proposed joining with a comma,
> which is itself a German subject/verb comma error. Round 2 confirmed the shipped fix avoids
> both traps.
>
> ROUND 3 was triggered by a GATE REFUSAL, not a finding — see the scope-auditor section.

routing:
  - scope-auditor — `always`
  - bi-analyst-reviewer — `site_v2/src/**`

  cto-reviewer and platform-reviewer were NOT run and are not required: no protected path is in
  scope. `.gitlab-ci.yml`, `.claude/hooks/**` and `.claude/agents/**` are deliberately held for
  PR 2, which is where the guard wiring lives.

## scope-auditor

VERDICT: PASS

rounds: PASS (1, full) · PASS (2, delta) · PASS (3, delta — contract only)

Round 3 was triggered by the acceptance gate refusing the commit: "5 acceptance criteria
declared, 4 demonstrated". The `acceptance_criteria:` list carried a leading BULLET that was a
note about the criteria ("CPO-approved 2026-08-06 and LOCKED"), not a criterion. The gate counts
bullets. The note moved above the key as a comment; the four criteria are byte-identical.

That edit touched `.claude/task/contract.md`, which is NOT in `hash_exclude_paths`, so the staged
hash moved from `091c06d7…` to `fb1fe69b…` and the round-2 verdicts no longer covered the tree.
Re-binding the recorded hash without re-review would have been exactly the keyhole the delta rule
warns about, so it went back to the reviewer that owns the acceptance block.

risks_checked:
- scope_paths boundary — the diff touches only `site_v2/src/i18n/strings.ts` and `.claude/task/**`,
  both declared before the edits. No protected path, so no `protected_override` is required and
  none is claimed.
- §10 silent decisions — every changed string is user-visible copy, a §10 class. All 16 were put
  to the CPO with their evidence and approved before any edit; the two genuine judgement calls
  (`fi.secForm`, `fi.footerDataSource`) were named as such and ruled individually; the round-1
  German fix was ruled separately.
- amendment honesty, criterion 2 — reworded from "zero U+2014 in strings.ts" to "zero in shipped
  string VALUES". Verified as a builder DRAFTING error, not a softened bar: the original counted
  code comments, which `check_copy_gate.py` does not read (`_ENTRY_RE` matches dictionary values
  only). Measured result is 0 em dashes in shipped values both before and after, so nothing that
  was failing now passes.
- amendment honesty, `fi.footerDataSource` — reversed a CPO ruling that proved impossible to
  satisfy, because the gate advertises a comment exemption its code does not implement. Reason
  recorded rather than the ruling quietly restated.
- acceptance-block format correction (round 3) — verified with tools, not from the builder's
  summary: all four criteria byte-identical against the round-1 baseline, no rewording, no
  softening, no criterion removed. A note-as-bullet is a plausible way to disguise dropping a
  criterion under cover of a gate error; confirmed that is not what happened. `scope_paths`,
  `impact_map`, `decisions_taken`, `decisions_reserved` and the two prior amendments unchanged.
- impact_map evidence — leaf change. `writers: none`; `downstream: 23 files` from an actual grep;
  `layer_rules: none` verified by running `check_layer_contract.py`; `blast_radius: display text
  only`. Short-form evidence appropriate for a leaf.
- undeclared thresholds — none crossed. No new mechanism, no recurring cost, no new external
  surface; declared explicitly in `decisions_taken` because no gate parses that field.
- credentials and secrets — none anywhere in the diff.
- dead-string finding correctly scoped — `comingTitle`/`comingPerformance`/`comingSquad` having
  zero consumers was found during verification and filed as GitLab #17 rather than folded in.
  Deleting user-visible copy definitions is a §10 call. Noting a finding without scope creep is
  the correct discipline.

## bi-analyst-reviewer

VERDICT: PASS

rounds: FAIL (1, full) · PASS (2, delta)

Not re-run in round 3: no source file changed. `site_v2/src/i18n/strings.ts` is byte-identical to
what it passed in round 2, and round 3 touched only `.claude/task/contract.md`.

risks_checked:
- DE `comingPerformance` / `comingSquad` — ROUND 1 FAIL, now fixed. The em-dash-to-full-stop
  split tore the sentence's subject from its only finite verb, producing a subjectless
  `"Kommt mit dem nächsten Release."` German requires an explicit subject in a declarative main
  clause, so the result read as an ungrammatical fragment or a nonsensical second-person-plural
  imperative. Fixing a typographic tell by introducing a grammar error is a net loss. Round 2
  verified the fix: plain dash deletion, subject and verb reunited into one correct verb-second
  sentence, no comma substituted (which would itself be a subject/verb comma error), no dash
  remaining.
- EN and FI equivalents checked and found NOT to share the defect — `"Landing…"` and `"Tulossa…"`
  are non-finite fragments and were fragments before the edit, so splitting does not change their
  grammatical status. This is why German alone diverges and keeps one sentence.
- DE and FI appositive commas in `heroVerdictUnder` / `heroVerdictOver` — the highest-risk edit —
  preserve nominative case agreement in both languages (`Ein Spiel` / `eine Torschussdifferenz`;
  `Tällainen peli` / `maalilaukauksien ero`). No defect.
- placeholder tokens — `{home}`, `{away}`, `{meetings}`, `{record}`, `{round}`, `{team}`,
  `{sotd}`, `{deserved}`, `{gap}` present and unchanged, in identical multisets, in every locale
  for every changed key.
- no em dash remains in any shipped dictionary value; all remaining em/en dashes sit inside `//`
  comments, outside amended criterion 2's scope, confirmed against the gate's own `_ENTRY_RE` /
  `_DICT_RE`. No en-dash substitution was used to dodge the gate.
- corpus corroboration checked rather than taken on faith — `fi.secForm: "Kuntovertailu"` and
  `fi.footerDataSource: "Tietolähde: API-Football"` both verified against real strings in
  `site/i18n/fi.json` (`kuntojakson`, `"Tietolähde ei toimittanut tätä arvoa"`).
- dead-string disclosure verified INDEPENDENTLY with Grep rather than from the evidence file's
  prose: `comingPerformance` / `comingSquad` / `comingTitle` have zero consumers anywhere under
  `site_v2/src` outside `strings.ts`; `TeamPerformance.astro` branches on `hasBench` and falls
  back to `notRankable`. The claim checks out and carries no display risk.
- round-2 patch diffed against round-1 hunk-by-hunk: only the DE hunk changed. Every other hunk —
  EN/FI/DE `aboutWithH2h`, the hero appositives in all three locales, `fi.secForm`,
  `fi.footerDataSource` — byte-identical to what was already checked and found clean.

## escalations

none. Neither reviewer returned an ESCALATE in any round.

## builder findings, not fixed here

1. **GitLab #17** — `comingTitle`, `comingPerformance` and `comingSquad` are referenced by no
   component and render on no built page in any locale. Nine grep hits, all definitions, zero
   consumers. Dead placeholders left behind when the Performance and Squad tabs gained real
   implementations. Still corrected in this PR because `check_copy_gate.py` reads every
   dictionary value regardless of use, so criterion 1 cannot pass while they carry em dashes —
   which means a German grammar defect was found and fixed in copy no user can reach.

2. **For PR 2** — `scripts/check_copy_gate.py` advertises an exemption it does not implement. Its
   message offers "the value needs a comment saying so", but check 4 (`untranslated values`)
   parses no comment. Found when the CPO's first ruling on `fi.footerDataSource` proved
   impossible to satisfy. Belongs to the MR that touches the gate.

## process note — on the guard machinery itself

`scope-auditor`'s round-2 delta re-review completed with **0 tool calls**. It reasoned from the
builder's written summary without reopening the patch, so that PASS certified the builder's
description of the change rather than the change.

`bi-analyst-reviewer`'s round-2 delta used 4 tool calls and states explicitly that it checked the
dead-string claim with Grep "rather than taking the excluded evidence file's prose on faith", and
diffed the patch hunk-by-hunk against round 1.

Both received the same delta framing. One verified it, one did not. `scope-auditor`'s brief
carries the refusal condition for exactly this — *"a delta brief is a cost saving, never a way to
move a change past you while you look through a keyhole"* — and it was not exercised.

In round 3 the same reviewer was told plainly that its round-2 review had used 0 tool calls, was
pointed at its own refusal condition, and was asked to verify the contract diff with tools. It
did, and reported the four criteria byte-identical against its round-1 baseline.

So the behaviour is promptable. That is a real mitigation and also the problem: a reviewer that
verifies only when the builder asks it to is not an independent check, because the builder is the
party with the incentive not to ask. The fix belongs in routing and model choice, not in the
builder remembering to say "please actually look". Recorded on GitLab #10.

This does not invalidate the verdicts: `scope-auditor` passed the same contract in round 1 with
18 tool calls, the round-2 delta changed no field it audits, and round 3 was verified with tools.
