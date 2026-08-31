# Acceptance evidence — step 4, MR 4: the five player `passing` metrics

Branch `refactor/metric-rename-player-passing`, from main `1cf0d40`.

    passes_total       →  passes_player
    passes_accurate    →  passes_accurate_player
    passes_key         →  passes_key_player        (+ its 4 derived yoy forms, CPO-ruled)
    pass_accuracy_pct  →  passes_accuracy_player_pct
    key_passes_per90   →  passes_key_per90         (PLAYER entity only)

**The largest and most exposed batch of step 4**: 426 tokens across 48 files, three surfaces no
previous batch had, and the first frontend source change of the whole step.

⚠⚠ **THIS IS ROUND 3, THE CAP. ROUNDS 1 AND 2 BOTH FAILED, ON FOUR SITES OF ONE DEFECT CLASS.**

  - **Round 1, 4–1** (`analytics-engineer-reviewer`): three models shipped
    `round(passes_player * passes_accuracy_percent / 100)` — a nested aggregate over a SIBLING
    ALIAS, against CTEs carrying only `passes_total`.
  - **Round 2, 3–2** (`analytics-engineer-reviewer` and `bi-analyst-reviewer`, independently): a
    FOURTH site, `mart_player_season_record.sql:168-170,187`, where the `matched` CTE was updated
    but the model's own FINAL SELECT still projected the old names — and its own yml already
    declared the new ones.

Counts moved 275/151 → 267/159 → **272/154**. All four sites could not have compiled.
⭐ **Before spending the last round I built a check that cannot fail the way my other four did** —
see "An independent check" below. It found exactly the one site the reviewers had found, and no
fifth; that is what made round 3 worth spending rather than a guess.

Every gate below was run **unpiped, with its exit code read bare**.
⚠ `check_ui_i18n_metrics.py` is run because it is a real CI gate but is **NOT evidence** here — it
validates only the frozen `site/**` tree this branch never touches, so it passes identically whether
or not the rename happened (`platform-reviewer`, `!128`).

criteria_demonstrated:
  - **Criterion 1 — no rendered name changed its words.** The site was built TWICE (base content stashed by explicit path, then branch) and measured structurally from the markup, never by substring: **12 rows and 7 group headings per comparison block in EN, DE and FI across 19 fixture pages**, distinct-label sets equal element-for-element, **REMOVED none / ADDED none**. ⚠ **For this batch that CONFIRMS A PREDICTION rather than discriminating** — see the correction below. The discriminating guard for the protected team row is `npm test`'s label binding.
  - ⭐ **Criterion 2 — `site_v2/src/lib/types.ts` is the ONLY frontend file that changes**, and it changes exactly one token (`passes_key` → `passes_key_player` on the `TopPlayer` interface). The other four swept frontend files are byte-identical and still carry `passes_key_per_match`. All **82** yml column entries naming an old, new, derived or protected name were reconciled against their own model's SQL — 79 resolve literally, 3 reported as not literally checkable (wildcard projections) rather than skipped. Every surviving old name is an upstream READ of a provider relation or a TEAM column.
  - **Criterion 3 — two guards passed AND each watched going RED.** `sync_metric_docs_blocks.py --check` (exit 0, 175 blocks) broken by mutating the seed's `passes_key_player` `metric_id` → **RED, exit 1**, and usefully it named all five dependent blocks. `check_description_hygiene.py` (exit 0, 1604) broken by dangling the re-pointed `doc('passes_key_player')` on the two provider marts → **RED, exit 1**, two findings. Both reverted, both green, file count unchanged at 33.
  - ⭐ **Criterion 4 — every dotted AND bare reference resolves.** 54 references checked, **0 broken**, 6 reported unresolved. Watched going RED on a reproduction of the `!125` round-2 defect: reverting `int_player_season__metrics.sql:47` to `sum(passes_total) as passes_player` gives *"bare read of 'passes_total' inside CTE 'aggregated' whose source is int_player_club_season__metrics, which does not emit it"*, exit 1. Restored, green.

## ⛔⛔ The round-1 defect: the alias heuristic, one more time

Three models shipped code that could not compile:

    int_player_club_season__metrics.sql:125 · int_player_season_position__metrics.sql:106
    int_player_season_record.sql:54
        sum(round(passes_player * passes_accuracy_percent / 100)) as passes_accurate_player
                     ^^^^^^^^^^^^^ a sibling alias; the CTE only carries passes_total

