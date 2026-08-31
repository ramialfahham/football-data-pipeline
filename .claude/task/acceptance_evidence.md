# Acceptance evidence — step 4, MR 7: the seven player `goals` metrics. THE LAST BATCH.

Branch `refactor/metric-rename-player-goals`, from main `6f0ee07`.

    goals           →  goals_player            assists       →  assists_player
    goals_penalty   →  goals_penalty_player    scorer_points →  scorer_points_player
    goals_open_play →  goals_open_play_player  penalty_won   →  penalty_won_player
    contribution_share →  contribution_player_pct

**1,519 occurrences across 93 swept files → 38 files changed.** Decided once each:
**279 renames · 63 `doc()` re-points (19 TEAM-side) · 1,177 protected.** The most protective batch
of the programme by a distance — `goals` is the most generic stem in the domain, and 78% of every
occurrence carrying the stem stays exactly where it is.

⭐ `contribution_player_pct` **IS ruled**, verbatim: *"contribution_player_pct is fine, go with it"*
(`escalations.log`, 2026-08-29). That entry also says the older *"flag it rather than quote it as
his"* caveat is **DISCHARGED and does not need to travel further** — I carried it anyway into this
MR's contract, evidence and log entry. Corrected; found by `football-analytics-expert-reviewer`.

Every gate below was run **unpiped, with its exit code read bare**.
⚠ `check_ui_i18n_metrics.py` is run because it is a real CI gate but is **NOT evidence** here.

criteria_demonstrated:

  - **The TEAM scoreline family is untouched.** Asserted mechanically over the whole diff: **zero**
    added lines carry a renamed token beside `goals_for`, `goals_home`, `goals_away`, `goals_diff` or
    `goals_own`. `export_site_data.py:1044/1046` — `"goals": r.get("goals_home")` — is byte-identical,
    which is the exact shape that FAILed `!131` round 1.
  - **The CPO's payload ruling is implemented on both sides of all four lines.**
    `_shape_squad_member` and `_shape_player_career_season` now read
    `career.get("goals_player")` / `row.get("goals_player")` while still emitting the key `"goals"`.
    Verified by reading `export_site_data.py:192-193` and `:443-444` directly.
  - **No `site_v2/` file changes** — `git diff --name-only -- site_v2/` is empty. Thirteen frontend
    files carry a swept token and every one protects: `PlayerRow.astro` reads the PROVIDER columns
    `goals_total`/`goals_assists`, the rest are team scoreline fields, TEAM label keys or UI words.
    Re-derived for this batch rather than carried from `!131`, where the opposite was true.
  - **Doc blocks 167 → 163**, matching the pre-code simulation term for term: 22 removed, 18 added,
    three collapses and the eight renamed yoy blocks. `sync_metric_docs_blocks --check` EXIT=0.
  - **All 16 `doc()` references to the eight derived player yoy blocks resolve** —
    `check_description_hygiene` EXIT=0 at **1604 descriptions, 225 blocks resolved** (229 at base;
    the −4 is the three collapses plus the four deleted orphans), which is the proof none dangles.
  - **The seed differs from base in `metric_id` ONLY**, on every row — checked field by field across
    the whole file, after a first apply that did not (see §(a) below).
  - **Every dotted and bare reference resolves**: the resolver reports zero broken references and
    `check_yml_vs_projection` zero mismatches, over both the old and new names.
  - **Documentation prose survives the sweep; identifier references in documentation move; and a
    formula quoted in a comment moves WHOLE** — the round-1 defect, its over-correction and the
    round-2 defect, closed by one role rule in two reaches (§(d), §(e)). Verified in both directions:
    **0** hits for eleven prose-corruption strings, **0** half-renamed formula comments, and each
    named identifier site confirmed moved.
  - **The rendered pages are unchanged**: base vs branch, **12/12/12 rows, 7/7/7 headings, none added,
    none removed** in EN/DE/FI across 19 fixture pages, both sides built from a stashed tree.

## Gates

  - `sync_metric_docs_blocks.py --check` — **EXIT=0**, 163 blocks.
  - `check_description_hygiene.py` — **EXIT=0**, 1604 descriptions, 225 blocks resolved.
  - `check_layer_contract.py` — **EXIT=0**. `check_registry_var_sync.py` — **EXIT=0** (48
    competitions). `check_ui_i18n_metrics.py` — **EXIT=0** (13 shown metrics).
  - `dbt parse` — **EXIT=0**.
  - `python -m pytest -q` — **1009 passed, 1 skipped, 14 subtests**, matching the `6f0ee07` baseline.
    Re-run in full after the sweep was re-applied from base for round 3.
  - `sqlfluff lint` on the thirteen changed models, from the REPO ROOT, full rule set —
    **byte-identical** to a re-lint of the same files stashed back to base: 27 violations both
    sides, same rules, same lines. ⚠ §(e)'s fix lengthens two comment lines by 7 characters; measured
    at ~106 against `.sqlfluff`'s `max_line_length = 120`, and the byte-identical result confirms no
    LT05 newly trips.
  - `npm test` — **76/76**. The site built: 66 pages, `audit-seo: 67 built page(s) checked. OK.`

