# Review — fix/74-nightly-image-tracks-main — 2026-08-18

diff_sha256: a4dc96249243d55a938d6578f184b527c5833fbf56aff6a52cc06d71441cc85a

> Rebind-only follow-up to merge commit ece6c36. The merge moved its own base again — CI's
> `check_task_artifacts.py` recomputes over `gitlab/main...HEAD`, which now already contains
> `feat/shared-competition-order` on the main side too, so the real delta shrinks back to just
> this branch's own 11 #74 files. Required-reviewer check against `gitlab/main...HEAD` confirms
> only scope-auditor, platform-reviewer and cto-reviewer are needed — all three already hold PASS
> verdicts below against this exact content; no re-review needed, only the hash moves.

> Round 4 (second merge round). `main` moved again after the previous merge landed — this time
> `feat/shared-competition-order` (!71, merge commit de393e5) arrived on top of
> `fix/gaps-register-vs-reduced-home-design`. Nothing in this branch's own #74 CI/deploy work
> changed (`.gitlab-ci.yml` confirmed byte-identical by platform-reviewer below); the new content
> is a second merge-inherited batch (`competitionOrder.mjs`+test, `HeroFixtures.astro`, four
> fixture JSON samples, `landing.json`, `export_site_data.py`, `types.ts`, two wireframe docs,
> `.gitignore`), already built and merged to `main` on its own branch. `contract.md`'s
> `acceptance_criteria` and `amendments` were extended to account for it (same standing merge
> authority as the first batch, not a fresh §10 decision). Four reviewers whose remit the new
> content actually touches (scope-auditor, analytics-engineer-reviewer, bi-analyst-reviewer,
> platform-reviewer) gave FRESH verdicts against the current diff below; `cto-reviewer`'s round-3
> verdict is carried forward unchanged since `.gitlab-ci.yml` — its entire remit here — did not
> move this round.

rounds: 4
rounds_cap_override: CPO, 2026-08-18 — "Go ahead, main keeps moving faster than the review cycle."

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope trace: all files touched by #74's own work (`.gitlab-ci.yml`, `Dockerfile`,
  `.dockerignore`, `.gcloudignore`, `deploy/nightly/README.md`, `tests/test_governance_hooks.py`)
  match `contract.md`'s `scope_paths` and the mechanism matches what rounds 1-3 already settled —
  no new content beyond what `decisions_taken`/`amendments` already describe.
- Merge-inherited content (`competitionOrder.mjs`+test, `HeroFixtures.astro`, `types.ts`,
  `export_site_data.py`'s matchday/region_rank changes, the two wireframe docs, `.gitignore`
  fixture entries, the two export test files): read each diff and cross-checked against
  `escalations.log`'s `feat/shared-competition-order` entry (2026-08-18, three CPO rulings:
  shared ordering rule, retiring `_HERO_FIXTURE_LIMIT=12`, and the GAP-32 layer dispute ruled
  "ship as-is, register the gap"). Content matches the rulings exactly — nothing reads as
  hand-authored for this branch under cover of the merge; the four fixture JSON files and
  `landing.json` are accounted for by the same named merge commit (de393e5).
