# Task contract — handover refresh: retire the stale strategy, state the road to a live v2 site

> Written on a CLEAN tree (branch `docs/handover-refresh-v2-roadmap` off main @ 1bc6087).
> CPO-directed 2026-07-21, verbatim: "I really would like to continue with the product because we are
> still far away of having the new website live. And the reason is that we have distractions all the
> time... I want you to give me clarity here. Prepare a proper handover so we can continue in a fresh new
> chat. Double check that we can continue without friction."
> Bookkeeping/handover refresh → plan mode is SKIPPED by standing CPO rule (2026-06-30), but the contract +
> review + commit gate still apply. See [[feedback-handover-discipline]] [[feedback-plan-mode-scope]].

objective: >
  Rewrite the TOP of `.claude/active_work.md` so a cold chat opens it and immediately knows (a) what is
  actually live, (b) what is actually built, (c) the remaining road to a live v2 website, and (d) the one
  next step — without having to reconstruct any of it. Three concrete defects are being fixed:
  (1) FOUR competing "⭐ ACTIVE" sections sit at the top (two now merged, two stale from 2026-07-11), so a
      cold chat cannot tell which is current.
  (2) The strategy header "#391 UN-PAUSED — data-first: complete v2 data+export, THEN the frontend" and its
      claim that "`site_v2/` is an empty Astro scaffold (2 stubs)" are BOTH stale. The data phase is
      complete (no orphan marts) and the fixture page + design system are built and merged (#672). A cold
      chat following that text would keep doing data work — the exact drift the CPO is objecting to.
  (3) The `_Last updated_` lead is a single ~4,000-character paragraph from 2026-07-11 whose "NEXT" list no
      longer matches reality.
  The history below (RECENT PRs, standing rules, governance, key specs) is REFERENCE and is left intact.

refs: >
  Verified live this session, not recalled: `gh pr list` (only #673 open) · `gh issue list` (the v2 epic
  #361 and its children #366–#377 open) · `site_v2/src/pages/**` (exactly 3 route files: 2 index stubs +
  the fixture route) · `site_v2/src/data/fixtures/` (exactly 1 committed sample fixture) · `site/` (the
  live MVP's 4 pages) · `scripts/export_site_data.py` (entity types it can emit) ·
  `docs/site_architecture.md` §5 templates→data contract and §7 deploy/cutover.

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

impact_map: >
  writers: none. A handover DOCUMENT change only. No seed, dbt model, test, export script, wireframe or
    `site_v2` code is touched. Zero rows, zero numbers, zero runtime behaviour.
  downstream: `.claude/active_work.md` is fed to every fresh chat by the `handover_in` SessionStart hook,
    so this file IS the thing that determines whether the next session continues or drifts. That is the
    entire point of the change.
  layer_rules: documentation only.
  deploy_order: nothing to deploy.
  blast_radius: zero runtime impact.

decisions_taken: >
  1. The four "⭐ ACTIVE" blocks collapse into ONE current section. Merged work (#677, #678) is stated as
     one line of outcome, not as an active task. The 2026-07-11 team-YoY and Phase-E blocks are folded into
     the same section because their live content (the team-page redesign, #673's rejection) is still true
     and must not be lost.
  2. The "data-first, THEN the frontend" strategy is recorded as COMPLETE, not deleted — it was the right
     call and it finished. The banner now says the frontend is the remaining work, so the next chat does
     not re-run the data phase.
  3. The handover states the road to a live site as an explicit ordered milestone list, because the CPO's
     complaint is drift, and drift is what happens when only the next ticket is written down.
  4. HONEST STATUS, no flattery: exactly ONE v2 page type is built (the fixture page), it renders from ONE
     committed sample JSON rather than real data, and it is deployed NOWHERE. The old MVP is what is live.
  5. The metric layer is recorded as **NOT finished**. The catalogue owns formula + `direction` +
     `interpretation`; the first two are complete, the third is empty on 28 player rows. Per the CPO's
     ruling this session that is a FOUNDATION gap, so it is written into the road as **TASK 0**, ahead of
     the player page — not as a footnote. An earlier draft of this handover claimed the metric layer was
     DONE and the gap was a non-blocker; both statements are corrected here.
  6. The player page design is step 1, per the CPO this session ("We're not done with the player page
     yet"), with its open decisions listed so a fresh chat does not re-derive them.

decisions_reserved:
  - "The milestone ORDER after the player page (build templates → wire real data → deploy preview →
     parity/cutover) is written as the proposed path; the CPO confirms or reorders it. Not self-granted."
  - "RETRACTED mid-task by CPO ruling (2026-07-21). An earlier draft of this contract recorded the blank
     `interpretation` rows as 'a logged nice-to-have, explicitly marked NOT a blocker'. The CPO rejected
     that framing: 'The metric layer is not a nice to have. It is the foundation of the metrics and their
     meaning. So I can't imagine where we could allow empty fields like explanations or interpretations.'
     The handover now records it as TASK 0, the next piece of work, ahead of the player page. The count was
     also wrong — it is 28, not 26: `finishing_efficiency` and `duels_won_pct` (player) already carry a
     direction but no interpretation, so they were missed by the direction-sweep-derived count. Verified by
     reading the merged seed. Writing the 28 values is NOT in this contract's scope — this task only fixes
     the handover; the sweep is its own PR."
  - "Whether to spend a session on repo/doc cleanup at all — recorded as an open CPO question, since the
     CPO raised it ('I'm not even sure if I need to do some cleanups') but did not decide it."

done_when:
  - `.claude/active_work.md` has exactly ONE "⭐ ACTIVE" section at the top, describing the true current state.
  - The stale "data-first / empty Astro scaffold" framing is corrected, not left to mislead the next chat.
  - The road to a live v2 site is an explicit ordered list, with the immediate next step and its open
    decisions written out.
  - FIRST STEPS is executable literally by a cold chat (checkout, verify command, what to read, what to do).
  - No file outside `scope_paths` is touched (diff-verified).
  - Required reviewer PASSes: scope-auditor (the only routed reviewer — no code path is touched, and
    `contract.md` is on `artifact_only_never`, so this commit is NOT review-exempt).
  - CPO merges; I never merge.

amendments: (none)
