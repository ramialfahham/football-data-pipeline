# Acceptance evidence — step 4, MR 3: the five player `defending` metrics

Branch `refactor/metric-rename-player-defending`, from main `a3fb952`.

    tackles_total          →  tackles_player
    tackles_interceptions  →  interceptions_player
    tackles_blocks         →  blocks_player
    defensive_actions      →  defensive_actions_player      (+ its 4 derived yoy forms)
    dribbles_past          →  dribbles_past_player          (PLAYER entity only)

⚠⚠ **THIS IS ROUND 3. ROUNDS 1 AND 2 BOTH FAILED 4–1, on different things, and round 3 is the cap.**

**Round 2's finding, and it is the more serious of the two.** `scope-auditor` FAILed
`impact_map.downstream` for describing the `dbt ls` lineage command without pasting its output. The
honest correction is larger than the finding: the field claimed the command was *"run on this branch
BEFORE the first edit"* — **it had not been run for this MR at all.** The sentence was carried over
from `!127`'s contract, where it was true. I asserted a step I skipped. The real output is now
pasted, and it is **13 models, not the 10** the previous batch held — so running it was not a
formality.
⭐ **The two round failures share one cause: carrying something forward without re-deriving it** — a
guard that worked by luck in `!125`, and a claim that was true in `!127`. What a template carries
safely is structure; every sentence in it that asserts a fact about *this* branch has to be
re-earned. After the finding I audited the rest of the contract for the same defect:
`deploy_order`'s "no touched model is incremental" was re-derived rather than re-asserted — all ten
changed `.sql` models are `table` or `view`. That one held.

⚠⚠ **ROUND 1 FAILED 4–1.** `bi-analyst-reviewer` found a real defect —
`03_player_profile.md:127-128` renamed two field names in prose documenting `mart_player_match_log`,
a provider surface that does not rename, so the wireframe named two fields existing nowhere in the
export. Cause, fix and the corrected numbers are in the section below; the other four reviewers
PASSed and their findings are unaffected by the fix, which touched one markdown paragraph.

Every gate below was run **unpiped, with its exit code read bare**. ⚠ One exception is recorded
rather than hidden: the mutation-2 run was first piped through `tail -5` and reported
`HYGIENE_EXIT=0` — which was **`tail`'s** exit code, not the gate's. Caught immediately and re-run
bare, where it reads **1**. That is the trap the record already names, committed live, and it is
here because the near-miss is more useful than a clean-looking log.

⚠ **AND ONE GATE IN `done_when` IS NOT EVIDENCE FOR THIS CHANGE**, raised by `platform-reviewer`.
`check_ui_i18n_metrics.py` validates only `site/**`, the retired frozen tree this branch never
touches, so its exit 0 passes identically whether or not the rename happened. It is still run
because it is a real CI gate, but it is **not** discriminating here and is no longer counted as
evidence. The discriminating check for the UI risk is the structural `dist` comparison.

criteria_demonstrated:
  - ⭐ **Criterion 1 — and for the first time in step 4 this is a REAL check, not a confirmed prediction.** `defensive_actions_per_match` is one of the 12 rendered metric rows AND a PROTECTED token of this batch, so a mis-scope would delete a rendered label. The site was built TWICE — base content (stashed by explicit path) and branch — and measured structurally from the markup, never by substring: **12 rows and 7 group headings per comparison block in EN, DE and FI across 19 fixture pages**, distinct-label sets equal element-for-element, **REMOVED none / ADDED none** in every locale. The row itself is present in all three: "Ø Defensive actions" / "Ø Defensivaktionen" / "Ø Puolustustoimet", on 19 built pages.
  - **Criterion 2 — old names gone from every surface that moved, nothing half-renamed, and the frontend untouched.** `git diff --name-only -- site_v2/` is **empty**: not one frontend file changed, including the five that were swept. New names present in **26** files (`tackles_player`), **25** (`interceptions_player`, `blocks_player`), **18** (`dribbles_past_player`), **12** (`defensive_actions_player`), **4** each for the derived yoy forms. All **72** yml column entries naming an old or new name were reconciled against their own model's SQL; 71 resolve literally and 1 is reported as not literally checkable rather than skipped. The **24** surviving old names sit in exactly five partially-moving files in the counts the classifier printed — four models (8 / 6 / 4 / 4), every one an upstream READ of a provider relation, plus **2 in `03_player_profile.md`'s match-log paragraph**.
  - **Criterion 3 — two guards passed AND each watched going RED.** `sync_metric_docs_blocks.py --check` (exit 0, 173 blocks) broken by mutating the seed's `tackles_player` `metric_id` → **RED, exit 1**. `check_description_hygiene.py` (exit 0, 1604) broken by pointing `mart_leaderboards.defensive_actions_player` at a non-existent block → **RED, exit 1**. Both reverted, both green, file count unchanged at 28.
  - ⭐ **Criterion 4 — every dotted AND bare reference resolves, and the resolver was repaired and re-proved before it was trusted.** 48 references checked, **0 broken**, 5 reported unresolved. See below — this is the batch's most substantial finding.