**The cause is the mistake this programme logged once already.** The classifier decided "is this an
upstream read?" by asking whether the LINE ends with `as <the same token>`. That recognises
`sum(passes_total) as passes_player` and misses `sum(round(passes_total * …)) as
passes_accurate_player` — which is just as much an upstream read, because the metric is *computed
from* the provider column. `!125`'s round-2 lesson was, verbatim, that for bare reads I asked "does
the alias match the inner name" instead of "did the source relation rename this column".

⭐ **The fix deletes the heuristic rather than patching it.** Every bare read now resolves its
scope's SOURCE: a source CTE that WRITES the token will emit the new name (aliases always move) →
RENAME; a chain reaching a provider relation → PROTECT; a chain reaching a renaming relation →
RENAME; **anything else ABORTS.** That abort fired twice on the first run — a jinja macro with no
query scope, and tokens inside `{# #}` comments — and both were real gaps in my model of the files,
now handled explicitly. ⚠ One inversion had to be corrected inside the new rule too: a source CTE
that aliases the token still shows the OLD name in the base text, but that alias moves, so the read
moves with it — reading the base and concluding "protect" is the same pre-vs-post error `!125` made
in the yml-column guard, and it inverted 17 decisions before it was caught.

## ⛔⛔ The resolver could not have caught it — three blind spots, found by experiment

I told the CPO the `!128` exemption had created a false negative here. **That was wrong, and the
truth is worse:** reintroducing the defect and running the resolver gave **exit 0**. Three separate
gaps, none of which two batches of green results had revealed:

| gap | consequence |
|---|---|
| `check_bare` walked only CTE bodies | a read in a model's FINAL SELECT was never scanned — exactly where `int_player_season_record.sql:54` lives |
| `window w as (…)` parsed as a CTE | pushed the synthesised final-select scope past the end of the file, so adding that scope still scanned nothing |
| a CTE joining two relations resolved to one | reported `int_team_season_record.sql:141` broken — **a false positive on a file this branch never touches** |

All three are closed, and each was verified by watching the real defect go RED (exit 1, exact line
and diagnosis) and the untouched file go GREEN. The `!128` `created` exemption was additionally made
**scope-aware**: a name aliased in the SAME select as the read is not exempt, because SQL cannot see
a sibling alias.

⭐⭐ **THE RULE: a fix that removes a false positive can install a false negative, and only
re-proving the ORIGINAL defect still goes red will tell you.** Twice in two batches now — which is
the strongest evidence yet that the resolver must be hardened before it is ever considered as a
committed CI gate.

## ⛔⛔ The round-2 defect: a fourth site, and a third root under the same rule

`mart_player_season_record.sql`. The `matched` CTE was correctly updated to read
`sf.passes_key_player` / `sf.passes_accurate_player` / `sf.passes_player`, but the model's own FINAL
SELECT still projected `passes_key` / `passes_accurate` / `passes_total`, which no longer exist in
that chain — and `shared.yml` already declared the new names for the same model.

**The cause:** `matched` is `from sides as s inner join season_final as sf`, and the renamed columns
come from the JOINED side. My scope resolution followed only `FROM`, chased `sides`, and answered
from the wrong branch. **Neither the classifier nor the resolver follows joins**, which is why both
reported the tree clean — twice.

⭐ Fixed by resolving across the WHOLE source set — every `ref()`, every `from` and every `join`,
walked transitively; RENAME if any terminal is a renaming relation, PROTECT only if every terminal
is a provider relation, **ABORT otherwise**. Two further aborts fired immediately and were real gaps
rather than noise: window clauses (`w as (…)`) parsing as CTEs had been hiding the final select of
`int_player_season_record.sql` from resolution entirely. The fix is the classifier's own output, not
a hand-edit — verified by re-running it from base and re-reading all four sites.

## ⭐⭐ An independent check, because four failures all came from one kind of logic

Every miss across both rounds came from my own source resolution. So before spending the last round
I built a check that cannot fail the same way: **for every model, do the columns its yml declares
actually appear in its FINAL SELECT projection?** That is exactly the mismatch `bi-analyst-reviewer`
used to find the round-2 site, and it is independent of CTE chains, joins and aliases.

