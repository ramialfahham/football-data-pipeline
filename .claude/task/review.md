# Review — feat/367-landing-page — rounds 1-8, closed 2026-08-09

branch: feat/367-landing-page
diff_sha256: d294d7c1c04b41fe5acebd90af71af68e252061ae1da83f574f60d5b2659dc76

# ⚠ REBOUND 2026-08-14, rebased onto main `2644989`, and the old number was dead for TWO
# independent reasons. (1) The base moved: main gained #53, #61, #63, #33 items 9/14/15, #65 and
# #57 while this branch sat open. (2) **#63 CHANGED THE ALGORITHM** — from hashing the RENDERED
# patch text to hashing CONTENT IDENTITY (`git diff --raw`). The recorded `5524939f…` was the
# rendered-text number and is not comparable to anything CI computes now.
#
# ⚠ A TRAP THIS BRANCH WALKED INTO, recorded because it will recur on any pre-#63 branch: the
# hook runs FROM THE BRANCH, so before the rebase `--staged-hash` was still the OLD implementation
# and cheerfully reproduced `5524939f…`. That looks like agreement and is not. Verified explicitly
# by computing both ways on the same tree: rendered = `5524939f…` (514,774 bytes), raw =
# `73e50633…` (5,697 bytes). **Compute the binding AFTER the rebase, never before.**
#
# The branch was COLLAPSED to one commit before rebasing — the method this branch's own handover
# documents — because 13 of its 15 commits were handover-only edits that would each have re-fought
# the same paperwork conflicts.
#
# Conflicts were the four `.claude/task/*` artifacts plus `.claude/active_work.md`. No code
# conflict. `shared.yml` and `seeds/schema.yml` were touched by BOTH sides and auto-merged; both
# were checked SEMANTICALLY rather than trusted — #57's `confederations`/`competition_types`/
# `single_country`/`label_i18n_key` and this branch's `label_en`/`computation_kind` all survive,
# and this branch's only `shared.yml` change was a trailing blank line.
#
# ⚠ `escalations.log` UNION: this branch does NOT follow the append-only shape the others use. It
# INSERTS 48 lines at the TOP and appends 181 at the BOTTOM. The two-part `main + (mine − base)`
# union that is correct everywhere else would have silently dropped the head block; an assertion
# caught it. Resolved three-part and checked by ARITHMETIC: 48 + 2,508 + 181 = 2,737 lines written,
# with #367, #57, #65, #63, #61 and the oldest 2026-06-12 entry all verified present.
#
# ⚠ `.claude/active_work.md` took MAIN's side, NOT this branch's — the opposite of the rule for the
# other three artifacts, and deliberately. It is not single-owner-per-task: main's copy is current
# (08-14) while this branch's was four days stale and still said "CI IS OUT OF MINUTES". Before
# discarding it, its unique content was checked against the tracker: the design decisions it
# summarised are in **#40** (12,976 chars) and **#41** (13,756 chars), which it names as the
# authority, plus #36/#42/#43/#44/#45 — all confirmed to exist with full bodies. Nothing was lost;
# a compact pointer block replaces the summary.

# ⚠ REBOUND AGAIN 2026-08-09 after REBASING onto `main` at `4ad4513`. The MR reported a merge
# conflict; `main` had merged `perf/33-raw-merge-on-write`. The conflicts were ONLY in the four task
# paperwork files — no code conflict — because that branch wrote its own `contract.md`,
# `review.md`, `review_input.patch` and appended to `escalations.log`.
#
# Resolution: mine for the three task-specific files (they describe THIS task); UNION for
# `escalations.log`, which is an append-only durable record where both sides' entries must survive.
# The union was checked arithmetically, not eyeballed: 1784 (main) + 1862 (mine) - 1633 (base)
# = 2013 lines, which is what the resolved file has, so nothing was dropped or duplicated.
#
# ⚠ MERGE WAS THE WRONG MECHANIC AND WAS ABANDONED. `git merge gitlab/main` pulls main's CODE files
# into the working tree, and the contract gate correctly flags them as edits outside `scope_paths`.
# A rebase replays my commit on top instead, so main's files are simply HEAD and no violation
# fires. The branch was collapsed to ONE commit first, so the paperwork conflicts had to be
# resolved once rather than five times.
#
# ⚠ REBOUND ONCE BEFORE, because I bound it to the wrong number and CI caught it
# (`validate:governance` red, `data:build:mr` green).
#
# The branch is now FOUR commits. `git_discipline.py --staged-hash` hashes `git diff --staged`,
# which after the first commit covers only the INCREMENT; `check_task_artifacts.py` recomputes over
# `gitlab/main...HEAD`, the whole branch. Those are the same number ONLY while HEAD is the
# merge-base. I collapsed the branch to one commit earlier for exactly this reason, then added
# three more commits and reverted to the staged hash without re-deriving.
#
# ⚠ THE TRAP IS DOCUMENTED IN `.claude/active_work.md` AND I READ IT THIS SESSION. The number here
# now comes from `check_task_artifacts.py`'s own recompute, which is what the handover says to use.
# Rebinding is free: `review.md` is in `hash_exclude_paths`, so a review-only commit is
# artifact-exempt and cannot change the value it records.

