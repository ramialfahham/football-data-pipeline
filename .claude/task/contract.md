# Task contract — restructure docs/metric_layer.md and correct what is false in it

objective: >
  The rule *"we cannot calculate anything on incomplete data"* was decided 2026-06-25 and lived only
  in `escalations.log`, so I re-opened it today as a question. Stating it in `docs/metric_layer.md`
  exposed that the document is structurally inverted and factually stale: an independent structural
  review found the router table buried below a rule that has to point backwards at it, and SIX
  verified factual errors — including one that sends an engineer to the wrong model. Restructure it
  and fix what is false. Link it from `CLAUDE.md`, which does not reference it at all.

refs: >
  The CPO, verbatim, this session: *"We can not calculate anything on incomplete data. It is as
  simple as that."*; *"If I have metric definitins that calculate averages and i don't have the data
  to calculate them consistently then I will not show them. We know that this can happen for leagues
  beyond uefa etc."*; and on my first attempt at the doc — *"So you're panicking and spitting a
  wallpaper of text into this impoetant document??? You keep adding timestamps here?"* — then
  *"I want you to review the structure of the document. Let a professional do it. Starting with the
  'Incoplete data is not calculated' is really crap. You ar too heavily influenced by the recent
  conversation."* and *"restructure it properly"*.
  ⛔ **HE IS RIGHT ABOUT THE CAUSE.** I put my section first because it was what I had just been
  arguing about, not because a reader needs it first. The structural review was commissioned with an
  explicit instruction not to treat any section as recent or protected.

scope_paths:
  - .claude/task/contract.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log
  - docs/metric_layer.md
  - CLAUDE.md
  - docs/wireframes/metrics_display.md

impact_map: >
  writers: none. Documentation only — no model, seed, test, script or site file, and no computed
  number moves.
  layer_rules: not applicable.
  downstream: `docs/metrics_context_model.md:4` defers here "for the map of where each thing lives",
  which is the argument for the map being first. `CLAUDE.md` gains one row in its authoritative-docs
  table — verified absent today (`grep -c metric_layer CLAUDE.md` = 0), so the map is currently
  unreachable from the front door.
  deploy_order: none.
  blast_radius: none in data. The risk is a doc that states something false with authority — which is
  what is being fixed, so the bar is that every claim is verified against the tree before it is
  written.

acceptance_criteria:
  - **The lookup table is first**, with no prose above it, and every row points at a file or an
    in-document anchor. No row points "above".
  - **The incomplete-data rule is second** — still above every mechanism section, reached by a named
    router row rather than by physical position.
  - **`## Adding or changing a metric` moves above the guard reference.** It is the reader's primary
    action and sits 6th of 7 today.
  - **Every factual error below is corrected, each verified against the tree by me, not taken from
    the review:**
      the three canonical models and the compose chain (`int_player_club_season__metrics` is the
      atoms source that `int_player_season__metrics` composes) — today's text names two and sends a
      player-count change to the wrong one;
      the seed's real columns, stated ONCE (today it is stated twice, the two lists disagree, and
      both are wrong — `group_display_order` does not exist in the seed);
      `computation_kind` exists, so "no `metric_kind` taxonomy" is false;
      `base_relation` + `numerator_expr`/`denominator_expr` with
      `assert_metric_catalogue_expr_resolvable` checking every token IS a binding map with a CI
      guard, so "no binding-map" is false;
      all FIVE catalogue guards named, not one;
      the `#500` / `#480` references are stale — the guard's own docstring says #500 Stage 2 shipped;
      `finishing_efficiency_pct` IS range-tested 0–1 (`int_team_season.yml:53`), so "uncapped" is
      false;
      `points_won` IS in the model (`int_team_season__metrics_cumulative.sql:47`) and clears the
      guard by the `_sum_season` exemption, not by absence.
  - **`## Scope / follow-ups` is cut.** Issue status belongs in the tracker.
  - **`CLAUDE.md` gains a row** pointing at this document.
  - **It stays short and carries no provenance** — no dates, no CPO quotes, no history, no lectures.
    That is what the first attempt got wrong.

decisions_taken: >
  ⭐ **THE MAP GOES FIRST, THE RULE SECOND — and the reader decides that, not the rule's importance.**
  Of the questions a reader arrives with (where is this defined · how do I add one · why is this
  column NULL · what will CI fail on), exactly one is the NULL rule. Opening with it makes the other
  three scroll past it. The rule loses nothing: it is still above every mechanism section AND now
  reachable by a router row that names it, which is more discoverable than a section whose only
  pointer said "above".
  ⛔ **THE RULE STAYS IN THIS DOCUMENT.** It is metric semantics — what a computed value means and
  when it must not exist. Not `metrics_context_model.md`, which owns WHICH matches form a window;
  not `engineering_standards.md`, which owns testing policy. The correction runs the other way:
  `metrics_context_model.md` §8.1 restates the player half in its own words and should defer here.
  ⚠ NOT done in this MR — that file is outside `scope_paths` and it is a second document's edit.
  ⭐ **FACTS ARE RE-VERIFIED, NOT COPIED FROM THE REVIEW.** Every correction above was checked against
  the tree or prod first: the seed header, the guard list, the three models scanned by the drift
  guard, `CLAUDE.md`'s missing row, and `finishing_efficiency_pct` (0 of 4,999 rows above 1, max
  exactly 1.0, because the model NULLs a value over 1 rather than serving it). Taking a reviewer's
  facts on trust is what produced half of today's defects.
  ⛔ **THE FINISHING-EFFICIENCY CAVEAT IS CORRECTED, ON THE CPO'S INSTRUCTION — *"fix it"*.**
  `metrics_display.md:238-241` said finishing efficiency *"can exceed 100% (penalties/own goals
  counted as goals but not always as shots); the true value is always shown, never capped"*. Two
  things make that false, and neither is a judgement call:
    · since `!156` the numerator is OPEN-PLAY goals — `goals_for - goals_penalty - goals_own` — so
      the penalties-and-own-goals mechanism the caveat names is gone from the formula;
    · the model never showed a value above 1 anyway. `int_team_season__metrics_cumulative.sql:147`
      NULLs it when `goals_open_play_in_sot_games > shots_on_goal`, and
      `int_team_season.yml:53` asserts `between 0 and 1`. Measured on prod: 0 of 4,999 non-null rows
      above 1, maximum exactly 1.0.
  ⭐ **The SEED already states it correctly** — *"In [0, 1] - penalties and own goals are excluded
  because they are not finishing the team's own on-target shots"* — and the seed is the SSoT for
  glossary text. So this is not a new claim; it is `metrics_display.md`'s rationale paragraph left
  behind when the formula changed. Corrected to match the seed and the test, nothing more.
  ⚠ The section is marked LOCKED by CPO ruling. What is locked is the DESIGN — the shooting funnel
  and its row order — and neither moves. Only a factual sentence about the formula's range changes,
  on his explicit instruction this session.

decisions_reserved: >
  - **`metrics_context_model.md` §8.1** duplicating the player half of the NULL rule. Should defer
    here; not touched.
  - **GitLab #110** — forfeits the provider labels `FT`. Unchanged by this MR.
