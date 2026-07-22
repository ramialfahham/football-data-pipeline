# Review — chore/route-display-reviewer-to-built-pages — 2026-07-22

> Required reviewers per `.claude/review_routing.json`: `scope-auditor` (always) + `cto-reviewer`
> (`.claude/review_routing.json`, `.claude/agents/**`, `tests/**`). Opus floor APPLIES: the diff
> touches guard paths, so every cto-reviewer round ran at opus.
>
> **WHAT THIS CHANGES.** `bi-analyst-reviewer` enforces the binding rule in
> `docs/wireframes/00_overview.md`, titled "the whole point": a block may reference only fields that
> exist in today's exported data, and anything missing is NEVER SILENTLY DRAWN. It was routed to the
> wireframe DOCUMENTS only. So the fake planned earlier on 2026-07-22 — two real metrics typed into a
> committed sample so a page looked finished while the pipeline could not feed it — drew
> `[cto-reviewer, scope-auditor]`, neither of which checks whether a displayed field exists. The rule
> was enforced on the document describing a page and not on the page. This routes `site_v2/src/**` to
> the display reviewer, widens that reviewer's brief to built pages, syncs the three other statements
> of its territory, and adds tests that pin the whole routing table.
>
> **FOUR ROUNDS, and what each cost.**
> Round 1: both reviewers FAILED, and both were right. The scope-auditor refused my authority — I had
> claimed it from the CPO's rhetorical question *"So you suggested something that is not needed?"*,
> which is not a discrete answer, and routing a reviewer at a new path class is a §10 rule extension.
> That is the SECOND time in one day on the identical mistake, three hours after the metric rename was
> caught the same way, in a contract that quotes that very lesson back at itself. The cto-reviewer
> found the route itself incomplete: I had listed pages, components, data and i18n and missed
> `site_v2/src/lib/`, which holds `metricRows.ts`, the CPO-locked 16-row display contract. Fabricating
> a metric takes a row in `metricRows.ts` AND a key in the sample, so I had routed the sample and not
> the contract, catching half of a two-file fake. SEVEN tracked files were missed. Root cause: my
> `refs` claimed verification against two paths that DO NOT EXIST — files I intended to create. I
> verified against an imagined tree.
> Round 2: scope-auditor PASS. cto-reviewer FAIL, six findings, all fixed.
> Round 3: scope-auditor PASS. cto-reviewer FAIL, two findings, both accepted and both recorded below
> because they are the same class as everything else today.
> Round 4 (this hash): both PASS.
>
> **ROUND 3, and it is the recurring defect once more.** (F1) The test that claims to pin every
> routing pattern compared the live table against a hand-typed set literal, not against the
> parametrized cases it claimed to guard. Two patterns sat in that literal with no case pinning them:
> `site_v2/**` and `dbt_project/seeds/competition_registry.csv`. Concretely — delete the
> `site_v2/**` route today and the entire suite stayed green, while frontend build config silently
> lost platform review. A docstring asserting it pinned EVERY pattern while pinning 20 of 22, in the
> file whose whole thesis is "enumerate the real tree". (F2) The cry-wolf direction was still a
> three-item hand list, which already missed `package-lock.json` and `.gitignore`. One direction
> enumerated from `git ls-files` and the other from a literal is the same defect at half scale.
>
> **THE FIX IS THE CLASS IN BOTH CASES.** The pin cases became a module constant and the coverage test
> now DERIVES from it with the real `fnmatch`; the hand-typed literal is gone. I did not take the
> reviewer's proposed predicate, which counts a pattern as covered on a path MATCH alone — that would
> mark `site_v2/**` covered via `site_v2/src/lib/metricRows.ts`, whose only assertion is
> `bi-analyst-reviewer` and which says nothing about the CTO route. The shipped predicate requires a
> case that both matches the pattern AND asserts a reviewer that pattern actually confers. The
> reviewer re-derived all 22 patterns against all 22 cases and confirmed it, including the four real
> overlaps. The cry-wolf test now enumerates `git ls-files site_v2`, filters to non-`src/` files, and
> guards against a vacuous pass.
>
> **VERIFIED BY EXECUTION, not by claim.** Full suite: 215 passed. The guards were then proved to
> BITE, in-process against mutated copies of the real routing: deleting `site_v2/**` fails its pin
> case; deleting the registry-seed route fails its pin case; adding an unpinned route fails the
> coverage test; and narrowing `site_v2/src/**` back to a pages-and-data directory list leaves 21
> tracked files escaping the display reviewer. Baseline clean on all four. The cto-reviewer confirmed
> these outcomes follow from the code rather than from the run.
>
> **KNOWN LIMIT, accepted not fixed.** A NEW route that happens to be matched by an existing pin path
> AND confers that pin's reviewer would be absorbed without failing the coverage test. Proving each
> route individually necessary needs mutation testing, which is over-engineering for this surface.
> Recorded because the docstring defines "pinned" exactly as the code implements it and does not
> overclaim — which is the defect this very round was about.
>
> **NOT VERIFIED.** No dbt, no BigQuery, no warehouse object: this change touches none. The one thing
> running locally that matters is `pytest tests/`, and `.github/workflows/python-ci.yml` runs it on
> every pull request with no path filter, so CI re-runs the same gate closed.