# BOUND TO THE STAGED INDEX, with HEAD at the merge-base 72a6a69. The branch was collapsed to ONE
# pending commit with `git reset --soft`, deliberately: the local gate hashes `git diff --staged`
# while CI recomputes `git diff base...HEAD`, and those are the SAME number only when HEAD is the
# base. On a multi-commit branch they diverge and one of the two gates always fails.
#
# `check_task_artifacts.py` uses the THREE-dot form, so it resolves through
# merge-base(gitlab/main, HEAD) and is immune to `gitlab/main` advancing — which it did three times
# during the 2026-08-08 session.
#
# The hash covers CODE + `contract.md` only. `review.md`, `review_input.patch`, `escalations.log`,
# `active_work.md` and both evidence files are in `hash_exclude_paths`, so rewriting any of them
# cannot invalidate it.

rounds: 8
rounds_cap_override: Rounds 1-6 ran on 2026-08-08 and were closed by CPO override. Round 7 is a
  REWORK ROUND, not another grind of the same diff: on 2026-08-09 the CPO rejected the premise the
  first six rounds had reviewed — "that's not what we were talking about in the other session. We
  were talking about next atches, top player, top teams, and browse section" — so the page was
  recomposed and every reviewer re-run against a materially different diff. He then authorised each
  fix that followed in the same conversation ("yes, add it to scope and land the fix", "yes to both,
  add the entity column and file the crest issue"). Counting this as round 7 rather than restarting
  at 1 is deliberate: the round counter should reflect how much reviewing this branch has consumed,
  not how many times its premise changed.
  ⚠ THE PROCESS DEFECT THE CPO NAMED ON 2026-08-08 IS STILL UNFIXED: "we have a problem with the
  design of the review rounds." The cap counts ROUNDS while the loop is driven by
  FINDINGS-PER-ROUND, so a reviewer surfacing one instance of a class per round consumes the whole
  budget. Needs its own issue.

  ROUND 8 is a DELTA round forced by CI, not by a reviewer. `data:build:mr` failed on
  `assert_metric_catalogue_expr_resolvable` with `Unrecognized name: computation_kind`: this PR adds
  that seed COLUMN and, in the same PR, tightens the guard that reads it, while the deferred
  singular-test step resolves `ref('metric_catalogue')` to MAIN's seed. The repo had ALREADY RULED
  on this twice — CI notes in `assert_metric_meaning_complete.sql` and
  `assert_metric_direction_lower_is_better_agree.sql` say "the values merge first, then the guard.
  Do not try to solve this with a CI workflow change." The guard is reverted to main's version and
  follows in its own MR. Only the two reviewers whose territory the delta touches were re-run
  (`analytics-engineer-reviewer`, `scope-auditor`), per the delta-review rule.

  ⚠ BEFORE THAT I TRIED THE FORBIDDEN FIX, and it is recorded rather than tidied away. I diagnosed a
  structural CI hole, obtained CPO approval, and opened a governance branch with `protected_override`
  to drop `--favor-state` from the DQ-test step. `cto-reviewer` and `platform-reviewer` both FAILED
  it — my premise was false (the BUILD step already validates the branch's own seed, `10 of 41 PASS`
  against `ci_analytics`) and the change would have created a false-green path on the shared,
  never-cleaned `ci_analytics`. Branch deleted, nothing pushed. My search for prior guidance had
  covered `docs/` only while the ruling lived in `dbt_project/tests/` — a claim of absence must
  search as wide as the claim.

# ROUTING. Five reviewers fired on the staged paths (`.claude/review_routing.json`):
# scope-auditor (always), analytics-engineer-reviewer (dbt_project/**, scripts/export_*.py),
# bi-analyst-reviewer (docs/wireframes/**, site_v2/src/**), platform-reviewer (scripts/**,
# site_v2/scripts/**, tests/**), football-analytics-expert-reviewer (metric_catalogue.csv).
#
# ⚠ ALL FIVE WERE TOLD, IN THEIR PROMPTS, which changed files `review_exclude_paths` strips from
# `review_input.patch` — `active_work.md`, both evidence files, this file. That false positive has
# fired three times historically; absence from the patch is not evidence a file is unedited.

## scope-auditor

VERDICT: PASS

ROUND 8 (delta) — PASS. Confirmed `.gitlab-ci.yml` appears NOWHERE in this branch's diff or
contract, so the abandoned CI branch left no residue. Ruled that reverting the guard is a rollback
of an in-branch tightening, NOT a weakening of a shipped guard, and that it follows an
already-used-twice repo pattern rather than inventing an exemption. Verified `contract.md`,
`escalations.log` and `acceptance_evidence.md` all state plainly that the tightened guard and its
three injected-defect classes are NOT delivered here, and that the abandoned CI episode — including
the CPO approval obtained for a fix that turned out to be wrong — is recorded honestly rather than
sanitised. Its round-7 findings stayed fixed.

ROUND 7 findings, both fixed:

Found two stale passages and correctly judged neither a scope or decision-rights breach. BOTH WERE
FIXED ANYWAY, because they are the same "a deleted module leaves traces that do not carry its name"
class that failed rounds 3-6:

- `contract.md`'s `impact_map` still narrated "ONE new mart, `mart_landing_trending` ... added",
  with `dbt ls` evidence keyed to it. It was the one passage in that document never struck when the
  mart was deleted. Corrected in place; the true net dbt surface (two comment-level edits plus the
  seed changes) is now stated, and the superseded paragraph is struck rather than erased.
- `indexability.mjs`'s `STUB_PAGES` comment said the landing is "a real page with four content
  blocks". It ships two. Corrected, with the reason the number was wrong (it counted the
  composition, not the build).

