# Review — chore/repo-polish — 2026-07-22

> Required reviewers per `.claude/review_routing.json`: `scope-auditor` (always) only. The diff
> touches README.md and docs assets — no dbt, ingestion, script, site or guard path — so no
> specialist reviewer is routed and no opus floor applies.
>
> **WHAT THIS CHANGES.** Presentation only, no code. It makes the public repo honest in its current
> state, for an experienced engineer assessing it as the owner's flagship.
> 1. **Dead links killed.** GitHub Pages returns 404 (verified via `gh api .../pages`), so the README
>    demo link, the dbt-docs link, and the repo homepage URL all pointed at nothing. All removed; the
>    repo description no longer advertises a "live web app".
> 2. **Honest state.** The web app is described as a prototype, currently offline. The retired-MVP
>    screenshot (which showed competition branding, the class of content the app was taken down over)
>    is deleted, and the Mermaid architecture diagram is the lead visual — a stronger image for a
>    data pipeline and rights-clean.
> 3. **The machinery framed.** A new "Development guardrails (AI-assisted)" section presents the
>    contract gate, blinded adversarial review, the hash-bound review artifact, and the
>    fail-open/fail-closed split as a deliberate artifact rather than unexplained over-engineering.
>    This follows the guardrail TRIM (#808), so what it describes now passes its own proportionality
>    test.
>
> **AUTHORITY.** The exact copy and framing are §10 product decisions, so they were put to the CPO
> before writing: two AskUserQuestion rulings chose a dedicated guardrails section (not a whole-repo
> reframe) and a neutral app-status note (no legal reason aired publicly). The shipped copy matches
> both. The repo description and homepage were updated via `gh` with the CPO-approved text, outside
> the diff.
>
> **HONESTY BAR.** Per the presentation principles: no self-praise, no "hire me" framing, honest
> about state, non-brittle numbers. The guardrails section describes what the system DOES in precise
> terms rather than adjectives, and names the one transferable idea (binding a review to its exact
> diff by hash). The reviewer independently checked its three load-bearing claims against
> `working_agreement.md` and confirmed each is accurate, not overstated.
>
> **NOT VERIFIED.** No code, no tests, no warehouse. The skill's link/render checks ran: every
> relative link resolves, the Mermaid block is well-formed and fenced, no github.io link remains.

diff_sha256: f22f5edf277100aa5dd1604997247be1ddd15d8a2e3e7031cd46e44a356f4dc0
rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Authority for the product copy: confirmed the two CPO AskUserQuestion rulings (dedicated guardrails section, neutral app-status note) and that the shipped README matches both — a standalone section rather than a whole-repo reframe, and an "offline" status with no legal reason given. No positioning was written that the CPO did not approve.
- Honesty and dead-link completeness: verified all three dead github.io links are gone with none reintroduced, the surviving badge and internal doc links resolve, the copy claims nothing live that is not, and the guardrails section neither overclaims nor reads as a recruiter pitch.
- Guardrails-section accuracy: checked its three core claims ("spawned cold with no builder context", "defaulting to reject", "an approval cannot drift from the code it approved") against `working_agreement.md` §2-3 and confirmed each is factually correct.
- Scope: every touched file inside `scope_paths`; the two deletions are justified (the screenshot is the retired app; its directory README documented only that screenshot).

## escalations
- question: How prominent should the AI-guardrails framing be, and how much to say about why the web app is offline? Put as two AskUserQuestion prompts with three and two options respectively.
  CPO ANSWER: "A dedicated section, after Design decisions" and "Neutral: prototype, currently offline" (AskUserQuestion, 2026-07-22). The exact README copy was shown before writing and the framing approved.