⚠ It also exposes why the existing yml guard was too weak: that one asked whether the new name
appears ANYWHERE in the file, and `passes_key_player` did — inside a CTE. The new check looks only
at the final projection.

  - **Run 1, against the still-broken round-2 state** (to validate the check against a known defect): 10 models, **exactly one mismatch** — `mart_player_season_record`, the site the reviewers had found, **and no fifth**. That result is what justified spending round 3 rather than guessing.
  - **Run 2, against the submitted state**, after the classifier fix was applied: 10 models, **zero mismatches**.
  ⚠ Dated explicitly because an undated "one mismatch" is ambiguous about which state it describes — raised by `platform-reviewer` at round 3, who resolved it independently by reading the delivered SQL.
  - ⭐ **The already-merged `!125` / `!127` / `!128` names, run as an audit of shipped work: 9 models, zero mismatches.** The three merged batches are sound.

## ⛔⛔ Three claims of mine that measurement disproved, all caught before review

`!128` lost two review rounds to claims carried forward from a previous branch. This batch was
audited for that specifically, and three of my own predictions still missed. Each is recorded as a
miss, not quietly restated.

**1. "`passes_key_per_match` is one of the 12 rendered rows, so criterion 1 is a real check."**
Both halves wrong. `metricRows.ts` declares **16** rows, **12** render, and the twelve EN labels are
`% Duels won · % Save percentage · Clean sheets · Ø Corners · Ø Corners against · Ø Defensive
actions… · Ø Duels · Ø Goals · Ø Goals against · Ø Passes · Ø Shots · Ø Shots on target`.
**"Ø Key passes" appears on ZERO built pages.** I carried the framing from `!128`, where
`defensive_actions_per_match` genuinely renders. ⭐ What *does* discriminate here, verified:
`check-metric-labels.test.mjs` extracts every `labelKey` from `metricRows.ts` and asserts in both
directions and all three locales that each is defined in `strings.ts` and that no defined label goes
unasked — so renaming one side without the other turns `npm test` red. `!125` measured that this
guard covers only TEAM `metrics.*` keys, which is exactly why it is load-bearing where the thing at
risk is a team row.

**2. "The block count will fall to 171 (two orphans disappear)."** It rose to **175**. The delta is
−2 +4: the two predicted orphans (`passes_total_sum_season__player`,
`passes_accurate_sum_season__player`) do stop being emitted, but four NEW blocks appear —
`passes_key_player_this_season__player` and its three siblings. They exist because the CPO-ruled
rename moves those columns from `key_passes_*` (which decomposes onto `key_passes`, **not** a player
metric_id, so no block) to `passes_key_player_*` (which decomposes onto a real player metric). I had
reasoned about the half of the mechanism I had seen before and not about the half this batch
introduced.

**3. "That's a documentation improvement — four columns can now carry a description."** Also wrong,
and I checked it only because claim 2 had just failed. **All four new blocks are ORPHANS**: `git
grep "doc('passes_key_player_this_season__player')"` and its siblings return **zero** references,
exactly like the two that disappeared (also zero at base). Nothing gained a description. The honest
statement is *two orphan blocks are replaced by four*. Wiring descriptions onto those columns would
be scope creep on a rename and blank descriptions are already tracked as **#82** — flagged, not
folded in.

⭐ **THE PATTERN ACROSS ALL THREE: a number I predicted from a previous batch's mechanism is a
claim, not evidence. When it misses, the miss is the finding.**

## The classification — 426 tokens, 272 renamed / 154 protected