risks_checked:
- Every changed path in `git status` and the patch compared against `contract.md`'s `scope_paths`,
  including both amendments — no out-of-scope file.
- Trending removal traced end-to-end across `export_site_data.py`, `index.astro`, the home
  components, `.gitignore`, `strings.ts` and `index.spec.json` — no residual code, key, mart
  reference or payload.
- Both contract amendments checked against their stated CPO authority and against the frozen-`site/`
  guard.
- Struck criteria 3 and 4 checked for quiet relaxation — both remove content demonstrated green but
  composed off the page by a later ruling; 3b tightens rather than loosens.
- `decisions_reserved` (copy, GAP-04, legal routes, `INDEXABLE`) — none decided here; `INDEXABLE`
  confirmed still `false` in the diff itself.
- Full patch swept for credential-shaped strings and widened permissions — none.

## football-analytics-expert-reviewer

VERDICT: PASS

Independently resolved the denominator question I had raised: team `shots_on_goal` and player
`shots_on` are the SAME football quantity under two API-Football field names, one per endpoint, and
the catalogue already labels both "shots on target" elsewhere (rows 11, 13, 34). So one shared
`label_en` across the split rows is football-correct, not a fabricated equivalence.

It also confirmed the formula asymmetry is a genuine data-shape difference, not an inconsistency:
team `goals_for` is the authoritative scoreline and carries opponents' own goals (verified to
`int_legs__team_match.sql:41`), so it must strip them; player `goals_total` never carries them.

risks_checked:
- Both `finishing_efficiency` rows traced to source columns in `base_apif__fixture_statistics.sql`
  and `stg_apif__fixture_players.sql`.
- `duels_won_pct`'s two rows after the key split — same formula, same direction, same zero-guard;
  the grain difference (team-of-players vs individual) is coherent.
- Both renames checked against their descriptions and standard football usage.
- All 80 rows' `numerator_expr`, `denominator_expr`, `lower_is_better` and `direction` re-read and
  confirmed unchanged by this round — only `label_i18n_key` moved on two rows.

## bi-analyst-reviewer

VERDICT: PASS (round 7 opened FAIL; both findings fixed and re-verified)

FINDING 1 — `index.spec.json`'s "Fixtures hero" declared i18n key `"vs"`, which no home component
renders. Confirmed independently: the only `t(lang, "vs")` in the tree is
`components/fixture/Masthead.astro:30`, a different page; the "vs" strings in the built home HTML
are fixture SLUGS (`palmeiras-vs-flamengo`), not the label. A residue of the superseded inline
"A vs B" hero layout. FIXED — key removed.

