# Review — feat/team-name-corrections — 2026-07-28

> Machine-checked review artifact (governance G3). Written in step 4 (Lock), after staging and after
> the blinded reviewers returned.
>
> ROUND 2 was forced by CI, not by a reviewer: `data-build` failed on SQLFluff **AM04** ("query
> produces an unknown number of result columns") plus three LT02 indent hits, because
> `select teams.* replace (coalesce(...) as team_name)` becomes ambiguous once a join is added — the
> original bare `select *` over one ref was resolvable, which is why it had always passed. Fixed by
> enumerating the 13 columns explicitly. **No `noqa` and no lint-rule config change**: this repo
> contains zero `noqa`, and adding the first one to make my own code pass is exactly the
> "never loosen a guard" failure. That fix invalidated part of round 1's reasoning, so both reviewers
> re-ran it rather than carrying their verdicts forward.

diff_sha256: d0979c93c0729ba67668f5bea915e69a9ad316d5370a2d9baab057c9b748ddb6

rounds: 2

> **HASH REBOUND after collapsing the branch to ONE commit.** An earlier value (`828a342b…`) was
> `--staged-hash` over only the final commit's staged diff, while CI recomputes `git diff main...HEAD`
> — the CUMULATIVE branch diff. With three commits on the branch those are different hashes, and
> `check_task_artifacts` failed on exactly that. Collapsing to one commit — which the working
> agreement requires anyway (ONE substantive commit per PR; the branch had two) — makes the staged
> diff and the branch diff the same object, so the hashes agree by construction rather than by luck.
> Verified: after `git reset --soft main`, `--staged-hash` returned the value CI had itself
> recomputed.
>
> **The collapse changed no content**, verified with
> `git diff --staged c792fd8 -- . ':!.claude/active_work.md' ':!.claude/task/review.md'` → empty.
>
> **ONE post-verdict change, disclosed rather than hidden: column ORDER in the final select.** Running
> SQLFluff locally with the FULL rule set (not just the two rules CI had reported) surfaced **ST06**,
> "select wildcards then simple targets before calculations" — the `coalesce(...) as team_name` sat
> third, ahead of simple targets. Moved to last. All 13 column names are unchanged and were
> re-verified programmatically against the live model's schema; only their order moved. This is
> explicitly covered by analytics-engineer-reviewer's own round-2 finding, which recorded that "order
> differs (harmless — every consumer selects by name)" and confirmed `dim_team.sql` projects each
> column by name. No round was spent on a reorder a reviewer had already declared immaterial, per
> review-cost discipline. Both files now lint clean locally:
> `python -m sqlfluff lint <model> <test> --templater jinja --dialect bigquery` → All Finished.

## scope-auditor
VERDICT: PASS
risks_checked:
- Authorisation of the round-2 SQL change: the contract's `done_when` requires an explicit import CTE
  per `ref()`, a join on `team_api_id`, the `coalesce`, and view materialisation — all four still hold.
  The contract does not prescribe how the projection is written, so changing `* replace` to an
  enumerated list is a technical HOW inside the authorised WHAT, and needs no amendment.
- Losing wildcard pass-through is a real maintenance trade-off: a column added to `base_apif__teams`
  in future will no longer reach `base_apif__teams_global` automatically. Accepted deliberately —
  lint compliance without suppression beats auto-coupling — and it is the same burden `dim_team`
  already carries with its own explicit select, so the gap does not widen. Called out in the model's
  own header comment.
- Round-1 finding, since fixed: the impact_map asserted "27 marts" from memory. Counted and replaced
  with pasted command output — `dim_team.sql` is the ONLY `.sql` child of `base_apif__teams_global`,
  17 mart models reference `dim_team`, 21 models in total — with an explicit CORRECTION line naming
  the Appendix A6 defect class so it is not silently overwritten.
- Round-1 finding, resolved without a code change: the singular test's INNER join cannot flag an
  override whose `team_api_id` vanished from the provider. The seed's `relationships` test to
  `ref('dim_team')` catches that direction, verified by tracing that `base_apif__teams` unions the
  teams endpoint plus fixtures, standings and fixture-level events. Indirect and deferred to the next
  CI test run, but loud rather than silent.
- Scope held throughout: every changed file inside `scope_paths`, no amendment needed, and every
  `decisions_reserved` item still undecided — the two duplicate provider-id pairs (Nyasa Big Bullets,
  Dragon), the unidentified Warriors #4207, the abbreviation/nickname cases, and the country-coalesce
  defect in the very file being edited, left alone per feedback-scope-discipline and recorded on #853.
- NOTE on this reviewer's round-2 Risk 2 ("the comment still advertises `* replace`"): raised against
  the round-1 comment text, not the file on disk. The header comment was rewritten in the same edit as
  the code and now states the AM04 rationale; verified by reading lines 28-32. No action needed, and
  recorded here rather than silently dropped.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Column-drop risk newly created by enumeration (round 1's `* replace` argument is dead and was NOT
  carried forward): verified by reading `base_apif__teams.sql`'s own final select and diffing its 13
  emitted names against the new list. Same 13 names, order differs (harmless — every consumer selects
  by name), none dropped, none added.
- `base.yml`'s `not_null` test on `league_code` for this model still resolves: `teams.league_code` is
  present at position 1 of the enumerated list.
- Blast radius of losing wildcard pass-through: re-ran the grep rather than reusing the round-1 count,
  since the claim is now load-bearing. `base_apif__teams_global` is referenced by `base.yml`,
  `seeds/schema.yml`, the new singular test, `layering.md`, `core.yml` and `dim_team.sql` — only
  `dim_team.sql` is a `.sql` model, and it already projects every one of its columns by name, all of
  which are present. No consumer relied on wildcard behaviour.
- Fan-out impossibility: `latest_per_team` dedupes to one row per `team_api_id` before the join, the
  seed carries `unique` + `not_null` on `team_api_id`, and the 14 CSV rows are distinct — a
  uniquely-keyed left join cannot fan out `dim_team`. Corroborated against BigQuery on both the
  `* replace` and the enumerated form: 3,249 rows in and out, 3,249 distinct ids, 0 null
  `league_code`, 14 corrections applied.
- Singular test is non-tautological: it compares against `base_apif__teams` (PRE-override) and
  re-derives the same dedup, rather than against `base_apif__teams_global` (POST-coalesce) which would
  trivially always agree and never fail. Both dedup clauses traced and confirmed identical.
- Layer placement holds mechanically, not just by ruling: `check_layer_contract.py`'s
  `BASE_FORBIDDEN_UPWARD_REF` matches only `ref('dim_|fct_|int_|mart_')` so a seed `ref()` does not
  trip it, and no `materialized=` override was added, so the view materialisation is preserved.
- Consumption-layer scope: `scripts/export_site_data.py` still calls `slugify(team_name, ...)`, which
  is the identity generation the consumption contract forbids — untouched here, outside `scope_paths`,
  and explicitly deferred to PR B (#852). No export or frontend file appears in the patch.

## escalations
(none)
