# Active work — handover

> The single handover contract. A fresh chat continues from here. Do not re-scope or infer the task
> from an issue title or a memory file. CURRENT STATE ONLY — history belongs in git. Under 16,000
> **CHARACTERS** (`handover_in.py:46`) — measure with Python `len()`, never `wc -c` (BYTES).

_Last updated **2026-09-01**. **main `22c8d9b`**, clean, no open MRs.
⭐⭐ **THE NAMING PROGRAMME IS DONE AND SO IS THE WORK IT OWED.** Step 4: all 35 player metrics carry
`_player` across seven MRs (`!125`–`!132`) — verified on main, of 48 player catalogue rows the only
one without a `_player` marker is `minutes_per_appearance`, the one name the record's "UNCHANGED,
all 14" list names. Step 5 (`!134`): the English label reads "on goal" — verified, **0** `label_en`
and **0** `METRIC_LABELS_EN` values still say "on target". The sample roll-forward (`!136`): the
build sample now pins **2026-09-01**, and the comparison renders **16 rows again, not 12**.
**GITLAB** (`glab`, MRs); runner `ci-runner-01`.
⚠ **A GROUP MOVE IS COMING**; it changes the project PATH, breaking remote URLs, the WIF binding on
`attribute.project_path`, and every hardcoded `rami.al-fahham/football-data-pipeline`._

## ⛔⛔ NEXT ACTION: NONE. THE QUEUE FROM THE NAMING PROGRAMME IS EMPTY.

⭐ **THE NIGHTLY LIVES IN CLOUD SCHEDULER — answered, not open.** Two ENABLED jobs in
**europe-west1**: `fdp-nightly` (`0 4 * * *`, ingest + full prod dbt build) and `fdp-freshness`
(`7 * * * *`, hourly). The CPO moved them there after GitLab CI limitations made a CI-hosted cron
unworkable. **The data IS refreshed on a timer**, which is why the warehouse was fresh enough for
`!136` to work.
⚠ `data:nightly` in `.gitlab-ci.yml` is NOT the nightly — nothing triggers it. GitLab schedule
`4379625` is deliberately **DISABLED** (last run 2026-08-10). **Enabling it without disabling
`fdp-nightly` runs the build twice.**
⛔ **AND THE LESSON THAT COST A WHOLE INVESTIGATION, 2026-09-01.** These jobs authenticate as
`github-actions-dbt@…`, a legacy GitHub-era name the GitLab migration reused. I reported a daily
04:02 pipeline to the CPO as UNEXPLAINED recurring spend, and named GitHub Actions as the cause from
the SA's name plus a leftover workflow file with a matching cron — both circumstantial, both wrong.
His reply settled it: *"We moved these two jobs to the cloud after your recommendation. We did this
after I ran into CI limitations with Gitlab."*
⭐ **Two rules out of it.** (1) **Identify a caller by its AUTH PATH, not its name** — that SA has
zero user-managed keys and one `workloadIdentityUser` binding, so GitHub could never have been it.
(2) **Before reporting anything as unexplained, check whether it is simply undocumented** — it was a
deliberate, authorised decision that no document recorded, and the doc gap was the only real defect.
⚠ Measured cost of the two jobs: **~129 GB/day ≈ 3.8 TiB/month ≈ $17–24**, recorded because it was
written down nowhere. Whether `fdp-freshness` needs to be hourly is the CPO's call, untouched.
⭐ **THE RUNBOOK IS `deploy/nightly/README.md`** — jobs, scheduler, IAM, and the `gcloud` that built
them. ⚠ I claimed this was "recorded nowhere" and it was not: I went from BigQuery metadata straight
to `CLAUDE.md` and never searched the repo. **"Undocumented" is a claim about the WHOLE tree — one
`git grep` for the identifier settles it.**
⭐ To measure it yourself: `region-eu.INFORMATION_SCHEMA.JOBS_BY_PROJECT` (⚠ **EU, not US** — a
`region-us` query returns a comfortable and completely false "0 jobs, no cost"), and pull a RANGE of
days: my first figure was ~$7/month from a single day that happened to be the smallest of fourteen.

