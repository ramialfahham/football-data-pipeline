# Review — feat/136-player-cards-data — 2026-11-06

diff_sha256: 39377dedeb92f729745ec5b03cde4b7957ff450ec8e490967561f7b285b60a6d

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 2 findings closed: the fill's zeros follow a per-stat flag, as the amendment says; base.yml and layering.md state the 0-minute case and the carded sheet player.
- decisions_reserved records the seed description and both rule names as approved in chat, 2026-11-06, relayed by the coordinating session.
- Seed rows carry source_kind, an https source and a note; the 23 matches left in dispute are named in the amendment for a follow-up MR.
- No credentials in the patch, no site or export change, no new mechanism or recurring cost; every file is inside scope_paths and the impact map carries both pasted lineages.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- stats_counted_in_match is one row per fixture, so its join cannot fan out, and a stat the provider did not count stays blank.
- The dispute check reads delivered rows per team, sheets unnest separately, and cards need full events in both player bases.
- assert_card_corrections_applied gains off_the_sheet, reading all sheets and the stat lines; no Red Card row lacks a minute.
- Team cards can move in a researched match where the provider's team value was blank, because base_apif__fixture_statistics reads card events; the MR head states it. The 8% limit has little headroom at CDR 2023.

## platform-reviewer
VERDICT: PASS
risks_checked:
- PAGE_WINDOW and the generated SQL agree, and metric_map.csv holds the two new rows in sorted position.
- The two metrics exist in the catalogue and in metric_columns.md; the export takes every is_card row with no code change.
- No test or script assumes the old metric list; no dependency, workflow or hook changed.
- Round 1 verdict: scripts/ and metric_map.csv have not changed since, and the seed's emptiness that it checked no longer applies.

## escalations
- question: the seed description of fixture_card_corrections and the rule names cards_need_research and cards_from_research.
  CPO ANSWER: approved in chat, 2026-11-06, relayed by the coordinating session.
- question: the Cards line in cleaning_rules.md, and that no name rule places a card.
  CPO ANSWER: approved in chat, 2026-11-06, relayed by the coordinating session, recorded on #256.