## ⛔⛔ FIVE defects the implementation surfaced — and how each was found

Each was fixed as a RULE, not an edit. **The means matter more than the defects.**

**(a) Found by a CHECK.** The seed's `contribution_share` row glosses its own formula as *"the
player's goals + assists (scorer_points)"*. The token-level rule — placed BEFORE the seed's field
allowlist — rewrote it to `(scorer_points_player)`. **A rule checked before the allowlist silently
reopens the hole `!131` closed.** The allowlist now outranks it. Verified after: **0 non-`metric_id`
seed fields differ from base.**

**(b) Found by READING the applied diff.** `mart_player_career.sql:130` documents the catalogue row
as *"(entity=player, group=goals, tier 1)"*; the first apply made it `group=goals_player`, naming a
metric_group that does not exist. `goals` is a metric_GROUP value as well as a metric_id
(`seeds/schema.yml:330` lists it beside "shooting"), so the rule is now positional. ⚠ **The token
counts were identical before and after the fix** — no total, guard or gate could have shown it.

**(c) Found by the TEST SUITE.** I put `tests/test_export_site_data.py` in the same role set as the
export and **pytest failed three tests**. The rule was not stale, it was INVERTED: in the test file a
dict KEY is a fixture (a mart row, which must move) while the payload keys appear as SUBSCRIPTS and
as members of an expected-key set. No single subscript rule works either —
`boards["goals_player"]` subscripts a dict keyed by metric_key, which does move. So the test file
follows the mart, and five assertions about the shaped OUTPUT are corrected by hand.
⭐ **`!131` recorded that an automated rename editing code and test together leaves the suite unable
to disagree. Here it disagreed** — because §2's ruling deliberately holds one side still, so the two
could no longer move in lockstep. **A rule that forces the code and its test apart is what makes the
test able to fail.**

