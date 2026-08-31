# Review — refactor/metric-rename-player-goalkeeping — 2026-08-31

> **STEP 4 of the metric catalogue naming programme, MR 6 of seven.** The four player
> `goalkeeping` metrics: `saves` → `saves_player`, `save_pct` → `saves_player_pct`,
> `goals_against` → `goals_against_player`, `shots_on_goal_against` →
> `shots_on_goal_against_player`. PLAYER entity only. Branched from main `9ee88a4`.

diff_sha256: 16375de0b6f7047f6328ff39485df26e2102dccb37f48485b12dd1071a51bf17

rounds: 2

⛔⛔ **ROUND 1 FAILED 5–0 ON TWO REAL DEFECTS, BOTH MINE — AND EVERY GATE WAS GREEN WITH BOTH IN THE
TREE.** `dbt parse`, the hygiene gate, the yml-vs-projection check, the resolver, `pytest`,
`npm test` and both site builds all passed. **The blinded round was the only thing between these and
production.** Counts moved 217/459 → **210/466**; `scope_paths` 45 → 43.

⭐⭐ **BOTH DEFECTS WERE ONE HABIT, NOT TWO BUGS: A SCOPE COARSER THAN THE ENTITY IT HAD TO RESOLVE.**

- **The TEAM scoreline pair (6 sites, found independently by 4 reviewers).** `goals_for` /
  `goals_against` is the team per-fixture scoreline from `int_legs__team_match`, reaching
  `mart_team_fixtures`, `mart_head_to_head` and `mart_team_momentum_window` — none renamed. I scoped
  four files as PLAYER wholesale. `export_site_data.py:166`'s `_TEAM_FIXTURE_FIELDS` is a KEEP-list
  applied to `mart_team_fixtures` rows via `row.get(k)`, so it would have emitted
  `goals_against_player: null` for every team fixture **forever, with no crash**, while
  `TeamFixtureRow.astro:23` still read `fx.goals_against`.
- **The seed's `interpretation` column (found by 3).** The protect list was a BLOCKLIST of 5 of the
  seed's 15 columns, so `saves_per90`'s prose became "More **saves_player** per 90 is better…" — an
  internal identifier in reader-facing text, on a row the contract states three times does not change.

⭐ **BOTH FIXES ARE THE CLASS, NOT THE INSTANCE.** The blocklist became an ALLOWLIST
(`SEED_RENAMEABLE_FIELDS = {"metric_id"}`), so a seed column added later is protected by default.
The scoreline fix is a fact about the domain rather than an exemption list — **there is no player
`goals_for`** — and, measured against the round-1 diff, it separates all 6 wrong renames from all 60
correct ones exactly.

⛔ **TWO SECONDARY LESSONS WORTH MORE THAN THE DEFECTS.** (1) **The test was mutated to match the
bug**: the sweep renamed `test_export_site_data.py:367`'s fixture key in lockstep with the code, so
`pytest` could not disagree — "verify the test fails" has a blind spot exactly where an automated
rename touches both sides. (2) **A file that falls to ZERO renames is never reopened** by the
no-op-write guard, so it silently keeps its previous text while every other file is rewritten from
base; `export_site_data.py` and its test had to be restored from base explicitly.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- `export_site_data.py` and `tests/test_export_site_data.py` **absent from the patch entirely** and
  read on disk to confirm `_TEAM_FIXTURE_FIELDS` carries the unrenamed pair — genuinely restored to
  base, not patched back at one line.
- Whole-repo sweep for `goals_for` co-occurring with `goals_against_player`, by line AND by proximity
  within 80 characters in either order: **zero matches.** Every team-side re-point moves only the
  `doc()` pointer, never the column name beside `goals_for`.
- The seed differs from base in `metric_id` only, on all four rows; `saves_per90`'s `interpretation`
  is absent from the diff entirely.
- **Over-protection checked in the other direction**: every legitimate player occurrence still
  renames across all ten models and the macro, read hunk by hunk — no dangling old name, no orphaned
  alias, every `safe_divide` num/den pair moved together.
- The GK chain end to end; all six `accepted_values` lists; the 172→167 block regeneration matching
  the simulation term for term; the four prose rewrites keeping mechanism, guard and fixtures intact.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- **My round-1 finding is fixed**: `export_site_data.py` restored and absent from the diff, and the
  binding traced end to end — `TeamFixtureRow.astro:23` reads `fx.goals_against`, `types.ts` keeps it
  on all five team interfaces (8 occurrences unrenamed), and `mart_team_fixtures` /
  `mart_head_to_head` / `mart_team_momentum_window` remain untouched sources.