diff_sha256: be6165c4b491426681a6fbfc6340d3550e1e23b26487c6d748f238743cb33000

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope and authority of the round-3 edit. Confirmed `tests/test_governance_hooks.py` is in `scope_paths` by a recorded amendment whose authority covers this edit, and that `.claude/review_routing.json` was NOT touched again in this round. Checked both ADDED pin cases against the live routing file to confirm they document routes that already exist rather than legislating new ones through a test, which would be a §10 decision taken silently. Judged the absence of a further contract amendment correct: no scope widened and no claim in the contract became false.
- Pattern-matching overlap at the `site_v2/**` versus `site_v2/src/**` boundary, verified against the real `required_reviewers` hook rather than a mock. Both directions are enumerated from `git ls-files`, not hand-written lists, which eliminates the bug class that caused the round-1 miss.
- Coverage enforcement over incomplete pattern enumeration. Verified the two-part gate — a case must both match a pattern and assert a reviewer that pattern confers — and that coverage derives from the real routing file rather than a second hand-written list, which is what had drifted.

## cto-reviewer
VERDICT: PASS
risks_checked:
- F1 fix, and whether the shipped predicate can go green falsely. Accepted the builder's objection to my own proposed derivation as correct: a path MATCH alone certifies nothing about the reviewer. Enumerated all 22 routing patterns against all 22 `PINNED_CASES` entries and confirmed every pattern is pinned by a case whose assertion that pattern confers and no other matching pattern confers — checked the four real overlaps individually (`scripts/export_site_data.py`, `metric_catalogue.csv`, `competition_registry.csv`, and `site_v2/src/lib/metricRows.ts` against `site_v2/package.json`). Deleting any single route today fails a pin case; adding an unpinned route fails the coverage test. Both follow from the code, not from the run. Vacuity checked in both directions.
- F2 fix. `git ls-files -z site_v2` filtered on the `site_v2/src/` prefix now puts `package-lock.json` and `.gitignore` — both missed by the old three-item literal — into the checked set, along with anything added outside `src` later; `assert outside` blocks a vacuous pass. Verified `git ls-files` emits forward slashes on Windows so the prefix filter cannot silently empty the set.
- Model-versus-system risk, the root cause of the earlier rounds. `required_reviewers` calls the real `_required_reviewers` in `.claude/hooks/git_discipline.py`, not a reimplementation, and `scripts/check_task_artifacts.py` carries byte-identical matching logic, so hook, CI backstop and test cannot diverge. The hook import is side-effect free.
- Dead import and docstring truthfulness. `import fnmatch` is now live at its sole use. The replacement docstrings no longer claim more than the code enforces, which was the substance of F1.
- Fail-open versus fail-closed, unchanged and correct in both directions: the local hook fails open so a corrupt routing file cannot lock the workflow, while CI fails closed. The new parse test closes the gap that asymmetry left.
- Cross-file consistency of the reviewer's territory, grepped repo-wide rather than taken from the contract's claim: routing, agent frontmatter, the territory line and `docs/agent_guardrails.md` all agree; `docs/metrics_context_model.md` and `.claude/agents/cto-reviewer.md` are about ownership and remain accurate untouched.
- Scope, mechanism, cost and secrets: no new package, class, workflow step, dependency, credential or permission. Cost delta is one sonnet reviewer per future `site_v2/src/**` commit, inherent to the approved ruling.

## escalations
- question: Should the display reviewer review the BUILT frontend as well as the wireframe specs? Put discretely via AskUserQuestion with three paths: everything under `site_v2/src`; pages and data only; or no change. Recommended everything under `src`, because a directory list is precisely what had just been got wrong, and build config lives outside `src` so it stays excluded without needing an exception list.
  CPO ANSWER: "Yes, everything under site_v2/src" (AskUserQuestion, 2026-07-22). Full record, including the rhetorical question I first wrongly claimed as authority, is the entry for this branch in `.claude/task/escalations.log`.
