# Review — chore/delete-stale-architecture-doc — 2026-08-07

diff_sha256: db054726563a345d038bbae86ba1d70baf226cd2057ec03bf72635d767cd2ec8

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAILed on a false `done_when` claim: it asserted that
  `grep -rn 'pipeline_architecture_plan'` over the tree returns nothing outside `.claude/task/` and
  git history. One hit existed — `site/fixture-list/index.html:6`. The grep behind the claim was
  `--include`-limited to `*.md`, `*.py`, `*.yml` and `*.json`, so it never looked at `.html`.
- Closed in round 2 by correcting the CLAIM rather than the file: the criterion now names the exact
  unscoped command, the expected count of one, and the exact file and line. The reviewer re-ran it
  and got the same result.
- The frozen-tree exclusion verified against the standing rule rather than accepted:
  `.claude/active_work.md:211` says "Do NOT touch `site/` (retired/frozen)", and `CLAUDE.md:29`
  and `:61` both record `site/` as retired, offline and frozen since 2026-07-21. Editing a comment
  inside a dead, unserved directory would be scope creep against a CPO ruling, for a reference
  nothing runtime reads. Declining is correct, not a dodge. `site/` was deliberately NOT added to
  `scope_paths`, since that would authorise touching the frozen tree.
- The deletion judged justified rather than destructive: the reviewer read the file from
  `git show main:docs/pipeline_architecture_plan.md` and confirmed it teaches the banned pattern.
  It further confirmed that the one piece of still-live knowledge in it — the form-window CPO
  decisions — is already carried by `CLAUDE.md`, so nothing true is lost with the file.
- The two DELIBERATE NON-DELETIONS from the audit's list checked and judged honest, not a builder
  quietly narrowing an instruction. `docs/api_football_ingestion_blueprint.md`: grepped, contains
  no `RAW_APIF_{LEAGUE_CODE}` or per-confederation pattern, carries the stale "20–50 API calls"
  figure at line 120 as claimed, and `ingestion/api_football/loads/batch_fixtures.py:24` does point
  at it as the live API spec. The two unversioned `~/.claude/hooks/` files are the open subject of
  GitLab #21.
- The removed `CLAUDE.md` paragraph's own claim verified as stale: no file matching
  `gh_pages_match_preview_*.plan.md` exists in the repo, so the paragraph warned about a file that
  was already gone while pointing at a second nobody had deleted.
- `review_routing.json` checked: `docs/**` and `CLAUDE.md` match no row, so `scope-auditor` is
  correctly the sole required reviewer.
- `decisions_reserved` deferring `docs/match_preview_pages_refinement.md` and the
  `seo-expert-reviewer` routing question judged a legitimate scope boundary rather than a dodge —
  neither was on the audit's list and both are named for later action.
- Round-2 delta scope confirmed from the patch's `diff --git` headers: the same three files as
  round 1, no new file, no widened `scope_paths`, no reopened decision.

## escalations
(none)

## Note on the class this branch failed on
The round-1 FAIL is the SIXTH #904-class claim from this builder in two days, and the SECOND with
this exact shape after "this repo has NO linter" earlier the same day. Both were a grep scoped
narrower than the sentence it supported, then reported as exhaustive. The rule that would have
caught both, now recorded in `escalations.log`: a claim of ABSENCE must state where it looked, and
the scope must be as wide as the claim. Six instances against a written rule is the evidence that
prose is not fixing this one.
