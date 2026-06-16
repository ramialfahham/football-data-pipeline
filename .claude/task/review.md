# Review — feat/gap-18-tournament-form-window — 2026-06-16 (commit 2: live label)

> Commit 2: surfaces home/away_form_from_qualifiers on mart_matchday_insights (from window_type)
> so the live formContextLabel UI switches the WC form label. Required reviewers (routing for the
> 4 staged paths): scope-auditor (always), analytics-engineer (dbt), bi-analyst (wireframes).
> Two §10 questions arose and were ruled by the CPO (2026-06-16, recorded below + escalations.log).

diff_sha256: 1b52806a4329a11400be20e4d86256d4a4e28f605228388abc201789ea0edce9

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope + additive: all 4 hunks within scope_paths; the two new columns are additive (existing
  columns/grain/one-row-per-fixture/row-count unchanged); deferrals (#483/#484/#391) intact.
- NULL-momentum boundary: coalesce(window_type='qualifiers', false) is total — a team with no
  momentum row (LEFT JOIN null) yields false, matching not_null; semantic intent preserved.
- Names pinned by the live UI (not a free choice); gaps-register "live preview fixed" now matches
  the diff (the flag IS wired here).

## analytics-engineer-reviewer
VERDICT: ESCALATE
risks_checked:
- Consumption-layer (A5): the export is SELECT * full-dict passthrough; the boolean derivation
  lives in the mart, not the export — no A5 violation.
- Additive + total: coalesce makes the columns boolean-non-null; not_null holds; grain unchanged.
question: The two new boolean columns are named home/away_form_from_qualifiers (no is_/has_ prefix),
  against the engineering_standards §1 boolean-naming convention — but the names are PINNED by the
  existing live UI (formContextLabel reads these exact keys). Match the UI name (convention exception)
  or rename + change the UI?
CPO ANSWER: Match the UI name (CPO 2026-06-16, this conversation). The published UI contract pins the
  field name; following is_/has_ would force a parallel live-UI edit. Documented as a CPO-approved
  exception in the mart comment.

## bi-analyst-reviewer
VERDICT: ESCALATE
risks_checked:
- Field-name match: the mart emits exactly home/away_form_from_qualifiers, the keys the live UI reads;
  i18n keys (formContextWcQualifiers / formContextWcTournament) already exist in en/de/fi, unchanged.
- No locked-contract change: no metric / i18n value / wireframe altered; v2 drill-down still under #391.
question: The UI labels a fixture "all qualifying matches" only when BOTH sides' form_from_qualifiers is
  true; a mixed-window fixture (one side pre-opener, one started) would read "all World Cup matches so
  far" — wrong for the qualifier side. Is "live preview fixed" safe, or must the UI become per-side?
CPO ANSWER: Proceed (CPO 2026-06-16). The mart surfaces one round per league, so under normal scheduling
  both sides share the same window phase and the mixed case does not arise; the dependency is documented
  in the mart comment. Per-side labels deferred (not needed today).

## escalations
- question: boolean column naming (UI-pinned home/away_form_from_qualifiers vs is_/has_ convention)
  CPO ANSWER: match the UI name (CPO 2026-06-16) — published-UI-contract exception, documented in the mart.
- question: mixed-window WC fixture labelling (UI both-sides AND check)
  CPO ANSWER: proceed (CPO 2026-06-16) — one-round-per-league makes both sides agree; dependency documented.