- `acceptance_criteria` amendment (CPO-locked field, §2): the second batch's entry cites "same
  standing authority" rather than a fresh two-path escalation — checked this holds because the
  underlying act (resolving a merge conflict per the CPO's own "merge conflict 70" instruction)
  is operational branch hygiene already authorized, not an independent §10 decision; no product/
  naming call is smuggled in via this field.
- No credential-shaped literal values anywhere in the diff — only guard-pattern additions
  (`.gcp-oidc-token`, `.gcp-credentials.json` exclusions); no IAM widening beyond what
  `impact_map`/`escalations.log` already itemize.
- `decisions_reserved: none` still holds — the one genuinely open judgment call this round
  (GAP-32, matchday-selection-in-export layer placement) was escalated and ruled by the CPO
  in-session and is recorded as an open gap, not silently decided.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- `scripts/export_site_data.py`'s `fetch_landing_payload` region_rank query checked against
  `dbt_project/models/5_marts/shared/mart_competition_index.sql` (unmodified by this branch — zero
  `dbt_project/**` hits anywhere in the patch). `region_rank` is a served fact sourced from the
  `confederations` seed via the mart, selected plain, not computed — matches layering's
  select/filter/group/rename allowance.
- `competitionOrder.mjs`/`HeroFixtures.astro` sort already-served facts (`region_rank`, kickoff
  timestamps); matches the 2026-08-16 CPO ruling (recorded in the mart's own header) that the
  mart publishes ordering *inputs* and the page applies `ORDER BY` — not a new ranking derivation.
- `_HERO_FIXTURE_LIMIT` retirement: `group_upcoming_fixtures` now does grouping only, no slicing/
  date logic; the window restriction moved to the SQL `WHERE`, not a Python loop.
- Matchday-selection SQL embedded in `export_site_data.py` (window selection in the export): this
  is the known layer-placement question — FAILed twice on its origin branch, properly escalated
  per §11 with two conflicting paths, CPO ruled "ship as-is, register the gap" (GAP-32). Arrives
  here as a closed, authorized decision via merge, not a fresh or silent violation; not re-failed
  on that basis. The dispute is stated openly in code comments and the gaps register, not hidden.
- Grep-dressed test check: the prior source-inspection assertion was deleted and replaced with two
  tests asserting real behavior (truncation, region_rank pass-through) — not weakened.
- No hardcoded competition identifiers in changed lines; `league_code` stays the discriminator
  throughout, test fixtures use league codes only as literal test data.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- `region_rank` field binding traced end-to-end: `types.ts` → `export_site_data.py` (queries
  `mart_competition_index`) → `mart_competition_index.sql` (joins `confederations` seed) →
  `confederations.csv` (UEFA=1, CONMEBOL=3). Committed `landing.json` sample matches the seed
  exactly — no fabricated field.
- Four committed fixture JSON samples diffed against a pre-existing sample — identical schema, not
  a hand-typed subset; every `fixture_id` `landing.json` references resolves to a committed file.
- Shared ordering rule not duplicated ad-hoc: `orderUpcomingGroups` and
  `groupAndOrderCompetitions` both delegate to the single `compareCompetitions`; the two other
  `.sort(` call sites in `site_v2/src` are unrelated (roster/dot sorts), not a second
  competition-ordering implementation.
- `HeroFixtures.astro` renders only team names, crests and kickoff time/date — every field it
  reads exists in the committed sample; `region_rank` is consumed only as a sort input, never
  rendered as a naked number; no metric creep.
- i18n keys the component calls are present and complete across all three locales.
- `rendered_page_evidence.md` present and substantive — real build output, per-locale group order
  and row counts, live geometry at 440px, and a real build-gate defect (dead links from a stale
  fixture sample) caught and fixed by the evidence-gathering itself, not a code-read-only pass.
- Wireframe docs match built behavior; `99_gaps_register.md`'s GAP-32 entry honestly records the
  unresolved layer dispute with the CPO's quoted ruling rather than presenting it as settled.

## platform-reviewer
VERDICT: PASS
risks_checked:
- `.gitlab-ci.yml` read directly and cross-checked line-for-line against the diff hunks — the two
  new jobs, `.data_paths_image`, `needs:`, matching `rules:`, shared `resource_group` are
  byte-identical to what rounds 1-3 already settled; no drift through the `!71` merge.
- Territory-file exclusion confirmed by direct grep against the full patch (18 files touched):
  none of `.claude/hooks/**`, `.github/workflows/**`, `check_task_artifacts.py`, `firebase.json`,
  `astro.config.mjs`, `tsconfig.json`, `package*.json`, or any `requirements*.txt` appear.
- `.gitignore` change is purely additive (four new fixture-file negation lines, nothing removed) —
  widens what's tracked, doesn't narrow what's hidden.
- Zero conflict-marker residue; zero credential-shaped literal values — the two ignore-file
  additions are filenames in exclusion lists, not secret values.
- `.claude/active_work.md` measured at ≈14,950 characters, under the 16,000 cap; present in
  `scope_paths`.
- No dependency/lockfile change; the four newly-committed fixture samples are inherited content
  from `!71`, not a new page-count driver authored by this branch.

## cto-reviewer
VERDICT: PASS (carried forward, round 3 — `.gitlab-ci.yml` unchanged this round)
risks_checked:
- `.gitlab-ci.yml`'s merged state carries exactly the two hunks already reviewed across three
  earlier rounds (`.data_paths_image` anchor; `build:nightly-image` + `deploy:nightly-image`
  jobs), both pure additions — confirmed unchanged again this round by platform-reviewer above.
- `protected_override` and a non-placeholder `impact_map` both survived every conflict resolution
  intact.
- New mechanism (CI build+deploy, redesigned mid-task from Cloud Build to kaniko) traced to the
  CPO's in-session choice in `escalations.log`, not asserted from the builder's own judgement.
- IAM footprint verified against `escalations.log`'s additions-only diff: final state matches the
  revocation entries; the project-level `cloudbuild.builds.editor` escalation path is recorded as
  found, revoked and verified — nothing re-widened by either merge.
- Recurring cost (kaniko runner time, uncollected Artifact Registry storage, no retention policy)
  declared and unchanged.
- Guard invariants hold: both new jobs fail closed; no other guard-path file in the diff.

## escalations
(none new this round — the CPO-locked `acceptance_criteria` escalations are recorded in full in
`.claude/task/escalations.log`; the GAP-32 matchday-selection-in-export dispute is a §11
escalation that happened on the `feat/shared-competition-order` branch, arrives here already
ruled and merged, and is not re-litigated by this review.)