⚠ It also identified a HOLE IN THE MACHINE GATE, which is the more valuable half:
`check-page-specs.mjs` verifies only that a declared `i18n_keys` entry EXISTS in the EN dictionary,
never that the declaring block calls it. So a spec can overstate its page and pass. Not fixed here
(out of scope); needs an issue.

FINDING 2 — `99_gaps_register.md` GAP-02 still read `pending` while `contract.md` and `10_home.md`
§10 both state this PR resolves it, and its two neighbours in the same hunk were updated. FIXED —
marked shipped in #367 with the measurement that decided the shape.

risks_checked:
- Every `trending`/`streak`/`TrendingStory`/`team_slug`/`/teams/` reference traced across
  `site_v2/src/**` — remaining hits are struck historical record or unrelated usages on other pages.
- `landing.json`, both payload shapers and the landing tests checked for a `trending`/`stats` key or
  ranking logic — payload is exactly `{type, upcoming, browse}`.
- Declared `i18n_keys` compared against what each home component actually calls `t()` with —
  finding 1.
- `.gitignore` allowlist, `data/README.md` and `data/teams/*.json` — only `33.json` remains; 0 team
  links in built output.
- `seoHomeDesc`/`seoHomeTitle` in all three locales — new copy claims nothing the page lacks, and
  DE/FI are genuine translations, not byte-identical to EN.
- `rendered_page_evidence.md` read from disk and judged real measured evidence, not a code read.

## platform-reviewer

VERDICT: ESCALATE (round 7 opened FAIL; escalated to the CPO, answered, and filed)

FINDING — the home page hotlinks 24 images per locale, 72 across de/en/fi, directly from
`media.api-sports.io`, with no proxy, self-hosting or fallback. `Crest.astro:23` renders the served
URL verbatim; `astro.config.mjs` has no image integration and `firebase.json` no rewrite. Its role
brief calls this non-negotiable: "Hotlinking someone else's origin is the defect that took the
previous site offline."

Verified independently from `dist/`, not from source: 24 per locale on the home page, 4 on the team
page. NOT introduced by this PR — `TeamHeader.astro` and the fixture `Masthead.astro` already do
it, and an earlier `platform-reviewer` PASS on this same branch never surfaced it. #367 is the first
PR to put it on the home page.

CPO ANSWER: "file the crest issue" (2026-08-09). Do not fix inside #367. `INDEXABLE` stays `false`,
the site is unlisted, and self-hosting or proxying crests is new infrastructure — storage, refresh
cadence, cache headers, licensing — that deserves its own issue rather than a bolt-on to the landing
MR. Filed as **GitLab #36**, a stated blocker on **#377**, with three options and the licence
precondition written up. Recorded in `acceptance_evidence.md` as well as the issue, so criterion 8's
"nothing else broke" cannot be read as "no known defect".

⚠ CAVEAT THE REVIEWER RAISED ABOUT ITSELF, carried forward rather than buried: it had no shell tool,
so it could not run the suites its brief asked it to run. It verified the metric-bindings fix and
the gitignore/tracked-file parity by hand-tracing the actual files, and reviewed the aggregate
counts for internal consistency only. **The execution evidence in `acceptance_evidence.md` is mine,
not independently re-run by that reviewer.**

risks_checked:
- `Crest.astro`, `astro.config.mjs`, `firebase.json` and the committed payloads traced to the
  literal third-party `<img src>` in `dist/` — the finding above.
- The metric-bindings fix hand-traced through `metric_catalogue.csv` rows 14/15,
  `metric_bindings.csv` row 9 and the committed `metric_definitions.json:54`; confirmed the guard is
  genuine and non-vacuous.
- `.gitignore` allowlist against files on disk — 1 team, 13 fixtures, one-for-one, no orphan and
  nothing tracked-but-ignored.
- Every symbol the contract claims was deleted confirmed actually gone, not merely absent from
  deleted tests.
- No hooks, CI, workflow, requirements or lockfile changes anywhere in the patch.
- Credential sweep over the whole patch — only false positives on the SQL unresolved-token guard.

## analytics-engineer-reviewer

VERDICT: ESCALATE (round 7 opened FAIL; ruling ACCEPTED, fix replaced, escalated only because the
compliant fix needed a second scope amendment and an edit under the frozen `site/`)

