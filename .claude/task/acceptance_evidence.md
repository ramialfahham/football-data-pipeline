# Acceptance evidence — bound the deserved-points fit to the range it is allowed to occupy

Branch `fix/deserved-points-clamped-to-legal-range`, from main `4ba3011`.

Everything below is measured against **LIVE PROD DATA** by compiling the model and running it
read-only. The ban is on `dbt build`, which writes and bills a materialisation; a SELECT over the
compiled SQL is neither. Same approach `!145` and `!153` used.
⚠ The compiled SQL exceeds Windows' command-line limit, so every query is fed to `bq` on **stdin**.
⚠ `dbt compile` resolves refs against the DEV target, so each query rewrites `dev_intermediate` →
`intermediate` and `dev_scratch` → `dbt_analytics` (seeds ride the profile `dataset:`, which is
`dbt_analytics` on prod). Recorded because reading the compiled file as-is would silently query
datasets that do not exist.

criteria_demonstrated:

  - **Nothing outside the legal range, where there was one row.** New model over prod: **1,125
    fitted rows, 0 out of range, 1 capped.** The live table it replaces has exactly one row
    outside — LP 2026, `team_sk` 211, four games played, `deserved_points` 12.0259 against a
    ceiling of 12.

  - **⭐ Exactly one row moves, and this is a TWO-SIDED result rather than an absence.** A naive
    old-vs-new diff reports **253** rows differing, which looks alarming and is not:

        new model  vs live table    253 rows differ exactly,   1 beyond 1e-9,  max delta 0.0259092103
        UNCHANGED  vs live table    252 rows differ exactly,   0 beyond 1e-9,  max delta 0.000000000000

    The second line is main's own model re-run against the same inputs that built the live table.
    **BigQuery's parallel window aggregates (`avg`, `stddev`, `corr` over a partition) are not
    bit-deterministic**, so 252 rows already disagree at the twelfth decimal on main, with this
    change nowhere near them. Subtracting the baseline, this change moves **one** row, by 0.0259
    points, which is the cap. Had I only run the HEAD side I would have reported 253 changed rows
    and been wrong about 252 of them.

  - **`deserved_rank` and `deserved_points_gap` stay consistent with the capped value.** Measured
    on prod: **0 rank changes** across all 1,125 fitted rows; **0 gap-contract violations**; and
    **0 rank/value disagreements** — every pair of teams in a league-season where one has more
    deserved points also has the better rank, and equal points implies equal rank. That last one is
    the reason the rank is computed from the capped number rather than the raw fit.

  - **The flag is true for exactly the rows the cap moved.** 1 true, 1,124 false, **0 null among
    fitted rows**; null only where there is no fit at all (1,399 of the 2,524 rows).

  - **`int_team_season_deserved_points_in_legal_range` is green on prod and RED without the cap.**
    It can no longer discover the condition, by construction — what it now pins is that the cap is
    wired in, and the mutation matrix below shows it doing that job.

  - **The warn detector reports rather than errors.** Its predicate returns **1** on the healthy
    model today — the LP row — at `severity: warn`, so the build proceeds and the ~620 downstream
    nodes an error-severity failure would skip are not skipped. That is the whole difference between
    this and the failure that stopped the prod warehouse on 2026-09-06.

  - **`dbt parse` exits 0; SQLFluff exits 0** under the dbt templater CI uses, run from
    `dbt_project/` with the venv's Python. Both codes read BARE, never through a pipe.
    `check_description_hygiene.py`, `check_layer_contract.py`, `check_registry_var_sync.py` and
    `sync_metric_docs_blocks.py --check` all exit 0, and `pytest tests/` is 1,011 passed / 1 skipped.
    ⚠ **A NEW TRAP, because it cost a false alarm here: redirecting SQLFluff's stdout on this machine
    makes it exit 1 ON SUCCESS.** Its completion message contains emoji, the console encoding is
    CP1252, and `... > /dev/null` sends it down a path that raises `UnicodeEncodeError` after the lint
    has already finished clean. The repo's "read the exit code bare" rule is what saves you — but
    bare means *unredirected*, not merely unpiped. Set `PYTHONIOENCODING=utf-8` or do not redirect.

  - **The metric definition lives in the SEED, and the generated file is generated.** The
    `deserved_points` description is edited at `dbt_project/seeds/metric_catalogue.csv:78` and
    `dbt_project/models/docs/metric_columns.md` is rebuilt by `scripts/sync_metric_docs_blocks.py`
    (163 blocks). Rendered lengths against BigQuery's 1,024-character column limit, re-measured at
    the FINAL text rather than quoted from an earlier round: `deserved_points` **961** (margin 63),
    `deserved_points_gap` **976** (margin 48), `deserved_rank` 430. ⚠ This line previously read
    "962 / 936 / 430" — the 936 was measured before round 3 lengthened `deserved_points_gap` and was
    left standing. That is `feedback_corrections_replace`: I re-checked the number I remembered
    changing and not the one I did not. Every figure here is now re-derived, not carried forward.
    See the round-1 failure below.

