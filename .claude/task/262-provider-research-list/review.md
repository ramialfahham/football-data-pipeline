# Review — claude/262-provider-error-list-9103de — 2026-11-18

diff_sha256: 47e44ca80d5a424d52ee9d43e3d8d37e891470cc023538d61ea34ad452a1a9c6

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is in scope_paths, the three task artifacts included; no amendment.
- decisions_reserved is untouched: no standings test, no kind_needs_research, no live-without-merge route, runner, weekly report or tier filter in the diff.
- The research tiers cite #176; the check list, the card no-longer-needed rule, the goals_not_reconciled move and item_key are in decisions_taken under the coordinating session's ruling and box 7's approval.
- Thresholds: a mart and an int model in existing layers, no new mechanism; the recurring cost is declared with a dry-run for the MR.
- impact_map carries the dbt ls lineage and shows the new base column reaches no reader. The tests lose only provider-data cases, which move to the list, and gain goals_on_not_recorded.
- No page surface, secret or permission change.
- Round 2: the rename to mart_competition_research_list is complete across the diff and scope_paths; the doc() references resolve in shared_columns.md; the earlier basis is unchanged.
- Round 3: the two relationships tests on fixture_sk and team_sk are existing dbt tests in an in-scope file, required by engineering_standards §3.1; their targets exist; nothing else changed.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The int model reads only base and seeds; the mart reads base for flags that exist only there (cards_need_research, goals_need_research), which no rule forbids and the contract states.
- The four moved no-longer-needed predicates equal the removed test branches, the goal-key matching included; a broken correction still fails the test through its own branch.
- The goals_not_reconciled list rows are the same match set as the removed case; goals_on_not_recorded tests our own code; both tests stay error severity.
- card_research_agreement is one row per fixture, so the join cannot fan out; a NULL player never matches; a match with no provider substitution or card is FALSE; readers of base_apif__fixture_events name their columns, so the new column leaks nowhere.
- The mart's item_key is unique by construction and tested; the tier and season joins are one row per key.
- No metric, league identifier, seed row, materialisation or export change.
- Round 2: the entity competition is in engineering_standards §1's list; no stale reference to the old name; the three doc() blocks are the shared ones; the mart SQL is unchanged but for its file name.
- Round 3: fixture_sk relationships to fct_fixture cannot fail on provider data, as every fixture comes from fct_fixture or base_apif__fixtures_next, which fct_fixture projects whole; team_sk relationships to dim_team adds no new failure, because the same line-up teams already carry it on fct_fixture_lineup and fct_fixture_player_stats.

## escalations
(none)