## ⛔⛔ The resolver had a FALSE-POSITIVE class, found on the UNMODIFIED tree

Run against `main` before a single edit, `check_column_refs.py` reported a BROKEN reference:

    int_player_profile__yoy.sql:82  bare read of 'defensive_actions' inside CTE 'cur'
    whose source is int_player_season_record, which does not emit it

**It was wrong.** The column is *born in the chain*: `std` creates it at line 50 as
`tackles_total + tackles_interceptions + tackles_blocks as defensive_actions`, and `cur` reads it
two CTEs downstream. Chasing the chain to the underlying `ref()` and asking whether IT emits the
column gives the wrong answer for any column a CTE computes. No earlier batch exercised this,
because none had a metric COMPUTED inside a CTE from renamed inputs.

⭐ Fixed: a name created by an `as <name>` alias in the same model is exempted — and exempted **into
the "unresolved, reported" list, never silently**, so what the tool did not check stays visible.

⭐ **Then proved the fix had not blunted it**, which is the half that matters. Reproducing the `!125`
round-2 defect — reverting `int_player_season__metrics.sql:45` to `sum(shots_total) as shots_player`
— still turns it **RED, exit 1**, with the exact diagnosis: *"bare read of 'shots_total' inside CTE
'aggregated' whose source is int_player_club_season__metrics, which does not emit it."* Restored,
green.

⭐ **THE RULE THIS LEAVES: a check that cries wolf gets ignored, which makes it the same defect as
one that gives false confidence.** The record already carries the second half. This is the first
instance of the first half, and it argues for *hardening* the resolver before adopting it as a CI
gate, not against adopting it — a false positive on a correct `main` would have turned the pipeline
red for nothing.

## ⛔⛔ The round-1 defect: a line-scoped guard on a list that wraps

`docs/wireframes/03_player_profile.md` documents **two surfaces**, and round 1 got one of them
wrong:

| lines | surface | source | round 1 | round 2 |
|---|---|---|---|---|
| 96-106 | season-stats bundle + unbundled atomics | `mart_player_profile` / `mart_player_season_record` — **rename** | 4 moved ✓ | 4 moved ✓ |
| 126-129 | MATCH LOG expanded-row list | `mart_player_match_log` — **provider, does not rename** | 2 moved ✗ | **2 protected** ✓ |

**The cause.** The provider-prose guard keys on line content — the mark *"may show the full
per-match line"* — but tested it against **the token's own line**. In `!125` the affected token
(`shots_total`) happened to sit on the same line as the mark, so it worked *by luck*. Here the list
wraps: mark on 126, tokens on 127-128. Every sibling in that list is a provider name —
`shots_total`, `shots_on`, `passes_accuracy_percent`, `fouls_drawn`, `is_starter` — which is what
makes the surface unambiguous once you look at the whole paragraph instead of one line.

⭐ **THE CLASS: a line-scoped test on a construct that spans lines.** The repo already records this
for grep ("a line-based grep misses a phrase straddling a line break"). This is the same defect in
prose. The mark now governs its whole **paragraph**, up to the first blank line.

**The fix was applied by re-running the classifier**, not by hand-editing the file, so what ships is
the classifier's own output. Totals moved **247/120 → 245/122**: exactly those two tokens changed
column, nothing else. Verified per-file — `03_player_profile.md` went from `renamed 6 / protected 0`
to `renamed 4 / protected 2`, every other file identical.

⚠ The verification suite had to change with it, and the shape of that change matters:
`03_player_profile.md` is pinned by an **exact count of 2 protected**, not added to a whitelist. A
whole-file exemption would let a future half-rename through silently — the second time in this
programme that a whole-file question proved wrong for a file that only PARTLY moves.

## The classification — 367 tokens, 245 renamed / 122 protected

1,464 tokens repo-wide: **1,062** untouched (the sample — `teams/33.json` alone holds 121 —
`.claude/**`, `site/**`, the regenerated `metric_columns.md`), **35** in provider `.sql` excluded by
the "yes" ruling, **367** in sweep across 42 files. 26 files were written; **16 were swept, decided
and left untouched**, which is deliberate: a printed decision for each beats silence.

⭐ **FOUR self-aliasing `sum(X) … as X` sites, and only ONE moves its inner read.** MR 2 had three;
this batch adds `int_player_season_position__metrics`, newly in the sweep:

    int_player_club_season__metrics.sql:108      sum(coalesce(tackles_total, 0)) as tackles_player
    int_player_season_position__metrics.sql:108  sum(coalesce(tackles_total, 0)) as tackles_player
    int_player_season_record.sql                 sum(tackles_total) over w as tackles_player
    int_player_season__metrics.sql:50            sum(tackles_player) as tackles_player   ← MOVES