## ⛔ THE SAMPLE IS FRESH TODAY AND WILL GO STALE THE MOMENT THOSE FIXTURES KICK OFF

`!136` pinned the **2026-09-01** matchday: 4 fixtures, 3 competitions (`CIT` ×2, `DFBP`, `SPL`).
⚠ **A past fixture can NEVER be re-exported** — `fetch_fixture_payloads` emits `status_short in
('NS','TBD') and fixture_date >= current_date()`, and once a match kicks off its pre-match form rows
leave `mart_team_momentum` entirely. So this set is already unrefreshable, exactly like its
predecessor. **The next refresh REPLACES it wholesale; it can never be updated in place.**
⭐ The full recipe, the traps and the four-list consistency check live in
`site_v2/src/data/README.md` — follow it verbatim rather than reinventing it.
⚠ It is deliberately thin (4/3 against the outgoing 19/13) on a CPO steer that this is
infrastructure with nothing on display. Coverage was MEASURED, not hoped: both competition shapes,
all three form paths, and the row-omission path. A richer matchday (2026-09-04 had 28 fixtures /
16 competitions) is available whenever a fatter sample is wanted.

## ⛔ TWO FOLLOW-UPS STEP 5 DELIBERATELY LEFT — flagged to the CPO, not folded in

Both were disclosed in `!134`'s `decisions_reserved` and confirmed untouched by two reviewers. Each
is small; neither was taken, because widening scope mid-MR is what this programme was FAILed on.

  - **The seed's `description` column.** ~19 descriptions still say "shots on target" as prose, so a
    row's label now reads "on goal" while its own description disagrees — and `persist_docs`
    publishes those descriptions to BigQuery.
  - **Four CHROME strings in `strings.ts`'s `Dict`** that name the same metric in rendered English:
    `axPlay` ("Shots on target difference / match", the team hero's x-axis) and
    `heroVerdictUnder`/`heroVerdictOver`/`heroCaption` ("a shots-on-target difference of {sotd}…").
    ⚠ **When the team Performance surface ships, that axis will read "Shots on target difference"
    beside a metric row reading "Ø Shots on goal difference".** Neither renders today.
  ⛔ **`label_i18n_key` is NOT one of these.** `metrics.shots_on_target_per_match.label` stays: it is
  the join key across the seed, `strings.ts`, `metricRows.ts`, three parsers and the page specs, and
  the catalogue declares no `..._on_goal_...` variant, so "fixing" it resolves the label to nothing.
  Four separate comments now say so; one more (`check-page-specs.test.mjs:179`) is still true because
  it compares the id to the KEY, not to the user-facing term.

## ⛔ WHAT STEP 5 IS PINNED BY — and what it is NOT

**Nothing pins the wording of the four rendered labels.** Mutation-tested and confirmed by two
reviewers independently: emptying a label goes RED, but putting `"Ø Bananas per fortnight"` in one
leaves `npm test` **green**. Three of the four also render on **zero** built pages (they live on the
unbuilt team Performance surface), so only `Ø Shots on goal` is provable from `dist/`.
⭐ The reason is structural, not accidental: the byte-identical gate compares only keys present in
BOTH `strings.ts` and the frozen `site/i18n` corpus — three of the four are absent from it and the
fourth is skipped by name.

## ⛔ OPEN, AND THE CPO'S — carried, never decided

  - ⭐ **The `__team`/`__player` doc-block split now has NO live instance.** All six dual-entity ids
    (`duels_won_pct`, `saves`, `goals_against`, `goals`, `goals_open_play`, `goals_penalty`) were
    renamed on the player side, so no catalogue metric disagrees across entities any more.
    ⛔ **Nothing was removed or weakened**: `_derived()` still suffixes unconditionally, `_blocks()`
    still splits and still aborts on rows it cannot tell apart, the synthetic fixtures stay, and one
    new seed row recreates the collision. ⚠ The cost is concrete: **five files documented the
    mechanism with a worked example the programme then falsified.** Whether a guard with no live
    instance should remain is his call.
  - **A rename frees a name from #87 only when no PROVIDER column shares it.** Measured twice
    independently (`!131`, `!132`): the hygiene gate's ambiguous-name list went 4 → 3, not 4 → 1.
    `goals_open_play` left it; `goals_penalty` and `goals_against` did not, because both are also
    provider leg columns. **#87's 49 blank columns are NOT freed by this programme.**
  - **The column-reference resolver as a committed CI gate.** `!129` found four blind spots; `!130`
    and `!131` bounded it further (dotted references only; the projection check's weak form). Not
    proposed.
  - **#99** — the export's literal board keys moved in `!132` and remain pinned by NO test.
  - **`_LEADERBOARD_METRICS` / `_LB_KEEP`** pinned by no test, confirmed by `platform-reviewer` on
    five MRs. ⭐ `!131` added that the OTHER export path is unpinned too: `shape_top_players`'
    DROP-list means `TopPlayer` fields reach the frontend with no test between mart and component.
  - **#96** — eleven reproductions; no offline gate checks `accepted_values`, only `data:build:mr`.
  - **#98**; the doc-block inheritance trap.

## ⛔ WHAT THE SWEEP MRs PROVED — read before any similar rename or text sweep

The programme is merged; the MR-by-MR account is in git and in
`feedback_fix_the_class_not_the_instance`. What survives is the method.

**1. A SCOPE COARSER THAN THE ROLE IT MUST RESOLVE IS THE ONE RECURRING DEFECT** — it FAILed review
on `!131`, `!132` (three rounds) and `!134`, **with every gate green every time**. The fix is never
an exemption list; it is a finer rule with a checkable property. The ones earned so far:
  - entity by enclosing model (`- name:` in yml), by the seed's `entity` column, by file for SQL
  - **role** where two meanings share a line: `t(lang,"x")` is a UI word, `player.x` a payload field,
    `.get("x")` a warehouse column, `"x":` a payload key, `group=x` a metric group
  - **a domain fact** where one exists — there is no player `goals_for`, so the scoreline family is
    the team's; that one discriminator separated 6 wrong renames from 60 right ones
  - **in a markdown TABLE the COLUMN decides**, not the backtick (`Source column`/`Atomics`/
    `numerator` are identifiers; `Payload key`/`JSON key` stay; the rest is prose)
  - **outside one, an OPERAND is an identifier**: a token in parentheses holding BOTH an arithmetic
    operator AND another underscored identifier is a formula quoted in a comment
  - `{placeholder}` is a template slot, never an id

**2. CENSUS THE TREE, COUNT BOTH DIRECTIONS, AND MATCH A PATTERN NOT A LIST.** Report every sweep as
"N move, M stay" — a one-sided claim ("the prose is fixed") is what let an over-correction through.
⛔ And write the separator as a character class BEFORE counting: `!134` FAILed round 1 because the
census matched `"on target"` and `"on-target"` but never `"on_target"`. **An enumeration of spellings
loses by one variant.** ⚠ A pattern buys false positives too — `README.md`'s "ingesti**on target**".

**3. ALLOWLIST, NEVER BLOCKLIST — AND NOTHING MAY BE CHECKED BEFORE IT.** A blocklist of 5 of the
seed's 15 columns swept `interpretation`; the fix is a field allowlist. Then `!132` and `!136` both
proved the second half — a token rule placed BEFORE the allowlist silently reopens the hole.

**4. WHAT ACTUALLY FINDS DEFECTS**, in order: the **blinded review** (every defect of the last four
MRs, all with gates green); **reading the printed decisions and the applied diff** (defects whose
counts were identical before and after); and the **test suite** — but only where a ruling forces
code and test apart. Where a sweep edits both sides in lockstep, green means nothing.

**5. SIMULATE THE GENERATOR BEFORE PREDICTING**, and **report the disproved predictions** — that is
how the "a rename frees a name from #87 only if no provider column shares it" rule got confirmed.

**6. TWO GUARD FACTS, MEASURED.** `check_description_hygiene` DOES catch a dangling `doc()`.
`check_yml_vs_projection` does NOT catch a column dropped from the final SELECT while still named in
a `safe_divide` on it — token presence, not projection. Mutation-test any guard before citing it.

## ⛔ TRAPS THAT COST REAL TIME

⚠ **CWD persists between Bash calls** — a `cd` in one call breaks repo-relative paths in the next;
it aborted an apply mid-run on `!131` and again on `!132`.
⚠ `git checkout -- .` reverts the CONTRACT too if it is unstaged — exclude it explicitly.
⚠ A file that falls to ZERO renames is never reopened by the no-op-write guard, so it keeps its
previous text: restore it from base explicitly and re-reconcile `scope_paths`.
⚠ `git grep` is BRE — `[` opens a character class, so `git grep 'values: ['` silently finds nothing.
Use `-F`.
⛔⛔ **`--review-patch` PRINTS; only a REDIRECT writes the file — and it reads the INDEX, not the
working tree.** `git_discipline.py --review-patch` builds from `git diff --staged <base>`, so running
it bare emits to stdout and **leaves the previous round's `review_input.patch` on disk**, exit 0. On
`!132` that served all five reviewers the ROUND-1 diff: two FAILed on defects already fixed, quoting
offsets that no longer existed. Correct call: `git add -u` then
`… --review-patch > .claude/task/review_input.patch`.
⭐ **The tell is free: `--staged-hash` printing `e3b0c442…`** = `sha256("")`, an empty staged diff.
Never write it into `review.md`.
⭐ **When two reviewers contradict each other on the same tokens, suspect the ARTIFACT before the
code.** One reading files said clean, one reading the patch said corrupted; that resolved it in one
step.
⚠ **`subprocess.run(..., text=True)` decodes with the WINDOWS locale (cp1252), not UTF-8.** Comparing
`git show <base>:file` against a UTF-8 read reports every non-ASCII character as a difference — `Ø`
arrives as `Ã˜` — and made a byte-identical seed look like 32 corrupted fields. Capture BYTES and
`.decode("utf-8")` both sides. The seed's `label_en` column is full of `Ø`.

## Method that works — seven MRs of evidence

Contract FIRST on a clean tree (the gate refuses otherwise; stash by explicit path with a `TEMP-`
label, verify your own entry is on top, pop immediately). Classify every token once and **print the
decision with its resolved entity**; abort before writing on any protected-count change or unlisted
file; maximal-token matching; multiset verify over old ∪ new; no no-op writes. Then gates unpiped
with exit codes read bare, mutations watched RED, two site builds, five blinded reviewers,
`review.md` with `--staged-hash`. **ROUND CAP 3** — past it, STOP and bring the findings; a fourth
round needs the CPO's word recorded as `rounds_cap_override:` in `review.md`, or the commit gate
refuses. Each reviewer section needs `## <exact-routing-key>`, then `VERDICT:`, then a
`risks_checked:` block — a PASS with an empty one is rejected. The classifiers are in the scratchpad
(`rename_s4_goals.py` is the most developed) and are deliberately **not committed**.

## Standing traps (also in CLAUDE.md)

`git commit` must be the SOLE command in a Bash call. Heredocs are gate-blocked for file writes —
use Edit/Write. `review.md` must be COMMITTED. `acceptance_evidence.md` needs a
`criteria_demonstrated:` block with one 15+ character bullet per declared criterion. Contract edits
need a CLEAN tree. Never read a gate's exit code through a pipe.
