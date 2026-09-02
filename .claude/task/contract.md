# Task contract — the assists board, and a club on every leaderboard row

objective: >
  **Close two registered gaps against `mart_leaderboards`, both prerequisites for Home's Top players
  block.**

  · **GAP-30** — add `assists_player` to `count_boards`. The approved four-board design is
    goals → **assists** → passes → key passes; three are boards, assists is not, so the second board
    of four has no rank to read. The column already exists on the mart and upstream; it simply never
    appears in the board list.
  · **GAP-27** — carry the player's club on every row. Today a leaderboard row links to a player and
    to nothing else, which halves the internal-link value the block exists for.

  ⚠ **NEITHER IS A DESIGN DECISION.** Both implement designs already approved; the register's
  "NOT YET RULED" on GAP-30 is a stale status field, corrected in this MR.

refs: >
  **CPO, verbatim, this session:** *"go ahead"*, on a plan naming exactly these two gaps as the
  first of three warehouse steps for Home. Preceded by *"For every page we need to know what is
  missing so it can be built. Home first anyway."*

  **CPO, on GAP-30 being treated as an open question:** *"So what's the question. The player block
  has assists in the mockup."* — correct, and the reason the register's status field is fixed here.

  **`docs/wireframes/99_gaps_register.md`** — GAP-27 (*design approved* CPO 2026-08-08) and GAP-30.
  **CPO 2026-08-08**, quoted in GAP-27: *"clicking a team, competition or player goes deeper into
  the site"* — the club link is the point of the block.
  **GitLab #40** — the four-board design. **GitLab #41** — *"Every row carries the club crest image
  — the team logo, on player rows as well as team rows"* (CPO 2026-08-10).

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/docs/layering.md
  - docs/wireframes/10_home.md
  - docs/wireframes/99_gaps_register.md