- All four wireframe scoreline rows read `goals_for` / `goals_against` again and describe fields the
  team marts actually emit.
- **Over-protection checked**: every legitimate player rename still lands across five wireframes and
  every in-scope player model and yml.
- The GK chain walked in the working tree, including `t(lang, "saves")` correctly left as a UI word
  key in all three locales.
- The ten byte-identical frontend files grepped individually, including both rendered team labels.
- Evidence judged for honesty: both files disclose the 5–0 fail, name both defects, **credit this
  reviewer for the second rendering-binding break rather than claiming self-discovery**, and state
  plainly that the dist comparison could not see it because it builds from the frozen sample.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Re-audited the whole branch rather than a delta, since round 1 had no PASS to build on.
- **My round-1 finding is fixed**: the seed's single hunk touches four lines; on each, all fourteen
  other columns — including `interpretation` — are byte-identical. `saves_per90`'s interpretation
  read from the live file is the exact pre-round-1 wording, and the row is absent from the diff.
- Both TEAM dual-entity rows (`saves_pct`, `goals_against_per_match`) absent from the diff with
  formulas intact — no entity mix-up.
- `saves_player_pct` traced term-for-term from the seed's `sum(saves)` over `sum(saves + goals_against)`
  through the macro and all four consuming models — still shot-stopping percentage.
- `mart_player_profile.sql`'s composed `a.saves_player + a.goals_against_player as
  shots_on_goal_against_player` matches the catalogue formula; direction correct on all four rows.
- **Doc-block prose compared byte-for-byte on every renamed and collapsed block**, including that the
  surviving team `saves` and `goals_against` blocks keep team language with no player wording leaking
  in; the five deleted orphans confirmed at 0 references.
- The scoreline fix checked for over-protection in both directions.

## platform-reviewer
VERDICT: PASS
risks_checked:
- **Both my round-1 findings verified fixed at source**, not from the write-up: the two Python files
  absent from the patch and read on disk; the seed differing in `metric_id` only on all four rows.
- ⭐ **The restore was checked for the failure mode it could introduce**: swept all 34 changed
  non-paperwork files for any carrying stale round-1 content with zero renames — **none**. Every
  touched file is internally coherent, and `goals_for` never appears as a rename target anywhere,
  including inside `mart_player_match_log`'s mixed team/player block in `shared.yml`, where the team
  scoreline stays untouched while that model's own player `saves` column re-points correctly.
- `_LEADERBOARD_METRICS` / `_LB_KEEP` confirmed to carry no goalkeeping-stem token, so the restore
  did not undo something that should have moved.
- The four prose-only files: every changed line is inside a comment or docstring; no executable line,
  fixture or assertion moved.
- **The gate-credibility narrative judged rather than accepted**: the "every gate green with both
  defects" claim is consistent with the defects' nature — a `dict.get` null-emission with no crash,
  and seed prose — and the mutated-in-lockstep test is disclosed honestly as the verify-the-test-fails
  blind spot.
- No `.claude/hooks/`, `.gitlab-ci.yml`, `.github/workflows/` or dependency manifest touched; no
  credentials; `fct_fixture_player_stats` confirmed as the only incremental model, its SQL untouched
  and only its yml doc-pointer moved — no `--full-refresh` implied.

## scope-auditor
VERDICT: PASS
risks_checked:
- `scope_paths` (43) reconciles exactly: 39 diff entries plus the 4 review-paperwork exclusions, no
  orphan either direction.
- **My round-1 finding verified by reading the live files**, not the claim: `_TEAM_FIXTURE_FIELDS`
  and the test fixture both carry `goals_against` again; both correctly dropped from scope.
- **The failure record checked across all four documents** — contract §11, both evidence files and
  the log append — for completeness and honesty. All state 5–0, both defects, "both mine", and that
  every gate was green; both secondary traps are recorded; `rendered_page_evidence.md` explicitly
  credits `bi-analyst-reviewer` rather than self-claiming. **Nothing softened or reattributed.**
- The two fixes judged as decisions: the allowlist and the domain-fact discriminator are both class
  fixes, and neither quietly widens what this MR may do; the classifier remains unshipped.
- Authority unchanged — four names verbatim, no new CPO ruling, §5/§6 still correctly FORM.
- `escalations.log` a single-hunk pure append (`@@ -6955,3 +6955,124 @@`).
- Credential sweep: every "token" hit is the programme's own term of art.

## escalations
(none)