⭐ **And the batch's own new shape, in `int_player_profile__yoy.sql`:** a metric COMPOSED across a
model boundary. Line 50 reads three columns from `int_player_season_record` (which renames them) and
writes a fourth:

    - tackles_total + tackles_interceptions + tackles_blocks as defensive_actions
    + tackles_player + interceptions_player + blocks_player as defensive_actions_player

## ⛔ The team/player junction, which is what makes this batch different

RULING 5's own reasoning named `int_legs__team_from_players` as where seven TEAM metrics are
aggregated FROM player data. Four of these five are on that list, and the model reads:

    sum(tackles_total) as tackles · sum(tackles_blocks) as blocks · sum(tackles_interceptions) as interceptions

Player names in, TEAM names out. It is excluded outright as provider `.sql`, and that exclusion is
**load-bearing**: its reads point at `int_legs__player_match`, which does not rename, so renaming
them would produce a model that cannot execute. Verified explicitly — untouched by the branch, still
reading the provider names, no new name leaked into it.

⭐ The team seed formulas are safe by construction: `defensive_actions_per_match` reads
`sum(tackles + interceptions + blocks)` from that model, whose columns are `tackles` /
`interceptions` / `blocks` — **different tokens**, unreachable by any stem.

## Gates, each unpiped with its exit code read bare

  - `sync_metric_docs_blocks.py --check` → **0**. 173 blocks before and after.
  - `check_description_hygiene.py` → **0**. **1604 descriptions**, 235 blocks resolved — *identical to base*. That number is the "re-point them" ruling measured: 59 of 72 doc references move, 13 do not because their blocks are not renamed.
  - `check_layer_contract.py` → **0**; `check_ui_i18n_metrics.py` → **0**.
  - `dbt parse` → **0**.
  - `sqlfluff lint` on the 10 changed models → **1**, and **proved pre-existing**: the same files stashed by explicit path, re-linted at base content, output **BYTE-IDENTICAL**, **zero LT05** both sides. All findings are the known `dbt_utils` TMP/PRS noise and its ST11 cascade.
  - `python -m pytest -q` → **0**: **1009 passed, 1 skipped, 14 subtests** — the baseline. Verified it carries: neither `!127` nor this branch changes any file under `tests/`.
  - `npm test` → **0**: 76/76. `npm run build` → **0** on both base and branch: 66 pages, `audit-seo` OK.

## #96 — SEVEN reproductions, and three of the six lists are in play

| list | names | this batch |
|---|---|---|
| `int_competition_benchmarks.yml:27` / `:66`, `shared.yml:2080` | 22 team | unchanged — and they hold `defensive_actions_per_match`, `tackles_per_match`, `interceptions_per_match`, `blocks_per_match`, all PROTECTED |
| ⭐ `int_competition_benchmarks.yml:105`, `shared.yml:2186` | 18 player | unchanged — both hold **`defensive_actions_per90`, which must NOT move**. Checked as PROTECTIONS, which is new this batch |
| ⭐ `shared.yml:1756` | 14 board keys | **`defensive_actions` → `defensive_actions_player`** |

The board key was then pinned mechanically, not by eye alone: the set `mart_leaderboards.sql`
emits, the `accepted_values` list, and the export's `_LEADERBOARD_METRICS` all carry
`defensive_actions_player`, none carries bare `defensive_actions`, and emitted == accepted exactly.

## Two defects of my own, both caught before review

  - **I reintroduced the lying-decision-list defect while trying to fix it.** MR 2 labelled every non-self-aliasing bare read "this model's own column" — false at `int_player_profile__yoy.sql:50`. My improvement swallowed the `alias` case, so the four aliases in `int_player_season_record.sql` came out labelled *"bare read of int_legs__player_match, which renames it"* — false twice over: a WRITE, and that relation does not rename. Decisions were identical before and after the fix (247/120), so it was label-only; but **a decision list a reviewer checks INSTEAD of the diff must not lie**, and I had just re-broken exactly that. Fixed by handling `alias` explicitly and naming the renaming relations.
  - **The verification suite cried wolf twice**, and both were the check's fault, not the work's. Protected-token counts read the whole repo and failed on +6 / +7 that were entirely inside `contract.md`, which *discusses* those tokens by name — now counted over the code tree only. And the yml-column check called `int_team_season__metrics.defensive_actions_per_match` a defect when that model projects `sf.* except (match_number)`; the column arrives from the cumulative model and never appears literally. Pre-existing on main, untouched here, now reported as not-literally-checkable rather than failed.
