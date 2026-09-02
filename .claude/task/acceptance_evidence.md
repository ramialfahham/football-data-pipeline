# Acceptance evidence — the assists board, and a club on every leaderboard row

Branch `feat/leaderboards-assists-board-and-club`, from main `24ac4e2`.

Two registered gaps against `mart_leaderboards`, both prerequisites for Home's Top players block:
**GAP-30** (`assists_player` is not a ranked board) and **GAP-27** (a row carries no club, so it
links to a player and to nothing else). Warehouse only — two model files plus the register.

criteria_demonstrated:

  - **The board exists and is load-bearing, proven by mutation.** `count_boards` gains exactly one
    entry. Compiled SQL has **15** union-all branches, not 14; the new branch carries
    `where assists_player > 0` and the UNCHANGED `partition by league_code, season_api_year`.
    Removing the key again returns the compile to **14** branches and **0** assists branches — so a
    green result proves the board rather than tolerating its absence.
  - ⚠⚠ **THE `accepted_values` TEST WOULD HAVE FAILED IN CI AND NOWHERE ELSE.** `metric_key` carries
    an `accepted_values` list of all 14 board keys. Adding a board without adding it there is a
    guaranteed red — and **#96 records that no offline gate checks `accepted_values`, only
    `data:build:mr`**. Found by reading the yml rather than by any local gate. List and the column
    description both updated (14 → 15, 9 → 10 count boards).
  - **The join cannot fan out, measured rather than assumed.** `dim_team` is **3,331 rows / 3,331
    distinct `team_sk`**. A `left join` on a unique key adds columns and cannot add rows, so the
    only row-count movement is the new board.
  - **Row-count delta attributed.** Current prod mart **158,198** rows across 14 boards. The assists
    board contributes **30,863** rows after the `board_rank <= 10` cut, so the mart becomes
    **189,061**. ⚠ Stated as a prediction: it can only be confirmed once `data:build:mr` builds the
    model, and it is recorded here so that number is checkable rather than re-derived.
  - ⭐ **THE NULL-CLUB RATE IS ZERO, AND IT WAS MEASURED BECAUSE A NULL CLUB IS THE DEFECT ITSELF.**
    GAP-27 exists so a row can link to a club; a row with no club silently cannot. Measured against
    prod before shipping: **0 of 185,421** player-seasons have a null `team_sk`. Reported whatever
    it came out as — it happened to be clean.
  - **The `relationships` test I added is safe, checked before adding it.** `team_sk` →
    `dim_team.team_sk` has **0 orphans**, so the new test passes on today's data. Adding a test
    without checking it holds is how a green branch turns CI red after merge.
  - **The columns stay documented as NULLABLE despite measuring zero.** `team_sk` is resolved
    upstream by `array_agg(... ignore nulls order by last_kickoff_at desc ...)`, so a player-season
    with no finished match has no club. Null is structurally reachable even though the set is empty
    today, and `engineering_standards.md` §2 requires a description to say what NULL means.
  - ⭐ **`team_logo_url` IS CARRIED, AND THE REGISTER DOES NOT ASK FOR IT.** GAP-27's disposition
    says "a `dim_team` lookup for name and slug". But **#41 rules that every row carries the club
    crest, "on player rows as well as team rows"**. Shipping name+slug would have satisfied the
    register's letter and still left a mart that cannot render the approved design. Four columns on
    the design's authority, not two on the disposition's.
  - **Descriptions REFERENCE, they do not restate.** `team_sk` and `team_slug` already have docs
    blocks in `models/docs/shared_columns.md` and are wired as `{{ doc(...) }}`.
    `engineering_standards.md` §2: *"restated definitions drift apart, which is how `league_code`
    came to be documented 76 times in 22 different wordings."* `team_name` and `team_logo_url` have
    no block and follow the inline pattern their neighbours in this same file already use.
    ⛔ Per §2's two bans, no description names a downstream consumer, an issue number or a date.
  - **`dbt parse` EXIT=0**; `dbt compile --select mart_leaderboards` EXIT=0.
    `dbt ls --select mart_leaderboards+` returns **only the model itself** — nothing downstream
    reads it, which is the impact_map's central claim, checked with dbt rather than asserted.
  - **All seven offline gates EXIT=0**, read bare: `check_description_hygiene`,
    `sync_metric_docs_blocks --check`, `check_layer_contract`, `check_registry_var_sync`,
    `check_competition_type_seed`, `check_ui_i18n_metrics`, `check_copy_gate`.
  - **SQLFluff: zero NEW findings, verified against main rather than believed.** Both sides report
    the identical profile — 2×LT02, 1×TMP, 1×PRS, all on the `dbt_utils.generate_surrogate_key`
    call, which is unresolvable under the jinja templater. Only the PRS line number moves (302 →
    336) because lines were added above it.
  - **BigQuery cost: 3 read-only queries, dry-run first.** The measurement query was validated at
    **5,417,160 bytes** before running. No table written, no build run — `dbt build` is never run
    locally.
  - **The register is corrected in the same MR**, so it stops asserting a decision is open after the
    work lands. GAP-30's "NOT YET RULED" is cleared with the reason it was wrong.
  - ⭐⭐ **A STALE DOC THIS CHANGE ITSELF CREATES — FOUND AT ROUND 1, SWEPT FOR THE CLASS, FIXED ON
    THE CPO'S WORD.** `analytics-engineer` flagged `dbt_project/docs/layering.md`'s canonical mart
    inventory reading **"9 count boards"** — true before this MR, false after. It marked it
    non-blocking as out-of-`scope_paths`; that does not settle it, since *"a correction must land
    everywhere"* is this project's most-repeated failure. Put to the CPO with the cost stated
    (amending the contract re-binds the review hash and costs a round): **"fix it here"**.
    ⭐ **Swept for the class rather than fixing the named instance — TWO stale statements exist:**
      1. `layering.md:332` — **fixed here.** ⚠ And the line was completed while open: it never
         mentioned the **5 rate boards** at all (a pre-existing omission, not from this MR), and
         `dim_team` is now a source. Disclosed rather than slipped in as "just the number".
      2. `scripts/export_site_data.py:45` — *"the 9 COUNT boards from mart_leaderboards"*.
         **Deliberately NOT fixed**: the export still exports 9 ON PURPOSE and
         `protected_override` bans export changes here, so this line's staleness is a property of
         the deferral. Assigned to the reserved export-wiring step in `decisions_reserved` so it
         has an owner instead of being rediscovered as drift.
      3. `10_home.md`'s schema sentence — **FIXED.** *"`mart_leaderboards` carries no team column
         (verified against the live schema…)"*. ⚠ **My sweep missed this; `analytics-engineer`
         found it.** It also predicted the fix would mean "joining a squad mart in the export,
         which is derivation in the consumption layer" — this MR falsifies that too, and did it
         the other way: a `dim_team` identity join in the mart, no export derivation.
      4. `10_home.md`'s GAP-27/GAP-30 lines, still reading `LIVE` — **LEFT.** The paragraph directly
         above them reads *"The register is the authority — check it, not this summary"*, and the
         register IS updated here, so a reader following the file's own instruction gets the right
         answer. ⚠ That disclaimer covers **gap status only** — it does not cover item 3, which sits
         under a weaker one ("describes the removed module"). Conflating the two is why I first
         proposed leaving both.
    ⛔⛔ **AND THAT "FINAL" WAS WRONG AS WELL — round 3 FAILed on THREE more**, all in `10_home.md`,
    all in one section: its heading *"What this needs from the warehouse. None of it is built."*
    (this MR builds two of its four items), *"`assists_player` is not a ranked board at all"*, and
    *"it is not selected into `mart_leaderboards`"*. **No disclaimer reaches that section** — the
    "register is the authority" line covers only the gap list far below. All three FIXED under the
    CPO's round-cap override, *"round 4, fix all three"*.
    Two-sided, after re-sweeping on the corrected basis: **7 found — 4 fixed, 1 assigned to the
    export step, 2 left under the disclaimer that genuinely covers them.** Checked and correctly
    NOT counted: `10_home.md:276` (inside an already-struck VOID bullet), `layering.md:239` (about
    `dim_player`, still true), `99_gaps_register.md:27` (a different mart), and GAP-27/GAP-30's own
    **Gap** cells, which stay present-tense by the register's convention — every shipped row does
    that, with status carried in the Ruling column.
  - ⭐⭐ **THE DIAGNOSIS FOR THREE FAILED SWEEPS IN ONE MR, and it is sharper than "sweep harder".**
    **I searched for the STRING I CHANGED, not for the CLAIMS MY CHANGE FALSIFIES.** Every sweep
    grepped `9 count boards` / `count boards` — the words I edited. The three I missed say "STILL
    MISSING", "is not a ranked board at all", "it is not selected", "None of it is built".
    **Not one contains a board count.** They state the same fact as an ABSENCE, and an absence
    shares no vocabulary with the thing it is absent of. Standing form now recorded: **sweep for the
    CLAIM, not the STRING** — ask what the tree asserts about the thing you just built, including
    every way of saying it does not exist yet.
  - ⛔⛔ **AND ROUND 4 — CONVENED TO CLOSE THIS OUT — FAILED ON A FOURTH.** `10_home.md`: *"…need six
    pieces of warehouse work, none of it built."* This MR ships two of the six, and the sentence
    sits immediately BEFORE the "register is the authority" disclaimer, which scopes itself to
    "this list". Fixed under a second CPO override, **"round 5"**.
    ⭐⭐ **THE REASON IT SURVIVED IS THE LESSON WORTH KEEPING: THE PHRASE STRADDLES A LINE BREAK** —
    the file holds `none of it\nbuilt.`, so **no line-based grep can match it**, not mine and not
    the reviewer's own quoted string (`grep -ci "none of it built"` → **0**). `CLAUDE.md`, loaded
    every session, already says: *"A line-based grep misses a phrase straddling a line break …
    Sweep whitespace-collapsed."*
  - ⭐ **FOUR SWEEPS, FOUR DIFFERENT FAILURE MODES, EACH ONE A RULE I ALREADY HELD**: searched the
    STRING not the CLAIM · searched only where a reviewer pointed · case-sensitive · line-based.
    Every fix addressed the previous mode and left the next one live — `fix_the_class_not_the_instance`
    applied to sweeping itself.
  - ⭐ **THE METHOD THAT FINALLY WORKED, stated so it is the starting point next time:** read each
    file whole, **collapse all whitespace**, match case-insensitively for the CLAIM in every
    phrasing including negations, then adjudicate every hit in writing. Run that way it returned
    **38 hits across the tree** — exactly **1** genuine defect and 37 noise, struck text, other
    marts or correctly-disclaimed entries. **A sweep is only trustworthy if it is allowed to return
    mostly noise**; one that returns only what you expected has not searched.
  - ⚠ **COST, recorded because it is the honest measure: three lines of SQL, five review rounds, and
    every FAIL was documentation drift rather than the change itself.** The model diff has been
    byte-identical since round 1 and passed every round.
  - ⛔⛔ **ROUND 2 FAILED ON THE AUTHORITY FOR THE FIRST OF THOSE FIXES, AND THE FAIL WAS RIGHT.**
    I amended the contract to cite *"he ruled: 'fix it here'"* and **never wrote the ruling into
    `escalations.log`**. `scope-auditor` grepped the log for "fix it here", "layering.md" and
    "9 count boards", found nothing, and ruled that a scope widening resting on an unverifiable
    authority IS unauthorised, whatever the contract prose says. **Fourth instance of
    `feedback_dont_attribute_repo_practice_to_cpo`** — and the sharpest yet, because I wrote the
    reviewer prompt telling the auditor to check for precisely this in the same turn I committed
    it. Knowing a rule, and even instrumenting a reviewer to catch it, is not the same as following
    it. Ruling now appended.
  - ⭐ **AND THE SAME FAIL EARNED THE RULE FOR HOW FAR A STALE-DOC FIX GOES.** The auditor held the
    `layering.md` edit had gone past the number, adding `dim_player`/`dim_team` to its "Composes"
    clause and naming rate boards it never mentioned. Correct: **fix what THIS CHANGE falsifies,
    leave what was already incomplete.** The count went true → false because of this MR; the
    "Composes" clause never claimed to be exhaustive (it already omitted `dim_player` long before
    this MR), so this change does not falsify it. The edit is now **the number alone**.

reserved:

  - ⛔ **The export.** `_LEADERBOARD_METRICS` (board keys) and `_LB_KEEP` (column allowlist) in
    `scripts/export_site_data.py` both still need edits before this reaches a payload — and are
    deliberately untouched. **No page or component consumes the leaderboards payload today**
    (`grep -rn "leaderboard" site_v2/src` → nothing), and the register's own rule is that *"gap
    fixes never ship inside blueprint PRs"*. `_LB_KEEP` already contains `assists_player`, so only
    the board key and the four club columns remain outstanding for the block build.
  - ⛔ **GAP-28** (the authored pool field) and **GAP-29** (the team mart) — Home's other two steps.
  - ⚠ **#40's text is stale and is NOT fixed here.** Its "What this needs from the warehouse" still
    says the real gap is pooling across leagues; GAP-31 was withdrawn on 2026-08-18 (*"One per
    league"*), which makes the existing per-league partition already correct. Out of scope.
