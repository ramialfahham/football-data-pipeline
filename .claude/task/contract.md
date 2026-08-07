# Task contract — delete the stale architecture plan, and the prose that existed to warn about it

> Branch `chore/delete-stale-architecture-doc` from `main` (`946dfa5`). No PROTECTED path
> (`CLAUDE.md` is absent from both `PROTECTED_PREFIXES` and `PROTECTED_FILES`,
> `task_contract_gate.py:66-78`), so no `protected_override`. Nothing on the structural surface, so
> no `impact_map`. No `site_v2/src/` path, so no `acceptance_criteria`. Reviewers: `scope-auditor`
> only — `docs/**` and `CLAUDE.md` match no row in `review_routing.json`.

objective: >
  Delete `docs/pipeline_architecture_plan.md`, and remove the always-loaded paragraph in
  `CLAUDE.md` whose only purpose is to warn about it.

  WHY THIS AND NOT A BIGGER SWEEP. A cold re-run of `/audit-agent-setup` on 2026-08-07, given no
  knowledge of the earlier audit's findings, recommended DELETION as its first action. The earlier
  audit had no subtraction in its vocabulary: it produced 29 issues, all of which add. Same repo,
  same skill, opposite first move.

  VERIFIED, not accepted from the audit: the file teaches `RAW_APIF_{LEAGUE_CODE}_{ENDPOINT}`
  (line 61), per-confederation raw tables (28, 62, 74) and "7 per-confederation staging models"
  (122). That is the exact anti-pattern `CLAUDE.md`'s scalability rules and
  `scripts/check_layer_contract.py` exist to reject. It was last touched 2026-06-13, flagged for
  "wholesale archival, not token-patching" on 2026-05-30, and its `MEMORY.md` pointer was removed
  2026-08-06 — but the file itself was never deleted. Decided, never executed.

  THE PARAGRAPH IS STALE IN BOTH DIRECTIONS, which is why it goes with the file. `CLAUDE.md:49-52`
  warns that `gh_pages_match_preview_*.plan.md` "still exists on disk" — it does NOT; no file
  matching it is present. And it points at the `pipeline_architecture_plan.md` pointer removal,
  which this task makes moot by deleting the file. Once the hazard is gone the warning is pure
  always-loaded cost.

refs: >
  Cold `/audit-agent-setup` re-run, 2026-08-07, run in a fresh context with no knowledge of the
  first audit's conclusions, at the CPO's request to test whether the findings are replicable.
  CPO instruction after reading it: **"start with the deletions"**. Not a numbered issue.

scope_paths:
  - docs/pipeline_architecture_plan.md
  - CLAUDE.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  THRESHOLD DECLARATIONS, stated because no gate parses this field.

  NEW MECHANISM — NO. This removes a file and four lines of prose. Nothing is built.

  RECURRING COST — NO, and it REDUCES the standing one: `CLAUDE.md` is auto-loaded every session,
  so the removed paragraph is a per-session token cost paid to warn about a hazard this task
  deletes.

  GUARD INVARIANT — UNCHANGED. No guard, hook, test or routing row is touched. The rule the doc
  contradicts is enforced by `scripts/check_layer_contract.py`, which is not edited and which
  keeps working exactly as before. Deleting a document that teaches a banned pattern strengthens
  the position; it cannot weaken it.

  NEW EXTERNAL SURFACE — NO.

  ⚠ TWO ITEMS ON THE AUDIT'S DELETION LIST ARE DELIBERATELY NOT DONE, because checking them
  contradicted it:

  1. `docs/api_football_ingestion_blueprint.md` — the audit said it "has the same problem". It does
     NOT. Grepped: it contains no `RAW_APIF_{LEAGUE_CODE}`, no per-confederation table or model
     pattern. It was last touched 2026-08-03, and LIVE CODE points at it —
     `ingestion/api_football/loads/batch_fixtures.py:24`, "See docs/api_football_ingestion_blueprint.md
     for the full API specification." Its only known defect is one stale figure at line 120
     ("approximately 20–50 API calls total" against a measured ~8,300), which is already filed as
     #900 and is a fix, not a deletion. Deleting it would have destroyed a live API spec and
     orphaned a code comment.
  2. `~/.claude/hooks/commit_review_gate.py` and `pre_push_gate.py` — unversioned, so deletion has
     no undo, and that whole layer is the open subject of GitLab #21. The CPO's call, not a
     builder's.

decisions_reserved:
  - "`docs/match_preview_pages_refinement.md` references the same retired-MVP plan and may be the
    same class of stale document. NOT investigated and NOT touched here: it was not on the audit's
    list and chasing it mid-task is the drift pattern the CPO corrected twice this session.
    Surfaced so it is not lost."
  - "Whether `seo-expert-reviewer.md` should be routed or deleted. The audit's point stands — it is
    currently neither, which reads as coverage while doing nothing — but routing is a governance
    event (§10) and deleting a reviewer is CPO-class. Not decided here."

done_when:
  - "`docs/pipeline_architecture_plan.md` no longer exists, confirmed with `git status` and a
    filesystem check."
  - "An UNSCOPED `grep -rn 'pipeline_architecture_plan' .` returns exactly ONE hit outside
    `.claude/task/` and git history: `site/fixture-list/index.html:6`. That reference is
    DELIBERATELY NOT FIXED — `site/` is the retired legacy MVP, offline since 2026-07-21 with its
    Pages deployment deleted, and `CLAUDE.md:29,61` plus the standing DO-NOT list forbid touching
    it. A comment inside a frozen, unserved product is not a live pointer, and editing it to tidy
    a reference would break a CPO ruling to fix nothing."
  - "⚠ THIS CRITERION FIRST CLAIMED the grep 'returns NOTHING outside `.claude/task/` and git
    history'. FALSE. The grep behind it was `--include`-limited to `*.md`, `*.py`, `*.yml` and
    `*.json`, so it never looked at `.html`, and the result was reported as if it covered the tree.
    `scope-auditor` caught it. This is the SIXTH #904-class claim from this builder in two days and
    the SECOND with this exact shape — a grep scoped narrower than the sentence it supports, the
    same defect as 'this repo has NO linter' earlier today. The rule that would have caught both:
    a claim of absence must state where it looked, and the scope must be as wide as the claim."
  - "`CLAUDE.md` no longer contains the `gh_pages_match_preview` paragraph, and its false claim
    that the file 'still exists on disk' goes with it."
  - "`python scripts/check_layer_contract.py` exits 0 — the rule the deleted doc contradicted is
    still enforced by the mechanism that actually enforces it."
  - "`python -m pytest tests/ -q` clean, collected count MEASURED, and pytest's OWN exit code read
    directly rather than through a pipe."
  - "The five offline gates pass, and `check_task_artifacts.py` runs BARE."

amendments: (none)