protected_override: >
  ⛔ **NO EXPORT CHANGES.** `_LEADERBOARD_METRICS` and `_LB_KEEP` in `scripts/export_site_data.py`
  will both need edits before this reaches a payload — and they are deliberately NOT touched.
  **No page or component consumes the leaderboards payload today** (`grep -rn "leaderboard"
  site_v2/src` returns nothing), and the register's own rule is that *"gap fixes never ship inside
  blueprint PRs"*. The export wiring belongs with the block build, which must touch it regardless.

  ⛔ **NO RANKING LOGIC CHANGES.** The `dense_rank() over (partition by league_code,
  season_api_year order by <key> desc)` stays exactly as it is. The block is **one player per
  league**, not a pooled ranking (GAP-31 WITHDRAWN, CPO 2026-08-18: *"One per league -> yes, it's
  not a leaderboard in the defined pool."*), so the existing partition is already the right shape.
  ⚠ `#40`'s prose still says pooling is the real gap; it predates that withdrawal and is stale.

  ⛔ **NO CHANGE TO `board_rank <= 10`.** The block shows 7. That is a display cut, not a mart one.

  ⛔ **NO NEW METRIC, AND NO METRIC DEFINITION WRITTEN BY HAND.** `assists_player` is an existing
  catalogue metric. Per `engineering_standards.md` §2, a metric's definition is GENERATED from the
  seed — writing one into this YAML would create a second source.

impact_map: >
  `mart_leaderboards` is read by no other model (`dbt ls --select mart_leaderboards+`) and by no
  frontend component. `scripts/export_site_data.py` reads it into a `leaderboards` export target
  that nothing renders. So the blast radius is the mart's own rows and columns.
  ⚠ **Row count MOVES, deliberately** — one new board adds one union-all branch, so the mart gains
  the assists board's rows. Every existing board's rows are unchanged. This is the one claim worth
  measuring rather than asserting.
  ⚠ The four club columns are ADDITIVE; no existing column changes type or meaning.

acceptance_criteria:
  - `count_boards` gains exactly one entry; the compiled SQL has **15** union-all branches, not 14,
    and the new branch carries `where assists_player > 0` and the unchanged partition.
  - Four club columns — `team_sk`, `team_name`, `team_slug`, `team_logo_url` — are projected, via a
    `left join` on `dim_team` that CANNOT fan out (`dim_team` is unique on `team_sk`).
  - **Row count moves by exactly the assists board and nothing else**, measured per `metric_key`
    before and after — not asserted from the diff.
  - **The null-club rate is MEASURED and reported**, because a row with no club has no link, which
    is the defect GAP-27 exists to fix. Reported two-sided, whatever the number.
  - `dbt parse` EXIT=0; the offline gates green, exit codes read bare and never through a pipe.
  - The register's GAP-27 and GAP-30 rows are updated in the same MR, including GAP-30's stale
    "NOT YET RULED".

decisions_taken: >
  ⭐ **§1. `team_logo_url` IS CARRIED, THOUGH THE REGISTER DOES NOT ASK FOR IT.** GAP-27's
  disposition says *"a `dim_team` lookup for name and slug"*. But #41 rules that **every row carries
  the club crest, on player rows as well as team rows**. Shipping name+slug alone would satisfy the
  register and still leave a mart that cannot render the approved design. Four columns, not two.
  This is following the design over a disposition written before it, not widening scope.

  ⭐ **§2. DESCRIPTIONS REFERENCE, THEY DO NOT RESTATE.** `team_sk` and `team_slug` already have
  docs blocks in `models/docs/shared_columns.md`, so both are `{{ doc(...) }}`.
  `engineering_standards.md` §2: *"A column documented in more than one model gets ONE docs block…
  restated definitions drift apart, which is how `league_code` came to be documented 76 times in 22
  different wordings."* `team_name` and `team_logo_url` have no block and are documented inline
  elsewhere in this same file, so they follow the neighbouring pattern.

  ⭐⭐ **§0. SCOPE WIDENED BY ONE FILE, ON THE CPO'S WORD, BECAUSE THIS CHANGE IS WHAT MAKES THE DOC
  FALSE.** `analytics-engineer` found at round 1 that `dbt_project/docs/layering.md`'s canonical mart
  inventory says `mart_leaderboards` has **"9 count boards"** — true before this MR, false after it.
  It marked this non-blocking since the file was outside `scope_paths`; that does not settle it,
  because *"a correction must land everywhere"* is this project's most-repeated failure. Put to the
  CPO with the cost stated (a contract amendment re-binds the review hash and costs a round), he
  ruled: **"fix it here"**.

  ⛔⛔ **AND THE CITATION ABOVE WAS NOT IN THE LOG WHEN IT WAS WRITTEN — `scope-auditor` FAILed round
  2 for it, correctly.** It grepped `escalations.log` for "fix it here", "layering.md" and
  "9 count boards", found nothing, and ruled that a scope widening resting on an unverifiable
  authority IS an unauthorised widening whatever the contract prose claims. **Fourth instance of
  `feedback_dont_attribute_repo_practice_to_cpo`** — and the sharpest, because I wrote the reviewer
  prompt telling the auditor to check for exactly this in the same turn I committed it. The ruling
  is now appended to the log; the citation only became true afterwards.

  ⭐ **THE DISCRIMINATOR FOR HOW FAR A STALE-DOC FIX GOES — earned from the same FAIL.** The auditor
  also held the `layering.md` edit had gone past the stale number, adding `dim_player`/`dim_team` to
  the line's "Composes" clause and naming 5 rate boards it had never mentioned. Right, and the rule
  is: **fix what THIS CHANGE falsifies; leave what was already incomplete.** The count went true →
  false because of this MR. The "Composes" clause never claimed to be exhaustive — it already
  omitted `dim_player` long before this MR — so this change does not falsify it. The edit is
  therefore **the number alone**, and `10_home.md`'s stale sentence is included for the same reason
  the number is: this MR is what makes it false.

  ⚠ **AND A SWEEP FOUND MORE, of which one more is fixed and two are left.**
  `scripts/export_site_data.py:45` reads *"the 9 COUNT boards from mart_leaderboards"*. That also
  goes stale — but the export still exports 9 ON PURPOSE, and `protected_override` bans export
  changes here. Its staleness is a property of the deferral, so it is owned by the reserved
  export-wiring step rather than left unowned. Fixing only the line a reviewer named, and not
  sweeping for the class, is the `feedback_fix_the_class_not_the_instance` failure.

  ⚠ **MY FIRST SWEEP MISSED TWO MORE — `analytics-engineer` found them in `docs/wireframes/10_home.md`.**
  · **`10_home.md`'s schema sentence — FIXED.** *"`mart_leaderboards` carries no team column
    (verified against the live schema…)"*, which also predicted the fix would mean "joining a squad
    mart in the export, which is derivation in the consumption layer". This MR falsifies it, and
    did it the other way — a `dim_team` identity join in the mart, no export derivation.
  · **`10_home.md`'s GAP-27/GAP-30 lines, still reading `LIVE` — LEFT.** The paragraph directly
    above them says *"The register is the authority — check it, not this summary"*, and the
    register IS updated in this MR. A reader following the file's own instruction gets the right
    answer. ⚠ That disclaimer covers GAP STATUS only — it does not cover the schema sentence above,
    which sits under a different and weaker one ("describes the removed module"). Conflating the
    two is why the first version of this paragraph proposed leaving both.

  ⛔⛔ **AND THAT "FINAL" COUNT WAS WRONG TOO — `scope-auditor` FAILed ROUND 3 on three MORE.** All
  in `10_home.md`, all in one section headed *"What this needs from the warehouse. None of it is
  built."* (itself falsified — this MR builds two of its four items), plus *"`assists_player` is not
  a ranked board at all"* and *"it is not selected into `mart_leaderboards`"*. **No disclaimer
  reaches that section**; the "register is the authority" line covers only the gap-status list far
  below it. **Round cap overridden by the CPO — "round 4, fix all three"** — recorded in
  `escalations.log` and as `rounds_cap_override:` in `review.md`.

  ⭐⭐ **THE DIAGNOSIS, AND IT IS THE DURABLE PART OF THIS MR. I SEARCHED FOR THE STRING I CHANGED,
  NOT FOR THE CLAIMS MY CHANGE FALSIFIES.** Every sweep grepped `9 count boards` / `count boards` —
  the words I edited. The three I missed say *"STILL MISSING"*, *"is not a ranked board at all"*,
  *"it is not selected"*, *"None of it is built"*. **Not one contains a board count.** They state
  the same fact as an ABSENCE, and an absence shares no vocabulary with the thing absent.
  ⭐ **Standing form: sweep for the CLAIM, not the STRING — ask "what does the tree assert about the
  thing I just built?", including every way of saying it does not exist yet.** This is
  `feedback_corrections_replace`'s search-key problem wearing a new disguise: its recorded fix is
  "pull every claim out and ask if it is still true", and I applied that to numbers but not to
  negations.

  ⛔⛔ **AND ROUND 4 — THE ROUND CONVENED TO CLOSE THIS OUT — FAILED ON A FOURTH.** `10_home.md`:
  *"…need six pieces of warehouse work, none of it built."* This MR ships two of those six, and the
  sentence sits immediately BEFORE the "register is the authority" disclaimer, which scopes itself
  to "this list" — the bullets after it. Fixed under a second CPO override, **"round 5"**.

  ⭐⭐ **THE REASON IT SURVIVED THREE SWEEPS IS THE DURABLE LESSON: THE PHRASE STRADDLES A LINE
  BREAK** — the file holds `none of it\nbuilt.` **No line-based grep can match it**, mine or the
  reviewer's own quoted string (`grep -ci "none of it built"` returns **0**). And `CLAUDE.md`, which
  loads every session, already says: *"⚠ A line-based grep misses a phrase straddling a line break …
  Sweep whitespace-collapsed."*

  ⭐ **FOUR SWEEPS, FOUR DISTINCT FAILURE MODES, EACH A RULE ALREADY HELD**: (1) searched the STRING
  changed, not the CLAIM falsified; (2) searched only where a reviewer pointed, not the class;
  (3) case-sensitive; (4) line-based. Each fix addressed the previous mode and left the next live —
  which is `fix_the_class_not_the_instance` applied to sweeping itself.

  ⭐ **THE METHOD THAT WORKS, and the one to start with next time: read each file whole, COLLAPSE ALL
  WHITESPACE, match case-insensitively for the CLAIM in every phrasing including negations, then
  adjudicate every hit in writing.** Run that way it returned **38 hits across the tree** — exactly
  1 genuine defect and 37 noise, struck text, other marts or correctly-disclaimed entries.
  **A sweep is only trustworthy if it is allowed to return mostly noise**; one that returns only
  what you expected has not searched.

  ⭐ Two-sided, final and verified by that method: **8 stale statements found — 5 fixed here, 1
  assigned to the export step, 2 left under the disclaimer that genuinely covers them.**
  Checked and correctly NOT counted: `10_home.md:276` (inside an already-struck VOID bullet),
  `layering.md:239` (about `dim_player`, still true), `99_gaps_register.md:27` (a different mart),
  and GAP-27/GAP-30's own **Gap** cells, which stay present-tense by the register's own convention —
  every shipped row does that, with status carried in the Ruling column.

  ⭐ **§3. THE DESCRIPTIONS CARRY THE NULL RULE, BECAUSE IT IS A REAL LIMIT.** `team_sk` comes from
  an `array_agg(... ignore nulls ...)` over finished matches, so a player-season with no finished
  match has no club and the left join yields nulls. §2 requires *"what NULL means"*, and here it
  means the row cannot link to a club at all.
  ⛔ And per §2's two bans, no description names a downstream consumer, an issue number or a date.

decisions_reserved:
  - ⛔ **The export wiring** — `_LEADERBOARD_METRICS` + `_LB_KEEP`. Ships with the block.
    ⚠ **It now also owns a stale comment**: `export_site_data.py:45` says *"the 9 COUNT boards from
    mart_leaderboards"*, and the mart has 10 from this MR. The export deliberately still exports 9,
    so the comment becomes accurate again only when that step adds the tenth. Recorded here so the
    line has an owner rather than being discovered as drift.
  - ⛔ **GAP-28** (the authored pool field) and **GAP-29** (the team mart) — Home's other two steps.
  - ⚠ **If the null-club rate is material, that is a finding for the CPO**, not something to absorb
    here: it would mean the block renders rows that cannot link, and the fix is upstream.
  - ⚠ CARRIED, untouched: step 5's four chrome strings; `fdp-freshness`'s hourly cadence; the
    disabled GitLab schedule; the resolver as a CI gate; **#99**, **#96**, **#87**, **#98**.

done_when: >
  - 15 boards compiled and verified; four club columns projected; no other behaviour changed.
  - Row-count delta attributed per `metric_key`; null-club rate measured and reported.
  - Register rows updated; gates green; blinded review (`analytics-engineer-reviewer` +
    `scope-auditor`). **Round cap 3.**
