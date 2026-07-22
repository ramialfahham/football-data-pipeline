# Review — chore/guardrails-cover-design-surface — 2026-07-22

> Required reviewers per `.claude/review_routing.json`: `scope-auditor` (always) + `cto-reviewer`
> (`.claude/hooks/**`, `.claude/settings.json`, `tests/**`). The opus-on-guards rule applies, so
> `cto-reviewer` ran at **opus** on every round. No other specialist routes here: no dbt model,
> no seed, no ingestion path, no wireframe is touched.
>
> **NINE rounds.** Both reviewers were re-run cold on every hash change, as the rule requires.
> The cto-reviewer returned FAIL on rounds 1 through 6 and 8, finding **19 real defects**, several
> of which would have shipped a guard that was broken or a document that lied about it. The
> scope-auditor returned FAIL on rounds 2 and 5 through 7. Round-by-round detail below, because
> the cost of this cycle is itself a live question for the CPO and the record should be honest
> about what the money bought.
>
> **What the reviews caught that would otherwise have shipped:**
> - A GUARD HOLE OPENED BY A GUARD-HARDENING PR: `SessionStart` was first wired to a script under
>   `docs/portable_guardrails/`, which is neither a PROTECTED prefix nor routed for review. That
>   would have made a script that auto-executes at every session start editable in any ordinary
>   task — the exact class of the `.claude/commands/` and `.mcp.json` rulings.
> - FOUR SUCCESSIVE BYPASSES OF THE SAME CLASS in the contract scanner: bare `>` and `|`, then a
>   missing case-fold on `none`/`n/a`/`TBD`, then the dash-list spelling, then the YAML chomping
>   suffix `>-` (which this repo's own workflows use). Each was patched as an instance until
>   round 7, when the class was closed with a pattern instead of a word list. **That churn is the
>   builder's fault, not the reviewer's, and it is the single biggest driver of this round count.**
> - THREE FORGEABLE KEY ORDERINGS in the same scanner, each letting a contract manufacture the
>   `impact_map` this task makes load-bearing on every guard edit.
> - A CHARACTERS-VERSUS-BYTES BUG in the SessionStart hook, invisible to an ASCII fixture.
> - TWO UNAUTHORISED RULES smuggled into the working agreement beyond what the plan approved.
> - The committed suite covering only the ALLOW direction of the protected-path change, three
>   times over, which is the exact trap this contract's own `done_when` names.
> - `docs/agent_guardrails.md` presenting four never-installed hooks as working, and an install
>   procedure that would double-fire the handover injector.
> - `CLAUDE.md` and `.claude/task/TEMPLATE.md` left contradicting the gates this PR ships —
>   the template would have denied PART 2 at its first publish.
>
> **One governance disagreement, escalated and ruled.** The scope-auditor FAILed rounds 5-7
> holding that the four new mechanisms had to be re-escalated before merge, because §11 requires
> escalation BEFORE implementation and these were answered in conversation and recorded after.
> Put to the CPO with the reviewer's position stated fairly and a recommendation to overrule.
> **CPO: "do it."** Recorded verbatim in `escalations.log`, together with the two things the
> reviewer was right about that are adopted regardless: escalations get written before the code
> from here on, and the commit gate has no way to express an overruled FAIL — so the honest route
> was to bring the reviewer the ruling and let it re-verdict, never to soften a recorded verdict.
>
> **Deliberately NOT taken, recorded as follow-ups rather than another round:** two exotic YAML
> indicator spellings that appear nowhere in this repo; an allow-fixture whose body line opens
> with an indicator; pinning the three insurance flag-clears with tests for the reordering they
> insure against; and the `isinstance` guard `stop_gate.py` did not get (spawned as its own task,
> since that file is out of scope here and the gap cannot wedge anything today).

diff_sha256: 9f6285af7f925433953cd38cc734cc55c36de662d9b0eab8e1246791bc257f68

## scope-auditor
VERDICT: PASS
risks_checked:
- Control-flow enforcement of the dual gate on protected paths, on BOTH write paths. The original bug was that the protected branch returned early after checking `protected_override`, making the `impact_map` check below it unreachable — so adding protected paths to `_is_structural` alone would have changed nothing. Verified the check now sits INSIDE the protected branch before the allow (Edit path) and that `_is_structural` covers protected paths for the shell path, and that both directions are tested: override without a map is denied, override with a map is allowed.
- Artifact-gate bypass resistance on reserved-content detection. Verified the `_NULLISH` set is now SHARED between `_impact_content` and `_reserved_content` so the two cannot diverge again, that `_BLOCK_HEADER_RE` closes the block-indicator class by pattern rather than enumeration, that `_has_real_reservation` removes placeholder spans before checking rather than latching a flag (which previously swallowed real entries after an unclosed bracket), and that both helpers strip a leading dash so the list spelling cannot slip through.
- Also checked clean: no scope creep across the nine `scope_paths`; every §10 decision carries recorded authority in `escalations.log` including the CPO's ruling on the post-hoc deviation; the `impact_map`'s claims are evidenced rather than asserted, including the verified statement that `stop_gate.py` imports neither changed function; and every document this PR touches is synchronised with the code it describes.

## cto-reviewer
VERDICT: PASS
risks_checked:
- The one load-bearing flag-clear is pinned by a non-vacuous test. Verified line by line that removing `in_impact_block = False` from the `scope_paths:` branch lets a stray indented non-item line inside the scope list fall through to the impact-content check and forge the map, failing `test_scope_paths_closes_an_open_impact_block`; with the clear present, the edit is denied. Also enumerated every branch that `continue`s before the impact check and confirmed every column-0 key now closes an open block, so the forging class is closed rather than this instance.
- The sibling Stop hook's import surface is untouched. `stop_gate.py` reads only `contract["scope"]` and `contract["protected_override"]`; the new `decisions_reserved_present` key is purely additive to `_read_contract`'s return, so the second Stop hook cannot break on it.
- Fail-open and re-run safety in all three hooks. Each `main()` wraps event read, root resolution and dispatch in one `try/except` returning 0, all three are read-only against the repo (the only subprocess is `git status`), so a second run gives the same verdict and dying halfway leaves nothing to clean up. Verified the four documented claims about the untouched portable archive are each true at source.
- Guard integrity and cost. Exactly the nine declared paths plus the two gate-exempt task artifacts are touched; no workflow, no `requirements*.txt`, no routing file, no permission widening, no credential-shaped string. The three recurring costs (the SessionStart injection at every start, resume and compact; one extra assistant turn per plain-language block; a bounded transcript tail read per turn) are all in the contract's `blast_radius` with a CPO-approved removal criterion.

## escalations
- question: The four new mechanisms (protected-paths-as-structural, the artifact gate, the plain-language gate, the SessionStart wiring) are §10 "NEW mechanisms". The scope-auditor held across three rounds that §11 requires them to be escalated BEFORE implementation, that these were directed in conversation and recorded afterwards, and that a transparent post-hoc record plus an offer to re-escalate does not substitute for asking first. It asked for all four to be re-put to the CPO before merge. Two conflicting paths were put to the CPO: (a) overrule the reviewer, merge, and record the ruling; (b) re-escalate the four formally before merging. Recommended (a), on the grounds that the alternative is asking him four questions he had already answered the same day, which is the failure this session's retrospective identified.
  CPO ANSWER: "do it" (conversation, 2026-07-22) — path (a). The deviation is accepted, the four mechanisms stand as recorded, no re-escalation. Full record in `.claude/task/escalations.log`, including the two practices adopted because the reviewer was right about them regardless of being overruled.
