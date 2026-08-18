# Review — fix/74-nightly-image-tracks-main — 2026-08-18

diff_sha256: 0ad82ad32c8b0a0ed882f652770df17ec741ca1e862480045d56bc814a79c60b

rounds: 3

> Rebind-only follow-up to the merge commit (f23313e). Per this repo's documented rule, a merge
> moves its own base — CI's `check_task_artifacts.py` recomputes `diff_sha256` over
> `gitlab/main...HEAD`, which differs from the pre-commit local hash bound in the merge commit
> itself. Recomputed with `python .claude/hooks/git_discipline.py --staged-hash` after fetching
> the live `gitlab/main`; also picked up one newly-required reviewer (`cto-reviewer`, since
> `.gitlab-ci.yml` is now in the diff against the new base) that the pre-merge local computation
> didn't surface. All content below is a genuine re-verification against the final merged state,
> not a restatement — every reviewer re-read the actual current diff.

## scope-auditor
VERDICT: PASS
risks_checked:
- The merge conflict-resolution files (contract.md, review.md, review_input.patch,
  escalations.log) are task artifacts, exempt from scope_paths; `.claude/active_work.md` is
  properly in scope_paths and its manual-merge content is faithful to both streams — the #62
  competitions-page section and the #74 ingest-cluster section are both fully present, neither
  overwrites nor drops the other.
- decisions_reserved is `none`, consistent with nothing in the diff being a product/naming/
  permanence call. The one new §10-class item (the CI build+deploy mechanism, recurring cost,
  IAM grants/revocations) carries explicit CPO authority in escalations.log, not smuggled in.
- The CPO-locked `acceptance_criteria` field addition carries a proper §11 two-path escalation
  in escalations.log ("RE-ESCALATED, two real paths"), corrected after two earlier FAILs on
  this same point — verified the correction actually holds, not just re-asserted.
- No credential-shaped literals anywhere in the diff — all matches are guard/exclusion-pattern
  discussion (`.dockerignore`, `.gcloudignore`), not actual secret values.