1,655 tokens repo-wide: **1,197** untouched (the sample, `.claude/**`, `site/**` — which holds
`pass_accuracy_recent`, the retired MVP's live_id — and the regenerated `metric_columns.md`), **32**
in provider `.sql`, **426** in sweep across 48 files. 31 files were written; **17 were swept,
decided and left untouched.**

⭐ **Bare `key_passes` is swept but never moves** — 14 printed PROTECT decisions instead of 14
invisible exclusions. Step 3's batch D justified it structurally and left the rule that comes with
it: *on a rename whose stem is shared, print the classification, not just the diff — a reviewer can
check a decision list, they cannot check an exclusion you kept in your head.*

⭐ **THE FIFTH SURFACE, and the record said to expect one: the seed's `description` field.** `!127`
found `label_i18n_key` as the fourth. Three descriptions gloss their own formula in prose and name
the PROVIDER column — `passes_accurate` ("Derived as SUM(passes_total × …)"), `pass_accuracy_pct`
("Null when passes_total is zero") and the TEAM `passes_accuracy_pct` (same sentence). ⛔ Not
cosmetic: `+persist_docs` publishes these to BigQuery, so renaming them would ship a published
description naming a column that exists nowhere. ⚠ The limit is stated: the field is protected
wholesale, a description naming its own metric_id would need the opposite treatment, none does, and
all three occurrences are printed for individual review.

**Four self-aliasing `sum(X) … as X` sites, one moves its inner read** — unchanged from `!128`.

## ⛔ The team/player junction, and this time a stem reaches it directly

`int_legs__team_from_players.sql:28` reads `sum(passes_key) as key_passes` — player name in, TEAM
name out. RULING 5 named key passes among the seven team metrics aggregated from player data.
Excluded as provider `.sql`, and that exclusion is **load-bearing**: verified untouched, still
reading the provider name, no new name leaked in. `int_legs__team_match.sql:120-121` additionally
carries `own.passes_total` / `own.passes_accurate` — TEAM leg columns sharing the player metric
names, also provider-excluded and verified.

⚠ **The substring hazard runs the other way here** and step 3 recorded it: a careless sweep turns
the team's `passes_accuracy_pct` into `passes_accuracy_pct_pct`. Measured after: all three 22-name
team lists still read `passes_accuracy_pct` intact.

## Gates, each unpiped with its exit code read bare

  - `sync_metric_docs_blocks.py --check` → **0**, 175 blocks, delta reconciled term by term above.
  - `check_description_hygiene.py` → **0**. **1604 descriptions — identical to the base**, which is the "re-point them" ruling measured a fifth time. Docs blocks resolved 235 → 237.
  - `check_layer_contract.py` → **0**. `dbt parse` → **0**.
  - `sqlfluff lint` on the 10 changed models → **1**, **proved pre-existing**: same files stashed by explicit path, re-linted at base content, output **BYTE-IDENTICAL**, **zero LT05** both sides. ⚠ The changed **macro** (`player_benchmark_metrics.sql`) is not in that set because CI runs `sqlfluff lint models` — macros are not linted there. Linted separately anyway: 3 LT02 findings at lines 19/20/41, and `git diff -U0` shows this branch touches only lines 26 and 31, so they are provably untouched.
  - `python -m pytest -q` → **0**: **1009 passed, 1 skipped, 14 subtests** — the baseline.
  - `npm test` → **0**: 76/76, including the label-binding guard that is this batch's real frontend check. `npm run build` → **0** on both base and branch: 66 pages, `audit-seo` OK.

## #96 at its widest yet — THREE of six lists, seven entries

| list | names | this batch |
|---|---|---|
| `int_competition_benchmarks.yml:27` / `:66`, `shared.yml:2080` | 22 team | unchanged — `passes_per_match`, `passes_accuracy_pct`, `passes_key_per_match` all intact |
| ⭐ `int_competition_benchmarks.yml:105`, `shared.yml:2186` | 18 player | **both change** — `key_passes_per90` → `passes_key_per90`, `pass_accuracy_pct` → `passes_accuracy_player_pct`; **`passes_per90` correctly does NOT move**. First batch in which either list changes at all |
| ⭐ `shared.yml:1756` | 14 board keys | **three entries** — `passes_total`, `passes_key`, `pass_accuracy_pct` |

Then pinned mechanically: the count-board keys agree as a SET across `mart_leaderboards.sql`,
`accepted_values` and `_LEADERBOARD_METRICS`; `passes_accuracy_player_pct` is a RATE board, so it is
correctly present in the mart and the list and **absent from the export** (rates deferred by #506) —
asserting it "in all three" was a check bug that fired on the first run and was corrected.

## The four range tests — a surface `!127` and `!128` had none of

All four PLAYER tests renamed (`int_player_season_…`, `std_player_…`, `player_profile_…`,
`mart_leaderboards_passes_accuracy_player_pct_in_range`), none left on the old name.
⚠ **And the first version of that check was wrong in a way worth keeping:** it asserted the set of
`*pass*_in_range` tests was exactly those four. There are **eight** — the other four are TEAM tests
on `passes_accuracy_pct` (`mmi_home_…`, `mmi_away_…`, `momentum_team_…`, `std_team_…`) which must
NOT move. Both halves are now pinned, which is strictly stronger than pinning one.