**(d) Found by the BLINDED REVIEW — and I got it wrong twice before getting it right.**
Round 1 FAILed **5–0**. `scope-auditor`, `analytics-engineer` and `football-analytics-expert` all
found the same class: the sweep had rewritten ENGLISH PROSE, because `goals`/`assists` are ordinary
words. It shipped *"the club's WHOLE-SEASON goals_player"*, *"own goals_player"*, *"Involved in 45%
of Bayern's goals_player"* — and `+persist_docs` publishes those to BigQuery, so a stranger would be
told a club's season goal total is called `goals_player`. **Worse, `int_player_profile__contribution`
said it two ways in ONE docstring**: the prose mislabelled, the formula line beneath it correct.
⛔ **My first fix over-corrected.** I protected any occurrence that was not a whole backticked span,
and `bi-analyst` caught the other side of it in the same round — `` `mart_player_career.goals` ``
(dotted), `` `goals − goals_penalty_player` `` (a formula operand) and the `Atomics` column's
`goals, assists` were all left stale, the last one two rows above ids `!130` had already renamed.
⭐ **The rule that actually holds is ROLE, not punctuation**, which is what step 4 has been
learning all along. In a markdown table the **column header** states the role, so the census was
taken over every table cell in the repo carrying the bare stem — **16 distinct column headers, three
roles**:
    IDENTIFIER  `Source column` · `Atomics` · `numerator` · `denominator`      → moves
    PAYLOAD     `Payload key` · `JSON key`                                     → stays (the CPO's ruling)
    PROSE       Element · Ruling · Gap · Notes · Component · Display string …  → stays
Outside a table the backtick still decides, and `{goals}` is excluded as a template slot — proved by
its own sibling row, where `{won} of {total} · {pct}%` sits against atomics `duels_won_player,
duels_player, duels_won_player_pct`. **The slots were never the ids.**
⭐ `11_team_squad.md:120` is the single line that demonstrates both rulings at once, and it is now
right in both halves: `` `squad[].goals` `` stays, `` `mart_player_career.goals_player` `` moves.
**Measured over all 51 in-table occurrences: exactly 6 move, 45 stay**, and the 100 occurrences the
prose rule moved out of RENAME are the whole difference between round 1's counts and these.

**(e) Found by the BLINDED REVIEW AGAIN — round 2, and it is (d)'s rule meeting a construct outside
its reach.** Round 2 came back 4 PASS / 1 FAIL. `analytics-engineer` found two SQL comments —
`int_player_season__metrics.sql:112` and `int_player_season_position__metrics.sql:155` — reading

    -- finishing efficiency (CPO Option A): open-play conversion = (goals − goals_penalty_player) /

directly above code that correctly computes `(goals_player - goals_penalty_player)`. A **formula
quoted in a comment**, half-renamed: every other name in the sentence had already moved, so the
comment contradicted the three lines beneath it.
⭐ **It is the identical construct (d) fixed at `12_player_stats.md:142` via the `numerator` column
— the role rule simply had no reach outside a markdown table.** The fix gives it one:
`in_operand_position()` treats a token inside a parenthesised arithmetic expression that also names
an underscored identifier as an operand, not a word. Both conditions are required, and together they
are exactly what separates a quoted formula from English: prose says *"penalty goals"* and *"own
goals"* with no operator and no underscored neighbour, and never inside parentheses holding both.
⭐ **Census over every comment line in the repo carrying a bare swept token — 26 occurrences: the
rule moves exactly 2 and keeps all 24.** The 24 include "own goals", "Penalty goals", "goals/subs",
"goals sum", `group=goals`, and `mart_player_momentum.sql:72`'s *"goals, then assists, then key
passes"* — which describes an ORDER BY over the PROVIDER columns `goals_total`/`goals_assists`, so it
is doubly protected.
⛔ **The honest reading of (d) and (e) together: I set this rule three times.** Too wide (prose
rewritten), too narrow (identifier references left stale), then correct in tables but blind outside
them. Each miss was the same root — a scope coarser than the role it had to resolve — and each was
found by review, never by a gate.

## Predictions written before the code, then measured

  - **Blocks 167 → 163** with the exact removed/added sets, simulated against the real generator with
    both the seed renames and the eight derived-column renames applied in memory. Measured:
    **163**, sets identical. **CONFIRMED.**
  - **The eight derived player yoy blocks are NOT orphans** — 2 live references each, 16 in all.
    Confirmed by grep before the work, and by the hygiene gate staying green after it.
  - ⛔ **DISPROVED, and the correction is the interesting half.** I predicted `goals`,
    `goals_open_play` and `goals_penalty` would all leave the hygiene gate's ambiguous-name list,
    leaving `league_code` alone. Measured base-vs-branch: the list goes **4 → 3**, not 4 → 1.
        base    goals_against · goals_open_play · goals_penalty · league_code
        branch  goals_against · goals_penalty · league_code
    `goals_open_play` leaves. **`goals_penalty` does not** — and its two variants CHANGE identity,
    from the doc-block pair `goals_penalty__player`/`__team` to the real columns
    `goals_penalty`/`goals_penalty_player`. The cause is exactly `!131`'s ruling, which this MR's own
    plan named in §3 and this evidence then contradicted: **`goals_penalty` is also a PROVIDER leg
    column**, so renaming the metric cannot disambiguate the name. `goals_against` stays for the
    same reason, from `!131`. **A rename frees a name from #87 only when no provider column shares
    it** — that is the general rule, and it now has two independent confirmations.

## The three collapses, and a mechanism that runs out of instances

    167 → 163   (22 removed, 18 added)
    REMOVED  goals__{player,team} · goals_penalty__{player,team} · goals_open_play__{player,team} ·
             assists · penalty_won · scorer_points · contribution_share ·
             the 8 goals_/assists_ yoy __player blocks · 4 goals_*__team orphans (0 refs, verified)
    ADDED    goals · goals_player · goals_penalty · goals_penalty_player · goals_open_play ·
             goals_open_play_player · assists_player · penalty_won_player ·
             scorer_points_player · contribution_player_pct · the 8 renamed yoy __player blocks

**63 `doc()` re-points, 19 of them TEAM-side.** ⛔ **After this MR no metric in the catalogue
disagrees across entities** — all six dual-entity ids have been renamed across step 4.
`sync_metric_docs_blocks.py`'s module docstring used `goals_open_play` as its worked example of the
collision; it is rewritten to state the rule and mark every such example historical. **Nothing is
deleted**: `_derived()` still suffixes unconditionally, `_blocks()` still splits and still aborts,
and the synthetic fixtures stay. One new seed row recreates the collision.

## Two more trap classes this stem adds

**`goals` as an ENGLISH WORD**, across nine documentation files including `CLAUDE.md`,
`docs/north_star.md` and `docs/data_contract.md` — all protected, each a printed decision, and §(d)
above is what it cost to get right.
**`goals` as a metric_GROUP value** — `seeds/schema.yml:330`'s enum, and the inline `group=goals` in
(b) above.
⭐ Where a token rule met documentation prose, the **backtick** decides outside a table and the
**column** decides inside one: `content_architecture.md:92`'s backticked `` `contribution_share` ``
renames, while `schema.yml:339`'s plain-prose *"goals, assists and scorer_points"* does not — because
renaming only the third would have shipped an internally inconsistent sentence. **`seeds/schema.yml`
therefore does not change at all.**

## #96 and #99

**#96 is narrow**: only `shared.yml:1756`'s 14-name board list moves, **2 entries** (`goals`,
`scorer_points`); the other five lists carry protected-only hits, including all three 22-name TEAM
lists and both 18-name player lists (whose hits are all `_per90`). Compared base-vs-branch in FILE
ORDER with a length assertion.
**#99 comes due, as the handover predicted**: `_LEADERBOARD_METRICS` / `_LB_KEEP` carry the literal
board keys `"goals"`, `"assists"`, `"scorer_points"`, and they follow the mart's `metric_key`.
**Still pinned by no test** — carried, not closed.
