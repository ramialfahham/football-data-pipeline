# Task contract — sweep the old brand, the board key, and the MVP-status false-claim class

> ⚠ **THE OBJECTIVE WAS WIDENED BY THE CPO ON 2026-07-28, MID-REVIEW.** It began as a brand rename.
> `scope-auditor` FAILed round 2 with the right complaint: the scope was growing through amendments
> in response to reviewer FAILs rather than going back to the CPO. It was put to him as three
> options, and he chose *"Keep it as one PR, you authorize the wider scope"* — explicitly naming
> "rename plus correcting the whole MVP-status class plus the ASCII realign". Amendments 3 and 4 are
> therefore CPO-authorised scope, not builder drift. See amendment 6.

> Written on a CLEAN tree, branch `chore/rename-brand-sweep` off `main` (`9e4ca94`, PR C1 merged).
> `gh pr list --state open` -> EMPTY, so this is a hard dependency of nothing and a new branch is
> correct (§3a).

objective: >
  PR C1 (#862) renamed the SITE surface and deliberately reserved the docs sweep. The CPO then asked
  for it directly: *"Maybe you need to clean up every reference to MatchdayIQ because it's
  MatchdayPilot now."* This is that sweep, plus the one occurrence that is not prose at all.

  **This is NOT a find-and-replace.** Two findings below make a blind replace actively wrong.

refs: >
  CPO, 2026-07-28, verbatim above. C1 = #862, merged.
  #860 owns `north_star.md`. PR C2 owns the wireframe SEO title templates and `package.json`.
  Memory `feedback_review_cost_discipline`: do not pay full adversarial-review price for prose.
  Memory `project_mvp_retired`: the MVP was retired 2026-07-21 — offline, Pages deleted, `site/`
  frozen. **No parity, no cutover, no restore.**

protected_override: >
  CPO, 2026-07-28, choosing "Rename board + all 5 refs" from an explicit three-way question whose
  option text read *"I change the string in both workflows and the 3 docs in the same PR"*. The
  PROTECTED paths this authorises are exactly `.github/workflows/board-request-sync.yml` and
  `.github/workflows/_paused/project-status-sync.yml`, and the authorised change is exactly the
  `PROJECT_BOARD_TITLE` value. No trigger, permission, secret or step is touched in either file.
  **This field was MISSING until cto-reviewer FAILed round 1 — see amendment 4, which is the real
  finding here.**

scope_paths:
  # A. Rename — these name the product GOING FORWARD
  - README.md
  - docs/agent_company_roadmap.md
  - docs/roles/bi_analyst.md
  - docs/roles/cfo.md
  - docs/roles/cto.md
  - docs/roles/growth_expert.md
  - docs/roles/legal_counsel.md
  - docs/site_architecture.md
  - docs/ui_design_brief.md
  - docs/wireframes/00_overview.md
  - docs/wireframes/09_chrome.md
  # B. The live lookup key — must move in lockstep with the real board
  - .github/workflows/board-request-sync.yml
  - .github/workflows/_paused/project-status-sync.yml
  - docs/board_request_sync.md
  - docs/project_status_sync.md
  - docs/chat_driven_workflow.md
  # C. Correct-not-rename — renaming these would launder a FALSE claim
  - scripts/export_site_data.py
  - AGENTS.md
  # D. The MVP-status false-claim class, CPO-authorised 2026-07-28 (amendments 6 and 7)
  - CLAUDE.md
  - docs/north_star.md   # ONE LINE ONLY (:37, the false claim). Its H1, brand and positioning
                         # remain RESERVED to #860 — see amendment 7 for why that split is exact.
  # artifacts
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/active_work.md

impact_map: >
  measurement: the first sweep I ran was WRONG and the corrected numbers are these. `git grep -i
  "matchday ?iq"` treats `?` as a LITERAL in basic regex, so the spaced form `Matchday IQ` was never
  searched at all — the same "the check could not have found it" class the C1 review caught twice.
  Extended regex (`grep -lEi "matchday ?iq|mdiq|matchdayiq\.io"`): **45 files on main before C1, 38
  after**. Re-run before and after this PR.

  **FINDING 1 — one occurrence is a LIVE LOOKUP KEY, not prose.**
  `PROJECT_BOARD_TITLE: Matchday IQ - Project Board` is matched against the real GitHub Project by
  title: `board-request-sync.yml:101` does `allProjects.find(p => p?.title === boardTitle)` and
  **`throw`s** at :104 when nothing matches. The board really is named that
  (`PVT_kwHOBm8D884BYSRV`, confirmed via `gh project list`). Changing the string alone BREAKS the
  sync; renaming the board alone breaks it too. **The board rename and these 5 files must ship
  together.** CPO approved renaming the board, 2026-07-28.
  ⚠ Residual window, stated rather than hidden: `board-request-sync` fires on `pull_request` AND
  `issues` events. `pull_request` runs use the workflow from the PR merge ref, which carries the fix,
  so this PR's own checks are fine. `issues` events run the workflow from the DEFAULT branch, which
  still holds the old string until merge — so opening or closing an issue between the board rename
  and this PR merging fails that one job. Low stakes, short, and it cannot be avoided while the
  lookup is by title.

  **FINDING 2 — for the RETIRED MVP the correct edit is usually NOT to rename.**
  `site/` was Matchday IQ. Matchday Pilot has never shipped anything. Calling the frozen prototype
  "the Matchday Pilot MVP" would attribute retired work to a product with no releases — a worse
  error than the stale name. Where a line describes the retired thing, the old name is CORRECT
  HISTORY and stays; where it describes the product going forward, it is renamed. Two lines are
  worse than stale, they are FALSE, and renaming them would launder the falsehood into the new
  brand:
    - `docs/site_architecture.md:29`, in the **locked constraints table**: *"The current Matchday IQ
      MVP (`site/`) stays fully functional until v2 reaches parity ... cutover only at CPO sign-off
      (#377)."* The MVP was retired 2026-07-21. There is no parity path and no cutover.
    - `scripts/export_site_data.py:8`: *"The current Matchday IQ MVP keeps running until cutover
      (#377)."* Same falsehood, same date.

  writers: every file is hand-authored. **Zero data changes**: no dbt model, no seed, no mart, no
    warehouse object, and `export_site_data.py` is touched in its MODULE DOCSTRING only — not one
    line of executable code.

  downstream: `.github/workflows/**` and `scripts/**` are cto-routed. `ci-ui.yml` is path-filtered to
    `site/**`, which this PR does not touch. No `site_v2/**` path is touched, so `ci-site-v2` and
    `bi-analyst-reviewer` stay dormant. Docs are read by agents, not built.

  deploy_order: none. No migration, no rebuild, no nightly interaction. The board rename is a GitHub
    account action taken immediately before this PR opens.

  blast_radius: ~20 prose occurrences, 1 live lookup key, 1 documented-wrong localStorage key, 2
    false status claims. Nothing user-visible: there is no public site.

decisions_taken: >
  - **Rename the GitHub Project board to `Matchday Pilot - Project Board`** and change all 5
    references in this PR. CPO approved, 2026-07-28, choosing this over leaving it stale.
  - **`docs/wireframes/09_chrome.md:94` is a CORRECTNESS fix, not cosmetics.** It documents the theme
    key as `mdiq-theme`; C1 changed it to `mdp-theme`. The doc has been wrong since #862 merged.
  - The two FALSE MVP-status claims are corrected rather than renamed, per Finding 2. This is the
    narrowest honest edit: a rename that carries a lie forward is worse than no rename.
  - **This is prose, and it is reviewed as prose.** Per `feedback_review_cost_discipline`, the sweep
    was done once up front and the reviewers are asked to confirm narrowly, not to re-derive it.

decisions_reserved:
  - **`docs/north_star.md`'s H1, brand and positioning** — #860 rewrites those wholesale. Renaming
    them now is work #860 discards. **Its line 37 is NO LONGER reserved** — see amendment 7.
  - **The 6 wireframe SEO title templates** (`| Matchday IQ` in `02`, `03`, `11`, `12`, `13`, `14`) —
    PR C2 rewrites these exact lines, and its approved plan DROPS the brand from titles entirely.
    Renaming them now is churn plus a guaranteed conflict.
  - **`site_v2/package.json` + `package-lock.json`** (`"name": "matchdayiq-site-v2"`) — never present
    in an HTTP response. C2 edits `package.json` anyway to add `@astrojs/sitemap`, and the lockfile
    must move in the same commit as the manifest.
  - **`site_v2/src/styles/system.css:2`** — the LOCKED design system; the comment is stripped at
    build. cto-reviewer agreed with leaving it in C1.
  - **`site/**`** — 9 files, ~50 hits, all `window.MATCHDAYIQ_*` JS globals in the retired, frozen
    prototype. `Deploy match preview` is `disabled_manually`; there is no reader. Renaming dead
    globals is breakage risk for zero benefit, and per Finding 2 the old name is correct there.
  - **`docs/player_stats_ui_data_modeling_concept.md:5`** — *"the existing Matchday IQ flow"* is a
    May-2026 concept doc describing the RETIRED MVP's match-preview flow. Accurate history.

done_when:
  - **`mdiq` returns NOTHING** across the target set. No exceptions: it is a dead key.
  - **Every remaining `Matchday IQ` in the target set sits on a line that also says `RETIRED`.**
    See amendment 1 — the original "returns NOTHING" form was WRONG and is NARROWED, not deleted.
  - `gh project list --owner ramialfahham` shows `Matchday Pilot - Project Board`, and `grep -rn
    "PROJECT_BOARD_TITLE" .github/` matches that title EXACTLY, character for character.
  - Every remaining hit in the repo is one of the reserved classes above, enumerated in `review.md`
    so no future reader "fixes" the board key and breaks the sync.
  - No `site_v2/**` path and no `dbt_project/**` path appears in the diff.
  - `scripts/export_site_data.py` diff touches the docstring only — `git diff` shows no change
    outside lines 1-14.
  - ONE commit.
  - Required reviewers: **FOUR**, computed from `review_routing.json` rather than guessed —
    scope-auditor (always) · cto-reviewer (`scripts/**`, `.github/workflows/**`) ·
    analytics-engineer-reviewer (`scripts/export_*.py`) · bi-analyst-reviewer (`docs/wireframes/**`).
    See amendment 2.

amendments:
  - 2026-07-28: **`done_when` clause 1 NARROWED, not deleted** — authority: the assertion as first
    written (`grep -rEi "matchday ?iq|mdiq" <target set>` returns NOTHING) is UNSATISFIABLE without
    breaking Finding 2, which this same contract states. Three lines keep the old name because they
    label RETIRED work, and renaming them would attribute a dead prototype to a product that has
    never shipped. The temptation was to drop the clause; per `feedback_never_loosen_a_guard` it is
    instead narrowed to where it still holds:
      - `mdiq` -> still NOTHING, unconditionally. It is a dead localStorage key with no historical
        reading, so no exception is legitimate. **Verified: zero.**
      - `Matchday IQ` -> every remaining hit must be on a line that ALSO contains `RETIRED`. A
        newly-stale forward-looking reference would not carry that word, so the guard still fails on
        exactly the thing it exists to catch. **Verified: 3 hits, all with RETIRED** — `AGENTS.md`,
        `docs/site_architecture.md`, `scripts/export_site_data.py`.
    This is a strictly SMALLER hole than deleting the clause, and the three exceptions are
    enumerated rather than described, so a future reader can diff the list.
  - 2026-07-28: **required-reviewer list corrected from 2 to 4** — authority: I WROTE the list from
    memory and it was wrong. Computing it from `review_routing.json` with the same `fnmatch` the gate
    uses adds `analytics-engineer-reviewer` (`scripts/export_*.py` routes to it as well as
    cto-reviewer) and `bi-analyst-reviewer` (`docs/wireframes/**`). No enforcement gap existed — the
    commit gate derives the required set itself and would have denied the commit — but a contract
    that states the wrong set invites someone to spawn two reviewers and stall. Recorded because
    "predict the reviewer set" is the wrong habit: compute it.
  - 2026-07-28: **`docs/site_architecture.md` swept for the WHOLE false-claim class, not the two
    lines I happened to hit** — authority: analytics-engineer-reviewer FAILed round 1, correctly. My
    Finding 2 claimed to have found "two false lines". It had found two of **six**, and patching
    only those left the file self-contradictory: §2's locked row now said "no cutover" while §7
    (`:196-197`, `:200`, `:203-205`) still described the legacy export "keeping running until #377",
    a `pages-match-preview.yml` "untouched until cutover", and #377 as "parity check → CPO sign-off →
    switch → redirects from old URLs"; §8's decisions log still carried "Current MVP stays live until
    parity cutover | **locked**". A doc that contradicts itself is worse than one that is uniformly
    stale. Swept by grepping the file for the CLASS (`cutover|parity|#377|stays live|keeps running`)
    rather than re-reading the diff, per `feedback_fix_the_class_not_the_instance`. §7 now states
    what is true (the legacy export is dead, `pages-match-preview.yml` is `disabled_manually` —
    verified via `gh workflow list`), §8's row is struck through and marked SUPERSEDED, and §1's
    workstream list says "go-live (#377)" not "migration (#377)".
  - 2026-07-28: **`docs/wireframes/09_chrome.md` ASCII box realigned — all 8 content rows, not the
    1 reported** — authority: bi-analyst-reviewer FAILed round 1 on the footer wordmark row being
    wider than the box. Measured rather than accepted: the row it named was **45 interior characters
    on `main` too**, and my edit had held every edited row's original width exactly. The real defect
    is PRE-EXISTING and larger — the drawer block (`:30-33`) and footer block (`:37-40`) were both
    45 while every border row was 44. The reviewer's proposed fix (shrink only line 37) would have
    made the footer block *internally* inconsistent as well. All 8 rows are now 44, verified by a
    script that measures every row rather than by counting spaces in a diff. Taken inside this PR
    rather than deferred because I am already editing this drawing and shipping one that does not
    close is not a defensible hand-off.
  - 2026-07-28: **`protected_override` ADDED — and the reason it was missing is a GUARD HOLE, not a
    typo** — authority: cto-reviewer FAILed round 1. `.github/workflows/` is in
    `task_contract_gate.py:66`'s `PROTECTED_PREFIXES`, so editing those two files required this
    field. It was absent, and the edit went through anyway. I reproduced why, and there are **two
    independent holes**, neither fixable here (`.claude/hooks/**` is itself PROTECTED and out of
    this contract's scope — filed separately):
      1. **PreToolUse never fired.** `_SED_I` (`:81`) anchors the filename group on `$`, so it
         cannot match a loop: `for f in …; do sed -i '…' "$f"; done` ends in `; done`, and the
         target is a VARIABLE the regex could not resolve even if it matched. Verified by importing
         the hook and calling `_SED_I.findall()` on the exact command I ran -> `[]`.
      2. **The PostToolUse "ironclad net" cannot catch it either.** `_gate_bash_post` flags a file
         only when `not _matches_scope(...)`. These two files ARE in `scope_paths`, so the
         protection test is never reached — **a PROTECTED file that is in scope with no override is
         invisible to the backstop.** Verified by evaluating the predicate directly.
    Both holes are in a guard, so per `feedback_never_loosen_a_guard` neither gets worked around;
    the contract now carries the field the gate wanted, and the hook defect is escalated on its own.
  - 2026-07-28: **the OBJECTIVE was widened by the CPO, and `CLAUDE.md` added to scope** —
    authority: `scope-auditor` FAILed round 2, ruling that amendments 3 and 4 had grown the scope in
    response to reviewer FAILs instead of returning to the CPO, and that the branch "cannot be
    assessed as a delta anymore". **I did not argue it into a PASS.** It was put to the CPO as three
    options — split into two PRs (my recommendation), authorise the wider scope, or drop the
    corrections and file them — and he chose to **authorise the wider scope**, explicitly including
    "correcting the whole MVP-status class plus the ASCII realign". Amendments 3 and 4 are now
    authorised scope rather than drift, and the objective above is restated to match.
    **What the widened objective then forced:** `analytics-engineer-reviewer` swept the SAME class
    repo-wide in round 2 and found two live instances outside `scope_paths` that the brand grep could
    never have caught, because neither contains the string "Matchday IQ":
      - `CLAUDE.md:53` — *"The legacy card MVP … stays live until cutover (#377)."* **Added to scope
        and corrected.** This is the file loaded at the top of every session and it self-declares
        that it OVERRIDES default behaviour, so a false claim here is the highest-harm instance in
        the repo — leaving it while fixing six lower-harm ones would be the exact
        `feedback_fix_the_class_not_the_instance` failure this amendment exists to close.
      - `.github/workflows/ci-site-v2.yml:4` — the same false framing in a code COMMENT. **NOT fixed
        here, deliberately.** It is a PROTECTED path and this contract's `protected_override` is
        bounded to the two board-sync workflows by name. Widening a protected-path override
        mid-review to reach a comment is precisely the creep the field exists to prevent, and the
        harm is near zero (no agent or job reads it). It rides with #863, which already needs its own
        CPO-approved contract for `.claude/hooks/**`.
  - 2026-07-28: **`docs/north_star.md:37` moved OUT of `decisions_reserved`, one line only** —
    authority: the CPO's widened objective (amendment 6) covers the whole MVP-status class, and my
    own repo-wide sweep — run because reviewers had now found this class twice in places my brand
    grep could not reach — turned up a third live instance no reviewer had named:
    *"**Legacy MVP (live until cutover, #377):** … It stays fully functional until v2 reaches parity
    and the CPO signs off the switch."* `north_star.md` is one of the three authorities `CLAUDE.md`
    tells every session to read FIRST. Leaving it would mean the north star contradicts both
    `CLAUDE.md` and `site_architecture.md` after this PR — a worse state than before it.
    **The reservation is narrowed, not lifted, and the boundary is the same one this contract has
    used throughout:** correcting a FALSE claim is a different act from RENAMING. #860 owns the H1,
    the brand and the positioning, and this PR touches none of them. It touches one sentence that is
    factually untrue.
    Sweep evidence, so the next reader can re-run it rather than trust it:
    `grep -rnEi "stays live until|keeps running until|until (the )?(parity )?cutover|until v2
    reaches parity"` over `*.md`/`*.yml`/`*.py`. After this PR the only surviving hits are
    `site_architecture.md:218` (the struck-through SUPERSEDED row, which must keep the words to
    record what was superseded) and `ci-site-v2.yml:4` (PROTECTED, deferred to #863 above).
