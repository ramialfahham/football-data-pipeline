# Review — feat/team-slug-no-provider-id — 2026-07-28

> Machine-checked review artifact (governance G3). Written in step 4 (Lock), after staging and after
> the blinded reviewers returned. **Three rounds, at the cap.** The history matters, so it is here
> rather than lost:
>
> **Round 1 — analytics-engineer-reviewer FAIL, and it was a real bug.** The level-3 terminal
> (`{candidate}-{id}`) was unique among id-suffixed rows because the id is, but was never
> anti-joined against the slugs already assigned at levels 1 and 2. Reachable, because club names
> embed digits: `1899 Hoffenheim` owns `hoffenheim-1899`. The model's own header and `base.yml`
> claimed unconditional closure and were wrong. Its second finding was also mine: I asserted both
> that level 2 fires on zero real rows AND that the Ararat case was "live" and "BigQuery-verified".
> Measured — `3682 Ararat` and `3683 Ararat-Armenia` both sit at level 1, so the anti-join has never
> fired. The data pattern is live; the mechanism is latent.
>
> **Round 2 — closed the gap, and introduced a hack.** An `assigned_before_level_3` anti-join, plus a
> level-4 terminal inserting a DOUBLED hyphen, justified because `kebab_slug` collapses runs so `--`
> is unreachable. Provably unique. Both reviewers passed it.
>
> **Round 3 — the CPO rejected the output on sight** (*"A double hyphen? Seriously? Looks
> extraordinary hacky."*) and he was right. Level 4 is deleted. The anti-join stays. The residual is
> now STATED: if a level-3 candidate is itself taken, `team_slug` is NULL and `not_null` stops the
> build naming the team. Removing the branch changed NO output — 3,250 distinct slugs before and
> after, zero double hyphens either way. It was machinery for a case that has never occurred.
>
> **The reason it was wrong is not only aesthetic.** Two of the three triggers that push a team to
> level 3 are DATA DEFECTS, not naming problems: a same-country duplicate record (#850's open alias
> decision — the entire reason the Nyasa pair is there) and a null country (#853: 39 teams, 22 of
> which have a country sitting in `stg_apif__teams`). An automatic escape hatch below level 3 made
> that absorption invisible. Both docs now name the owners.

diff_sha256: 9bb99a180a66bf04dcb8dddabb7dbcf800a0daf279daab8595f22733f02f8d3d

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- **Removing level 4 is guard STRENGTHENING, not loosening** — the standing rule here is "never
  loosen a guard", so this was audited directly. The level-4 branch was not a guard; it was an
  automatic workaround that ensured `not_null` could never fail, neutering it. Deleting it gives the
  guard teeth: a level-3 collision now stops the build and names the team instead of silently
  emitting a URL no reader should see.
- **Data-defect ownership is now named rather than absorbed** — the docs cite #850 (alias decision
  for duplicate records) and #853 (39 null countries) as the owners of the two common level-3
  triggers, which is what stops a future reader reinventing level 4 as a "fix".
- Rounds 1-2 risks, unaffected by this delta: scope held with one legitimate amendment
  (`site_v2/src/data/teams/33.json`, named in the approved plan, omitted from `scope_paths` by
  mistake) and one deliberately REFUSED amendment (`dbt_project/.sqlfluff`, recorded as refused);
  every `decisions_reserved` item still reserved (persistence, player/coach slugs, the dead
  `team_name_key` macro, the two phantom records); the `site_architecture.md` §3 rewrite is a
  correction that relocates the "never change once published" promise to an explicit target state
  rather than deleting it; the FALSE `mode=alias` claim the previous PR left in `seeds/schema.yml` is
  corrected with a dated CORRECTION note explaining why it was wrong.
- ⚠️ HONEST CAVEAT ON THIS ROUND'S VERDICT: scope-auditor used **zero tool calls** in round 3 and
  wrote "CORRECT IF PRESENT" about the doc changes, so its round-3 verdict rests on my description
  rather than on reading the files. I verified the claims myself by grep: the hack-was-removed note
  is at `base_apif__teams_global.sql:215-218` and `base.yml:49-52`, the DATA DEFECTS note at
  `base_apif__teams_global.sql:205` and `base.yml:53-55`, the STATED RESIDUAL at `base.yml:45`, and
  the `not_null`-as-escalation-path wording at `core.yml:186`. Recorded rather than glossed.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- **The NULL path is correctly modelled and correctly caught**, verified by reading the current file
  rather than the summary: the final `case` has no `else`, which in BigQuery yields NULL, and
  `core.yml` carries both `not_null` and `unique` on `team_slug`. The reviewer then found an edge I
  had not stated — if the branch fired for TWO OR MORE teams, `unique`'s `group by` treats NULLs as
  one group and would ALSO fail. The two tests reinforce each other; there is no gap between them.
