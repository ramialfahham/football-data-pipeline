# Task contract — docs: player performance-surface spec (resolve the deferred player season surface)

> CPO-directed this conversation (2026-06-17). Writes the player performance-surface specification —
> the resolution of the deferred player full-season surface in `docs/metrics_context_model.md` §7 —
> recording the CPO decisions made across this conversation. DOCS ONLY: no model/SQL/seed/YAML/python
> change. It specifies what the build PRs (#480 one canonical player-season model; #484 player
> national/tournament context) construct against. The national-team rules OVERRIDE the catalogue's
> domestic-substitution form-window dispatch — a deliberate CPO override (reframe: form → context);
> football-analytics confirms the football-correctness. Reviewers: scope-auditor (always; routing-
> required for these docs paths) + analytics-engineer-reviewer + football-analytics-expert-reviewer
> (CPO-directed for the analytics-design + football-domain content).

objective: >
  Write the player performance-surface spec into docs/metrics_context_model.md (new section) and point the
  superseded catalogue section at it. Captures: the shared-aggregation principle (one aggregation, two
  windows), per-club season grain, season-over-season side-by-side, the appearance/playing-time context
  block, and the club/national window matrix with the national-team "context" reframe. No code.

refs: >
  This conversation 2026-06-17. Resolves docs/metrics_context_model.md §7 (player full-season part). Build
  follow-ups #480 (consolidate to one player-season model) and #484 (player national/tournament context).

scope_paths:
  - docs/metrics_context_model.md
  - docs/player_metrics_catalogue.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO (this conversation, 2026-06-17), all explicitly ruled:
  (1) Aggregation is ONE shared logic, applied to whichever window's match-set: sum the counts; the four
      ratios (duels-won %, dribble-success %, pass-accuracy %, save %) are WEIGHTED (sum num / sum den),
      never an average of per-match %s; honest absence (count only matches the provider gave stats for);
      zero denominator -> "-" with the counts still shown. The per-match leg is the shared building block;
      form and season differ ONLY in which legs are selected.
  (2) What we show = the nine CPO-locked player rows (docs/wireframes/metrics_display.md, 2026-06-11) as
      TOTALS + the four weighted %s (NOT per-match) + a NEW appearance/playing-time context block: two rows
      (appearances . starts . subs; minutes total . avg-per-appearance) + last appearance in the window
      meta-line, with the year (e.g. "18 May 2026 vs Dortmund").
  (3) Season model: ONE model, per-club grain (a transferred player gets a separate per-club season line),
      carrying this season + last season SIDE-BY-SIDE (a persistent comparison, not a pre-season-only
      fallback); always within one competition (never cross-competition). Replaces the three divergent
      player-season rollups that exist today.
  (4) Window matrix. Club: a player's club form (last 5 across the club's competitions; domestic = previous
      season before matchday 1, full season after). National: REFRAMED as CONTEXT, not form -- last <=5
      national-team appearances pooled across ALL national-team competition types (friendlies included once
      ingested), by recency, no season cap; during AND after a big tournament (world / continental
      championship) show the cumulative tournament figures ONLY; (future, when NT history is ingested) a
      career view grouped by NT competition type. Strict club/national separation: the national view never
      borrows club data.
  (5) This OVERRIDES the catalogue's "Form-window dispatch" (player WC form drawn from the domestic club,
      qualifiers excluded). The reframe form -> context dissolves that section's three objections (all about
      form-PREDICTION). Recorded as a CPO override; football-analytics confirms the football-correctness.
  (6) No separate "context vs form" UI framing mechanism -- the existing locked window meta-line carries the
      scope distinction through its copy (final wording at i18n).

decisions_reserved:
  - BUILD is out of scope. Spec only. #480 (consolidate to one player-season model) and #484 (player
    national/tournament context) are separate PRs with their own validation (they change shipped numbers ->
    metric defs are already weighted in the catalogue; analytics-engineer + football-analytics review there).
  - The appearance/playing-time block + the "no-separate-framing" ruling are DISPLAY-contract additions; this
    spec records the decision, but the formal amendment to the locked display contract
    (docs/wireframes/metrics_display.md, bi-analyst-owned) is a follow-up -- NOT edited here.
  - Friendlies in the NT pool, and NT history grouped by competition type, are COST-GATED ingest
    dependencies (friendlies endpoint; NT history ~ #477) -- the rule is defined; the data lights up only
    when those are CPO-approved.
  - If football-analytics FAILs the national-context override on football-correctness grounds (distinct from
    the CPO's product call), record it as ESCALATE + the CPO ruling already made this conversation as the
    CPO ANSWER; do not silently re-decide.
  - Any further §10 (a NEW mechanism, a grain change, a shipped-output change to a LIVE surface) -> escalate
    in plain language, do not decide.

done_when:
  - docs/metrics_context_model.md carries a new self-contained player performance-surface section (windows +
    shared aggregation + per-club grain + season-over-season + appearance block + national-context reframe +
    override note + #480/#484 build pointers); §7's player full-season item is marked resolved, pointing to
    the new section.
  - docs/player_metrics_catalogue.md "Form-window dispatch" section carries a SUPERSEDED-BY pointer to the new
    section (its definitions/formulas stay canonical).
  - Internal consistency: no remaining doc statement contradicts the override (the catalogue dispatch is
    pointed, not silently left); all cross-references resolve.
  - Docs-only: no model/SQL/seed/YAML/python touched, so NO dbt build / DQ run is required (and none is run).
  - reviewers: scope-auditor (required) + analytics-engineer-reviewer + football-analytics-expert-reviewer
    (CPO-directed) -- all PASS (>=2 named risks each), no FAIL, every ESCALATE has a recorded CPO ANSWER.

amendments: (none)