ROUND 8 (delta) — PASS, and it verified all five points adversarially against the files rather than
against my claims. (1) The reverted guard references no column this branch removed —
`group_display_order` appears repo-wide only in prose, never in a live query, schema or config.
(2) `computation_kind` keeps real coverage: its `not_null` + `accepted_values` schema tests attach
directly to the modified seed node and run UN-DEFERRED against `ci_analytics` in the
`state:modified+` build step; it traced the two-step job to confirm the mechanism rather than
accepting it. (3) The seed/schema.yml pair is coherent and the reverted file has no dangling
references. (4) The round-7 fix still stands unchanged — `(metric_id, entity)` keying, no default,
`SystemExit` on an unmatched pair, `catalogue_entity` carried as data on every bindings row.
(5) THE POINT I ASKED IT TO CHECK HARDEST: no singular test references `label_en` or
`computation_kind` — all three `label_en` tests are schema-level generics on the seed node, so they
run against `ci_analytics` and are NOT exposed to the deferred-to-main resolution defect. So the
single revert is sufficient and no sibling defect is hiding behind it.

ROUND 7 finding:

FINDING — my first fix hardcoded "prefer the team row" in `load_catalogue`, collapsing the
catalogue's `(metric_id, entity)` grain inside consumption-layer code. I had flagged this question
to the reviewer explicitly rather than hoping it would pass, and it ruled against me, citing
`layering.md` §Consumption layer (which forbids entity derivation downstream of the marts and names
`site/` scripts as inside the contract, so "it is legacy" is not an exemption) and
`docs/roles/analytics_engineer.md` (entity alignment is base-layer business logic).

The sentence worth keeping: **byte-identical output does not cure a rule living in the wrong layer —
the mandate for the default IS the violation.** My own docstring had named the compliant fix and
skipped it for scope convenience, which is exactly the pattern that review exists to catch.

CPO ANSWER: "yes to both, add the entity column and file the crest issue" (2026-08-09). Scope
amended a second time to add `site/match-preview/metric_bindings.csv` — under the frozen `site/`,
authorised explicitly. Shipped fix:

- The bindings CSV carries `catalogue_entity` per row, 13 rows, all `team`.
- `load_catalogue` is keyed on `(metric_id, entity)` with NO default and NO preference.
- `build_defs` raises `SystemExit` on an unmatched pair, so a miss fails loudly instead of falling
  back to another entity's row.

Verified four ways: red before the fix, green after; still red when the DATA is wrong (flipping the
binding to `player` reproduces the failure, so the guard is not vacuous under the new design);
an unknown pair raises with the entity named; and `metric_definitions.json` is byte-identical, with
`git status site/` showing the bindings CSV and nothing else.

risks_checked:
- `mart_landing_trending` deletion — yml block gone with no orphaned keys, `grep -r` returns
  nothing, no dangling `ref()`.
- The landing writer confirmed pure select/group/rename; `_HERO_FIXTURE_LIMIT` is display
  truncation, not a business rule; no hardcoded league_code.
- `metric_catalogue.csv`/`schema.yml` coherence after the deletion and after the per-entity key
  split, including the tightened `assert_metric_catalogue_expr_resolvable` partitioning on
  `computation_kind`.
- `load_catalogue` — the finding above.

# ROUND 8 CARRY-FORWARD, stated rather than left implicit. `bi-analyst-reviewer`,
# `football-analytics-expert-reviewer` and `platform-reviewer` were NOT re-run in round 8. The
# delta is one file, `dbt_project/tests/assert_metric_catalogue_expr_resolvable.sql`, reverted to
# main's version, plus task artifacts. It touches no `site_v2/**` or `docs/wireframes/**` path
# (bi-analyst), changes no metric formula, definition or display name (football-analytics — the
# seed CSV is untouched in this delta), and alters no script, hook, CI file or python test
# (platform). Their round-7 verdicts stand on a diff whose only change since is the removal of an
# assertion they did not review. `platform-reviewer`'s round-7 ESCALATE and its CPO answer are
# unaffected; the crest finding is filed as #36 either way.
#
# WHAT ROUND 7 COST, recorded because the pattern is the point.
# Six rounds reviewed a page whose composition was wrong, and passed it. The premise was never in
# the diff, so no reviewer could see it — `[[feedback-verify-by-running]]` again, one level up:
# review checks the diff, not whether the diff is the right diff. Two of round 7's findings
# (the red suite, the hotlinked crests) had been latent through all six earlier rounds.