## ⛔ Mutation testing changed the shipped tests, and one mutation still survives

Every cell is the number of rows each test's own predicate returns, run against prod.

| mutation | legal_range (error) | cap_did_not_bind (warn) | flag_matches_value (error) |
|---|---|---|---|
| **healthy** | 0 | 1 — intended | 0 |
| `no_cap` — remove the cap | **1 RED** | 1 | **1 RED** |
| `flag_false` — hardwire the flag FALSE | 0 | 1 | **1 RED** |
| `flag_true` — hardwire the flag TRUE | 0 | 1 | **1,124 RED** |
| `upper_only` — drop the floor half of the cap | 0 | 1 | 0 |

**1. A surviving mutation rewrote the detector.** The warn test was first written as
`not deserved_points_was_capped`. Hardwiring that column to FALSE then **silenced it with every
test still green** — the detector I had just added to replace the detection the legal-range test
lost could itself be switched off unnoticed. It now reads the VALUE (`deserved_points` strictly
inside its bounds) rather than the boolean, because a capped row sits exactly on its bound and the
value carries the evidence with nothing to trust. The flag is pinned separately by
`flag_matches_value`, which is what turns `flag_false` and `flag_true` red.

**2. ⛔ `upper_only` SURVIVES, and it is a data limitation, not a test I can write.** Removing
`greatest(…, 0)` — the floor half of the cap — is caught by nothing. The reason is measured: no
fitted rate in prod is below zero, the minimum is **0.1944**, so there is no row on which the floor
can bind and therefore none on which its removal can show. The floor is there because the outcome is
bounded below as well as above, not because today's data exercises it. Stated rather than left for a
reviewer to find; closing it would need a synthetic fixture for a dbt model, which this repo has no
mechanism for and which is not this MR's to invent.

⭐ Same lesson as `!151` and `!153`, now applied BEFORE a reviewer had to: the mutations worth
running are the ones the design is defended against. `flag_false` is not an accident anyone would
commit — it is the question "what is this detector actually resting on?", and the answer was "a
boolean nothing checked".

## ⛔ ROUND 1 FAILED, and five green gates had nothing to say about why

I wrote the new metric definition into `dbt_project/models/docs/metric_columns.md`, whose own first
line is `GENERATED FILE - DO NOT EDIT BY HAND`. It is produced from
`dbt_project/seeds/metric_catalogue.csv` by `scripts/sync_metric_docs_blocks.py`, and I left the seed
row untouched — so the seed and the generated file disagreed about what `deserved_points` means,
which is the precise drift that rule exists to prevent, and the next sync run would have overwritten
my text with the stale description. `.gitlab-ci.yml:411` runs `sync_metric_docs_blocks.py --check` in
`validate:governance`, so this was a live CI break rather than a latent one.

⚠ **`dbt parse`, SQLFluff, `check_description_hygiene.py`, `check_layer_contract.py` and
`check_registry_var_sync.py` ALL EXITED 0 over the hand-edited generated file.** Two things caught
it, independently and at almost the same moment: `tests/test_sync_metric_docs_blocks.py::
test_the_real_seed_and_the_real_file_are_in_sync`, and `analytics-engineer-reviewer` reading the
file's own header. That is the fourth branch running where every defect came from the blinded review
or the suite and none from the gates.

⭐ The reviewer also caught a stale claim in the model header — *"It sums to exactly 0 across a
balanced (completed) league-season"* — which the cap can break, by exactly the amount it shaves. The
comment now carries the qualifier and says plainly that "no completed season carries a capped row"
is a fact about today's data, not a property of the model. Nothing in the repo asserted the identity,
so nothing went red; a reader would simply have been told something untrue.

## ⛔ ROUND 2 FAILED because I patched THAT claim where it was named and nowhere else

`football-analytics-expert-reviewer` FAILed round 2: the sums-to-zero correction went into the SQL
comment only, while `metric_catalogue.csv:79` (`deserved_points_gap`) still asserted it flatly — and
the seed is the copy that actually reaches readers. `persist_docs` attaches it to the BigQuery
column, `dbt docs generate --static` publishes it, and `scripts/export_site_data.py`'s
`fetch_glossary` ships it into `metrics.json`. Nobody reading any of those cross-references a
model's inline SQL comment.

⛔ **That is `feedback_fix_the_class_not_the_instance`, occurring INSIDE the fix for a finding about
a claim left standing in a sibling artifact.** So round 3 swept the tree rather than patching the
line it named. **Two-sided count: THREE live instances, TWO sources.**