- **Round 1's actual gap stays closed** — `assigned_before_level_3` is unmodified, and its two
  `where` clauses were re-checked against the final case's level-1 and level-2 winning conditions and
  still match exactly. Removing level 4 only changes the disposition of the (verified zero) rows that
  would have collided AT level 3; every non-NULL slug remains provably collision-free.
- **The docs no longer overclaim** — `base.yml` says "STATED RESIDUAL, not closed", which is strictly
  more honest than round 2's "closure is unconditional" and matches what is actually true.
- **It agreed with the removal on substance, not taste**, and grounded that in this repo's own
  standards: the site is pre-launch (`noindex`, no public site), so failing loud costs nothing today;
  reaching the branch requires an underlying data defect FIRST, which is exactly the
  ambiguous-identity situation the codebase says should get a human and an override row rather than a
  silent rule; and it is not new blast radius, because `unique` already carried "any collision halts
  the nightly" exposure — `not_null` now shares it for a strictly narrower, zero-occurrence case, and
  names the offending team instead of requiring someone to diff URLs.
- Rounds 1-2, unaffected: no `team_slug` leakage into unrelated marts (all 21 `ref('dim_team')`
  consumers checked; the two that `select *` enumerate their projection); layer placement legitimate
  against the actual text of `layering.md`; the level-4 `--` proof was independently re-derived from
  the regex before being removed; export purity correct with `team_slug` in the identity-drop set.

## cto-reviewer
VERDICT: PASS
> Round 2 verdict, carried forward: round 3 touched only `base_apif__teams_global.sql`, `base.yml` and
> `core.yml` — all `dbt_project/**`, none of them a cto-routed surface.
risks_checked:
- **The `.sqlfluff` change cannot affect CI** — `ci-data-build.yml` lints with
  `working-directory: dbt_project` and no `--templater` override, so it resolves the untouched nested
  config (`templater = dbt`) and never invokes the jinja templater; `ci-validate.yml` does not run
  sqlfluff at all; no hook reads `.sqlfluff`. The new section is inert unless `--templater jinja` is
  passed explicitly.
- **A non-blocking fragility, recorded rather than dropped:** the old `slugify()` could never return
  empty, so the payload's `slug` was never `None`. `latest.get("team_slug")` can be, and
  `slug_map[None]` would silently become the JSON key `"null"` and collide across teams. Judged
  acceptable: every other identity field in that payload relies on `.get()` the same way, and
  `team_slug` has MORE protection than most (`not_null` and `unique`). Note this interacts with round
  3 — the NULL case is now reachable in principle, and `not_null` is what stops it reaching the
  export at all.
- Rename hygiene: the repo was grepped for `slugify`; only the updated test file and an accurate
  mention in `active_work.md` remain. The rename prevents a future caller reusing it for a team and
  reintroducing the id the CPO ruled out.
- The pinning test is honest — `_kebab`'s NFKD-then-ascii-ignore path was traced by hand for both
  literals, so `sigursson-1` and `preuen-2` are real current behaviour, not guessed.

## bi-analyst-reviewer
VERDICT: PASS
> Round 2 verdict, carried forward: round 3 touched no `site_v2/**` file.
risks_checked:
- **The binding rule, traced end to end** rather than taken from prose: base derives `team_slug` →
  `dim_team` publishes it → `mart_team_profile` selects it → the export reads it. The value the
  committed sample asserts is one the warehouse genuinely produces, which is the fabrication class
  this reviewer hunts for. It also confirmed `slugify` no longer exists, so no live path could put
  the id back on a team slug.
- **Rendered-page evidence (#827) correctly does not apply**, established by grepping `\.slug\b`
  across all of `site_v2/src`: the only consumers are `getStaticPaths` in two page files — route
  generation, never template interpolation. No component reads `.slug`. This changes which path a
  page is generated at, not anything a reader sees.
- Sample self-consistency: `33.json` contains the slug exactly once with no stale `-33` elsewhere,
  and the only other committed sample never embeds a team slug.
- The team/player slug shape divergence is disclosed in the `site_architecture.md` diff with its
  reason and marked out of scope in `decisions_reserved`.

## escalations
(none)