- Out-of-scope-looking files (dbt_project/**, site_v2/src/**, docs/wireframes/**) traced to the
  #62/gaps-register merge-inherited content, corroborated against git log merge commits — not
  new authorship on this branch, no scope defect in the merge itself.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- `dbt_project/**` in this diff is #62's merge-inherited content, judged on its merits as
  warehouse code rather than re-litigating #62's own already-approved design.
- `mart_competition_index.sql`'s layer placement (5_marts, denormalization for a single named
  consumer) matches `dbt_project/docs/layering.md`; grain + column tests present in `shared.yml`.
- Cross-layer `ref()` legality checked on every touched base/core/mart model — base models only
  add a `country_name_overrides` seed ref (no dim/fct/mart refs); the mart only refs core +
  seeds, never staging/base directly.
- Base-prepares/dim-publishes discipline followed for the country-name correction, matching the
  existing `team_name_overrides` pattern; no `coalesce`-style correction added inside any dim.
- `single_country` removal swept clean — the five remaining repo hits are prose/comments, no
  live SQL reference; the new `relationships` test in `core.yml` targets a column that actually
  exists on `dim_country.sql`'s terminal select.
- No hardcoded competition identifiers above staging found in the touched models.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Export → mart binding: `export_site_data.py`'s `_COMPETITION_INDEX_KEEP` tuple matches
  `mart_competition_index.sql`'s SELECT list column-for-column; no field the frontend renders
  is fabricated.
- Committed sample (`competition_index.json`, 48 rows) carries exactly the declared 14 keys on
  every row, values within the declared enums — not a hand-typed sample wearing a data-file
  costume.
- `.claude/task/rendered_page_evidence.md` is present and substantive for this `site_v2/src/**`
  diff — built output read directly, screenshot unavailability stated with reason and the
  actual substitute methods named.
- A real rendering defect (region-filter label overflow at 375px) was caught and fixed by that
  evidence-gathering, not by a code read alone — the class of defect this hunt exists to catch.
- No naked percentages/metric creep (page renders no metrics at all); nulls fall back honestly,
  never fabricated; all 22 new i18n keys present identically across all three locales; the new
  nav link is the only nav item with a real `href`, independently confirmed via the accessibility
  tree on two different pages.

## platform-reviewer
VERDICT: PASS
risks_checked:
- `.gitlab-ci.yml` is unchanged by this merge — verified the exact byte positions of the anchors
  and jobs already reviewed in earlier rounds still resolve identically; that review stands, not
  re-derived.
- Zero conflict-marker residue anywhere in the working tree; `.git/MERGE_HEAD`/`MERGE_MSG` were
  present pre-commit, consistent with a clean merge resolution.
- Nothing in platform's territory (`.claude/hooks/**`, `.github/workflows/**`,
  `check_task_artifacts.py`, `.gitignore`, `firebase.json`, `astro.config.mjs`) appears in the
  diff beyond #62's own already-reviewed `export_site_data.py`/`check-page-specs.mjs` additions.
- No dependency/lockfile change; no credential widening (the only credential-adjacent change is
  subtractive — excluding the two CI-generated files from the kaniko build context and the
  manual-fallback upload).
- Acceptance-gate arithmetic verified to actually hold under the merged state: 8 criteria vs 9
  demonstrated bullets in `acceptance_evidence.md`, not merely claimed.
- Confirmed `diff_sha256` shifts once the merge commit lands (CI's `origin/main...HEAD` base
  moves to main's new tip) and must be rebound in a follow-up artifact-only commit — this file
  is that follow-up; fail-closed CI behaviour, not a bypass.

## cto-reviewer
VERDICT: PASS
risks_checked:
- `.gitlab-ci.yml`'s final merged state carries exactly the two hunks already reviewed across
  three earlier rounds (`.data_paths_image` anchor; `build:nightly-image` + `deploy:nightly-image`
  jobs), both pure additions — no third hunk, no smuggled edit; `workflow:`, the shared anchors,
  `validate:secrets` and the existing deploy jobs are untouched, standing as main's version.
- `protected_override` (the CPO's 2026-08-17 "fix #74 so the image tracks main" instruction) and
  a non-placeholder `impact_map` both survived the conflict resolution intact.
- New mechanism (CI build+deploy, redesigned mid-task from Cloud Build to kaniko) traced to the
  CPO's in-session choice in escalations.log, not asserted from the builder's own judgement.
- IAM footprint verified against escalations.log's additions-only diff: final state (run.developer
  + run.invoker on the fdp-nightly resource, iam.serviceAccountUser self-actAs,
  artifactregistry.writer on one repo) matches the revocation entries; the project-level
  cloudbuild.builds.editor escalation path is recorded as found, revoked and verified — nothing
  re-widened by the merge.
- Recurring cost (kaniko runner time, uncollected Artifact Registry storage, no retention policy)
  declared and unchanged by the merge.
- Guard invariants hold: both new jobs fail closed; `needs:` now includes validate:secrets +
  lint:python, strengthening rather than weakening the secrets gate; the deploy-reachability
  test's two-name exclusion is a narrowing (by name, existence-asserted, mirror-pinned), not a
  deletion — consistent with "never loosen a guard".
- No other guard-path file in the diff (nothing under .claude/hooks/, .claude/agents/,
  .claude/commands/, .claude/settings.json, .claude/review_routing.json, .mcp.json,
  .cursor/mcp.json, .github/workflows/) — the merge did not slip a second guard change through.
- Zero conflict-marker residue; no deletion in .gitlab-ci.yml, .dockerignore or .gcloudignore.

## escalations
(none new this round — the CPO-locked `acceptance_criteria` escalation is recorded in full in
`.claude/task/escalations.log`, "RE-ESCALATED, two real paths", per §11; not restated here since
reviewers do not judge the review's own paperwork.)