| where | how it was handled |
|---|---|
| the SQL comment in `int_team_season__deserved_vs_actual.sql` | fixed at round 2 |
| `dbt_project/seeds/metric_catalogue.csv:79` | **the reviewer's finding** |
| `dbt_project/models/4_intermediate/.../int_team_season.yml:309` | **the reviewer did NOT name this one** |
| `dbt_project/models/docs/metric_columns.md:306` | generated from the seed; regenerated |

Fixing only what was named would have shipped the third. Rendered lengths after the edit:
`deserved_points` 962 (margin 62), `deserved_points_gap` **976 (margin 48)** against the
1,024-character column limit.

## ⛔ ROUND 3 FAILED TWICE, and the second sweep missed by the same method as the first

**1. `scope-auditor` — I decided something that was not mine.** I kept `severity: warn` and justified
it by analogy after conceding it matched none of `engineering_standards.md` §3's three rows. It
quoted the rule I had broken while breaking it, `docs/working_agreement.md:328`: *"when a new case
does not clearly match a written rule, the classification itself is a CPO decision. 'It's analogous
to X' is not a license."* ⚠ The two reviewers had reached OPPOSITE conclusions on the same question,
which is itself the argument that it was not mine. Escalated; ruled **"warn"**; recorded in
`escalations.log`.

**2. `analytics-engineer-reviewer` — a now-false formula sentence, THREE LINES from the one I had
just patched.** `int_team_season.yml:305-307` still said *"deserved_points is that rate times the
team's games played"*, which is false today for the LP row where the served value is the capped rate
times games.

⛔ **Both sweeps missed the same way, and the method is the fault.** I grepped the phrase a reviewer
named. That finds instances of that phrase; it does not find the other statements the change
falsified. **Sweeping INVERTED — enumerate every claim about the quantity, ask whether each is still
true — found the yml sentence AND a second one no reviewer reached:**

`site_v2/src/components/team/DeservedHero.astro:97` says deserved totals are colinear in `sotd`
"only when every team has played the same number of games". The cap makes that insufficient, and the
comment is LOAD-BEARING: it justifies drawing the trend as a segment between **the two extreme-`sotd`
dots' served values**. The cap binds precisely at the extremes — the capped team is by construction
the one with the most extreme signal — so for a capped league-season the line is drawn through a
capped endpoint and is no longer the model's line. My own impact map called this tolerable on the
grounds that "the component plots dots and the trend independently"; the dots are independent, the
segment endpoints are not. Corrected there, and out of scope here.

## ⭐ A WRONG DECISION OF MINE THAT PASSED REVIEW, overruled by the CPO

`decisions_taken` asserted *"the integer domain is a display property, and stays one"*, citing that
`DeservedHero.astro:79` already renders `integer(...)`. His ruling: **"Rounding is business logic."**
He is right, and the rule was already written — the consumption layer may select, filter and order,
never derive. I was pointing at a defect and calling it a design, and **two blinded reviewers passed
it**. A sweep of `site_v2/src` found three places deriving a number the reader sees; two-sided, four
more were checked and CLEARED as presentation. Filed as **GitLab #108**. Not fixed here: serving the
integer changes what reaches the frontend, so it touches the mart, the export and the trend line.

⚠ Also this round: `deserved_points_was_clamped` → **`deserved_points_was_capped`**, and the test
`..._deserved_clamped_flag_matches_value` → `..._deserved_capped_flag_matches_value`, so the column
and test match the word the ruling used and all four prose copies use.
`football-analytics-expert-reviewer` raised the inconsistency without failing it. The mutation matrix
was re-run after the rename and is byte-identical to the table above.

## What this does NOT do

- **It does not change when the read is SHOWN.** The two open CPO questions on this hero — how to
  render the fitted line mid-season, and from which matchday to show it at all — are untouched, and
  raising a matchday threshold later is still fully available.
- **It does not round the stored value.** The integer domain is honoured at the page
  (`DeservedHero.astro:79`), and moving it into the warehouse was rejected on measurement: rows tied
  on `deserved_points` would go from 75 of 1,125 to **252 of 1,125**, making a fifth of
  `deserved_rank` an artifact of rounding, and it would scatter the hero's dots off the trend line
  they are colinear with.
- **It does not touch the freshness guard.** `assert_fct_fixture_no_stale_live` uses a 3-hour window
  against a once-daily ingest and has been failing the nightly roughly one night in three (9 of the
  last 29 executions). Diagnosed in the same session, deliberately left to its own contract.
- **It does not fix the handover's claim** that the nightly put `is_current_season` in prod. It was
  `data:build:main` on the !153 merge. Left for the next handover MR rather than smuggled in here.
