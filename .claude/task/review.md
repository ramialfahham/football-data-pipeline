# Review — docs/handover-retrospective — 2026-07-22

> Required reviewers per `.claude/review_routing.json`: scope-auditor (always). No path-routed
> specialist applies: the staged paths are `.claude/active_work.md` and `.claude/task/contract.md`,
> neither of which matches a `paths` pattern. The commit is NOT review-exempt, because
> `contract.md` is listed in `artifact_only_never` (a contract authorises scope, F10/#409).
>
> Round 1 returned FAIL on two points; both were fixed with judgment rather than escalated.
> (1) `decisions_taken` (3) recorded the work-sequence REORDER — the player page design was step 1
> and now sits behind the governance task and the team-page build — against a bare "go". It now
> quotes the full exchange that "go" answered and states the reorder explicitly.
> (2) The retrospective claimed every logged escalation gives a recommendation. That was WRONG and
> the reviewer caught it: `escalations.log` holds 9 entries that withhold one per §11 and 8 that
> give one. Corrected to "split down the middle", which is accurate and more useful.
> The hash changed, so the reviewer was re-run cold on the new diff.

diff_sha256: 8554f41af22906e23ab30a66e2ea186fde4828567e85832bc6bd8a201af824a1

## scope-auditor
VERDICT: PASS
risks_checked:
- Third-party requests in `site_v2` reach parity with the defect that took the MVP offline. Verified independently by the reviewer: the committed sample fixture carries 14 `media.api-sports.io` URLs (team crests and player photos), and `ui/Crest.astro:18` plus `fixture/PlayerRow.astro:28` render them as `<img src>`. Confirmed the new handover states this plainly and names the privacy-versus-rights tension rather than presenting mirroring as a clean fix.
- The SessionStart delivery claim. Verified independently that neither `.claude/settings.json` nor `.claude/settings.local.json` registers a SessionStart hook, while `docs/agent_guardrails.md` still describes `handover_in.py` firing on one. Confirmed the false claim is removed from the handover and the discrepancy is routed to the governance task as "wire it or delete the claim".
- Also checked and found clean: all three `decisions_taken` carry direct CPO quotes with context; no §10 product, UX, metric or naming decision is embedded as settled without authority; the standing do-nots survive the 85% deletion; and staging `contract.md` alongside the single in-scope file is legitimate, because the contract is the governance artifact authorising the task rather than implementation content.

## escalations
(none)
