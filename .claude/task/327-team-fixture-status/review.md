# Review — claude/327-team-fixture-status — 2026-11-21

diff_sha256: b1e6b3f1d824faaf37ccb897aa209aedab593073829825faf225d5509c50f040

rounds: 5

rounds_cap_override: round 4 was a text-only fix of the round 3 warehouse finding (stale "in fct_fixture" phrases), approved in chat, 2026-11-21. Round 5 fixes the MR build failure of assert_stat_facts_equal_base: its team-fact row filter excluded base rows that carry no stat line and no scoreline (both sides of a finished match with a withheld result); the filter is now the exact rule, a fact row is compared when a base row backs it. Approved in chat, 2026-11-21. Scope-auditor and platform-reviewer passed round 3 on the preceding diff; the warehouse reviewer re-ran on rounds 4 and 5 and passed.

## Readers of fct_fixture_team_stats

Every reader, found by grep over the repo, with the filter it applies to the widened fact (every status, two rows per fixture):

| Reader | Filter it carries |
|---|---|
| int_legs__team_match | `where t.is_finished and goals_for is not null and goals_against is not null`, added in this MR; the output equals prod (123,248 rows, 0 different both ways) |
| assert_fanout_facts_not_empty | `where is_finished`, added in this MR |
| assert_fct_fixture_team_stats_covers_active_competition_var | `where is_finished`, added in this MR |
| assert_stat_facts_equal_base | fact side restricted to rows a base row backs (`raw_ingested_at is not null`), changed in this MR; 123,250 fact rows = 123,250 base rows, 0 different both ways in the MR tables |
| assert_team_stats_team_in_fixture_participants | re-pointed at base_apif__fixture_statistics in this MR; the fact can no longer carry a non-participant team |
| assert_team_id_aliases_merged | reads `team_sk` only; the unplayed sides carry the same team keys as fct_fixture, which the same test already checks |
| assert_team_fixture_rows_reconcile | new in this MR, built for the widened grain |
| scripts/diagnostics/verify_competition_ingest.py | reads `team_sk` against dim_team; every team of every status is in dim_team (0 missing across ten statuses) |
| int_legs__team_from_players | a comment names the fact; no ref |

No reader is a mart or a page model; every page number reaches the fact only through int_legs__team_match, whose output is unchanged.

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 3: every changed path is in scope_paths or in amendments (1) and (2); no CPO-class decision, new mechanism, dependency, recurring cost or CI check in the diff; layering.md text is carried in the MR head for the merge approval; pins only go down.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 5: the team-fact `fact_rows` filter in assert_stat_facts_equal_base (`raw_ingested_at is not null`) selects exactly the fact rows that have a base partner, because the fact takes raw_ingested_at from a left join to base and base's raw_ingested_at is never NULL; both EXCEPT directions stay sound and a lost base row surfaces under "missing from the fact".
- Round 4: layer placement, grain and fan-out of the new base model and the widened fact, NULL semantics of the status and result columns, int_legs__team_match and int_round_names equality against the removed lines, the five re-pointed or new tests, column collisions on the widened base and core tables, and persisted descriptions and comments that name a moved model; the round 3 finding (stale fct_fixture wording) is fixed and no further stale text found.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 3: the decision-history pin recounted from the gate's own counting (minus one line, minus one file), the sentence-length pins, every dbt singular test in the diff (cannot pass vacuously, cost trivial), and nightly blocking exposure; no new failure exposure beyond invariants already enforced on fct_fixture and int_legs.

## escalations
(none)
